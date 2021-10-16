from datetime import datetime, timedelta
from decimal import Decimal

import django_tables2 as tables
import pytz
from django.db.models import Avg, ExpressionWrapper, F, IntegerField, Sum, Count, Min, Max, Window, Value, FloatField
from django.db.models.functions import RowNumber
from django.shortcuts import render
from django.urls import reverse

from DSTBundesliga.apps.leagues.config import LEVEL_MAP, LOGO_MAP
from DSTBundesliga.apps.leagues.models import League, Roster, Draft, Pick, Player, DSTPlayer, Matchup, \
    PlayoffMatchup, Season, PlayerDraftStats, WaiverPickup
from DSTBundesliga.apps.leagues.tables import LeagueTable, RosterTable, DraftsADPTable, NextDraftsTable, \
    UpsetAndStealPickTable, PlayerStatsTable, WaiverTopBids, WaiverTopPlayers
from DSTBundesliga.apps.services.awards_service import AwardService


class LeagueView(tables.SingleTableView):
    table_class = LeagueTable
    queryset = League.objects.get_active().order_by('level', 'sleeper_name')
    template_name = "leagues/league_list.html"


def roster_list(request, league_id):
    league = League.objects.get(sleeper_id=league_id)

    title = league.sleeper_name
    table = RosterTable(Roster.objects.filter(league=league))

    return render(request, "leagues/roster_list.html", {
        "title": title,
        "table": table
    })


def level_detail(request, level=None, conference=None, region=None, season=None):
    league_objects = League.objects.all().order_by('sleeper_id')
    header_logo = None

    if season:
        season = Season.objects.get(year=season)
    else:
        season = Season.get_active()

    league_objects = league_objects.filter(season=season)

    if level:
        league_objects = league_objects.filter(level=level)
        header_logo = LOGO_MAP.get(level).get(conference)

    if conference:
        league_objects = league_objects.filter(conference=conference)

    if region:
        if region == "Sued":
            region = 'Süd'
        league_objects = league_objects.filter(region=region)

    leagues = [{
        "title": league.sleeper_name,
        "table": RosterTable(Roster.objects.filter(league=league)),
        "conference": league.conference or "",
        "stats_link": reverse('facts_and_figures_league', kwargs={'league_id': league.sleeper_id}),
        "playoffs_link": reverse('playoffs', kwargs={'league_id': league.sleeper_id}),
        "draft_link": reverse('draft-board',
                              kwargs={'league_id': league.sleeper_id}) if league.draft.status != 'pre_draft' else None
    } for league in league_objects]

    return render(request, "leagues/level_detail.html", {
        "leagues": leagues,
        "header_logo": header_logo
    })


def my_league(request):
    all_leagues = League.objects.get_active()

    context = {
        "levels": [{
            "title": LEVEL_MAP.get(level),
            "leagues": all_leagues.filter(level=level).order_by("sleeper_name")
        } for level in all_leagues.order_by("level").values_list("level", flat=True).distinct()]
    }

    my_league_id = request.COOKIES.get('my_league')
    if my_league_id:
        league = all_leagues.get(sleeper_id=my_league_id)
        title = league.sleeper_name
        table = RosterTable(Roster.objects.filter(league=league))

        header_logo = LOGO_MAP.get(league.level).get(league.conference)

        context["my_league"] = my_league_id
        context["title"] = title
        context["table"] = table
        context["conference"] = league.conference or ""
        context["header_logo"] = header_logo
        context["stats_link"] = reverse('facts_and_figures_league', kwargs={'league_id': league.sleeper_id})
        context["draft_link"] = reverse('draft-board', kwargs={
            'league_id': league.sleeper_id}) if league.draft.status != 'pre_draft' else None

    return render(request, "leagues/my_league.html", context)


def draft_stats(request, position=None):
    drafts = Draft.objects.filter(league__season__active=True).filter(league__type=League.BUNDESLIGA)

    drafts_done = drafts.filter(status='complete').count()
    drafts_running = drafts.filter(status__in=['drafting', 'paused']).count()
    drafts_overall = League.objects.get_active().filter(type=League.BUNDESLIGA).count()
    drafts_done_percent = drafts_done / drafts_overall * 100

    picks = Pick.objects.filter(draft__in=drafts)
    player_stats = PlayerDraftStats.objects.filter(season__active=True)

    if position:
        player_stats = player_stats.filter(player_position=position)
    else:
        player_stats = player_stats.filter(pick_count__gte=drafts_done * 0.5)

    adp_table = DraftsADPTable(player_stats.order_by('adp')[:200])

    next_drafts_table = NextDraftsTable(
        drafts.exclude(start_time=None).exclude(start_time__lte=datetime.utcnow().replace(tzinfo=pytz.utc)).exclude(
            status__in=['complete', 'drafting', 'paused']).order_by('start_time', 'league__level',
                                                                    'league__sleeper_name')[:10])

    upset_and_value_picks = player_stats.filter(pick_count__gte=drafts_done * 0.8).annotate(
        upset_value=ExpressionWrapper(F('adp') - F('highest_pick'), output_field=IntegerField()),
        steal_value=ExpressionWrapper(F('lowest_pick') - F('adp'), output_field=IntegerField()))

    upset_picks = []
    for upset_pick in upset_and_value_picks.order_by('-upset_value'):
        pick = picks.filter(player__sleeper_id=upset_pick.player_id, pick_no=upset_pick.highest_pick).annotate(
            adp=ExpressionWrapper(Value(float(upset_pick.adp)), output_field=FloatField())).first()
        upset_picks.append(pick)

        if len(upset_picks) >= 5:
            break

    steal_picks = []
    for steal_pick in upset_and_value_picks.order_by('-steal_value'):
        pick = picks.filter(player__sleeper_id=steal_pick.player_id, pick_no=steal_pick.lowest_pick).annotate(
            adp=ExpressionWrapper(Value(float(steal_pick.adp)), output_field=FloatField())).first()
        steal_picks.append(pick)

        if len(steal_picks) >= 5:
            break

    upset_table = UpsetAndStealPickTable(upset_picks)
    steal_table = UpsetAndStealPickTable(steal_picks)

    positions = [
        {"title": "Gesamt", "position": ""},
        {"title": "QB", "position": "QB"},
        {"title": "RB", "position": "RB"},
        {"title": "WR", "position": "WR"},
        {"title": "TE", "position": "TE"},
        {"title": "K", "position": "K"},
        {"title": "DEF", "position": "DEF"}
    ]

    return render(request, "stats/draft.html", {
        "drafts_done": drafts_done,
        "drafts_running": drafts_running,
        "drafts_overall": drafts_overall,
        "drafts_done_percent": drafts_done_percent,
        "adp_table": adp_table,
        "positions": positions,
        "selected_position": position or "",
        "upset_table": upset_table,
        "steal_table": steal_table,
        "next_drafts_table": next_drafts_table
    })


def player_stats(request, position=None):
    players = Player.objects.all()
    pos_filter = ""
    if position:
        pos_filter = "where position = '{position}'".format(position=position)

    players = players.raw(
        "select * from (select id, first_name, last_name, position, points, games_played, points/games_played as avg_points from leagues_player as whatever left join (select player_id, sum(points) as points, Sum(Case when stats = '""' then 0 when stats='{}' then 0 else 1 end) as games_played from leagues_statsweek group by player_id) as asdf on id=player_id %s) as player_data left join (select player_id, AVG(pick_no) as adp from leagues_pick group by player_id) as adp_picks on id=player_id order by  points desc, adp asc;" % pos_filter)

    player_stats = players[:200]

    player_stats_table = PlayerStatsTable(player_stats)

    positions = [
        {"title": "Gesamt", "position": ""},
        {"title": "QB", "position": "QB"},
        {"title": "RB", "position": "RB"},
        {"title": "WR", "position": "WR"},
        {"title": "TE", "position": "TE"},
        {"title": "K", "position": "K"},
        {"title": "DEF", "position": "DEF"}
    ]

    return render(request, "stats/player_stats.html", {
        "player_stats_table": player_stats_table,
        "positions": positions,
        "selected_position": position or ""
    })


def draftboard(request, league_id):
    draft = Draft.objects.get(league__sleeper_id=league_id)
    rosters = draft.league.total_rosters
    picks = draft.picks.order_by('round', 'draft_slot')
    picks_count = picks.count()
    fill_picks = []
    fill_pick_round = 16
    fill_picks_at_front = True
    fill_pick_pos = picks_count
    if picks_count < 180:
        fill_picks = range(rosters - (((picks_count - 1) % rosters) + 1))
        fill_pick_round = int(picks_count / rosters) + 1
        if fill_pick_round % 2 == 1:
            fill_picks_at_front = False
        else:
            fill_pick_round = int(picks_count / rosters)
            fill_pick_pos = fill_pick_round * rosters

    owners = DSTPlayer.objects.filter(sleeper_id__in=draft.draft_order.keys())

    draft_order = sorted([(draft.draft_order.get(owner.sleeper_id), owner) for owner in owners], key=lambda do: do[0])

    return render(request, "stats/draftboard.html", {
        "pick_width": "{:.2f}% !important".format(100 / rosters),
        "draft": draft,
        "draft_order": draft_order,
        "picks": picks,
        "fill_picks": fill_picks,
        "fill_pick_pos": fill_pick_pos,
        "fill_picks_at_front": fill_picks_at_front
    })


def playoffs(request, league_id):
    league = League.objects.get(sleeper_id=league_id)
    playoff_matchups = PlayoffMatchup.objects.filter(league_id=league_id)

    bracket_names = ["Playoffs", "Toilet Bowl"]
    brackets = [{
        "bracket": bracket,
        "rounds": [
            {
                "round": round,
                "matchups": [
                    {
                        "roster_one": league.rosters.get(
                            roster_id=matchup.roster_id_one) if matchup.roster_id_one else None,
                        "roster_two": league.rosters.get(
                            roster_id=matchup.roster_id_two) if matchup.roster_id_two else None
                    } for matchup in playoff_matchups.filter(round=round, bracket=bracket)]
            } for round in sorted(playoff_matchups.filter(bracket=bracket).values_list('round', flat=True).distinct())
        ]
    } for bracket in bracket_names]

    context = {
        "league": league,
        "brackets": brackets
    }

    return render(request, "leagues/playoffs.html", context)


def listener_league(request):
    league = League.objects.get(type=League.LISTENER, season=Season.get_active())
    title = "DST - Hörerliga"
    table = RosterTable(Roster.objects.filter(league=league))
    context = {}
    context["title"] = title
    context["table"] = table
    context["draft_link"] = reverse('draft-board', kwargs={
        'league_id': league.sleeper_id}) if league.draft.status != 'pre_draft' else None

    return render(request, "leagues/custom_league.html", context)


def champions_league(request):
    league = League.objects.get(type=League.CL, season=Season.get_active())
    title = "Champions League"
    table = RosterTable(Roster.objects.filter(league=league))
    context = {}
    context["title"] = title
    context["table"] = table
    context["draft_link"] = reverse('draft-board', kwargs={
        'league_id': league.sleeper_id}) if league.draft.status != 'pre_draft' else None

    return render(request, "leagues/custom_league.html", context)


def cl_quali(request):
    context = {}
    cl_quali_rosters = Roster.objects.filter(league__season=Season.get_active(), league__type=League.BUNDESLIGA).order_by("-fpts", "-fpts_decimal")
    top12_rosters = cl_quali_rosters[:12]
    in_the_hunt_rosters = cl_quali_rosters[12:100]

    top12_table = RosterTable(top12_rosters)
    in_the_hunt_table = RosterTable(in_the_hunt_rosters, ranking_offset=12)
    context["top12_table"] = top12_table
    context["in_the_hunt_table"] = in_the_hunt_table
    return render(request, "leagues/cl_quali.html", context)


def some_quali(request):
    ranked_rosters_qs = Roster.objects.annotate(rank=Window(expression=RowNumber(), partition_by=[F('league_id')],
                                                            order_by=[F('wins').desc(), F('ties').desc(),
                                                                      F('fpts').desc(), F('fpts_decimal').desc()]))
    rank_two_rosters = [roster for roster in ranked_rosters_qs if roster.rank == 2]
    rank_three_rosters = [roster for roster in ranked_rosters_qs if roster.rank == 3]

    rank_two_rosters = Roster.objects.annotate(rank=Window(expression=RowNumber(), partition_by=[F('league_id')],
                                                           order_by=[F('wins').desc(), F('ties').desc(),
                                                                     F('fpts').desc(),
                                                                     F('fpts_decimal').desc()])).filter(
        rank=2).order_by('-fpts', '-fpts_decimal')
    rank_three_rosters = Roster.objects.annotate(rank=Window(expression=RowNumber(), partition_by=[F('league_id')],
                                                             order_by=[F('wins').desc(), F('ties').desc(),
                                                                       F('fpts').desc(),
                                                                       F('fpts_decimal').desc()])).filter(
        rank=3).order_by('-fpts', '-fpts_decimal')
    # rank_two_rosters = Roster.objects.raw("select * from (select *, row_number() over (partition by league_id order by wins desc, ties asc, fpts desc, fpts_decimal desc) as rank from leagues_roster) where rank=2 order by fpts desc, fpts_decimal desc;")
    # rank_three_rosters = Roster.objects.raw("select * from (select *, row_number() over (partition by league_id order by wins desc, ties asc, fpts desc, fpts_decimal desc) as rank from leagues_roster) where rank=3 order by fpts desc, ftps_decimal desc;")

    top8_rank_two_roster_table = RosterTable(rank_two_rosters[:8])
    top8_rank_three_roster_table = RosterTable(rank_three_rosters[:8])

    context = {
        "top8_rank_two_roster_table": top8_rank_two_roster_table,
        "top8_rank_three_roster_table": top8_rank_three_roster_table
    }

    return render(request, "leagues/some_quali.html", context)


def facts_and_figures(request):
    week = Matchup.objects.filter(season=Season.get_active(), league_id__in=League.objects.filter(type=League.BUNDESLIGA).values_list('sleeper_id')).aggregate(Max('week')).get('week__max')
    awards_service = AwardService(week)
    stat_service = StatService(week)
    stats = stat_service.get_all()
    awards = awards_service.get_all()

    return render(request, "stats/facts_and_figures.html", {
        "current_week": week,
        "stats": stats,
        "awards": awards
    })


def facts_and_figures_for_league(request, league_id, week=None):
    if not week:
        week = Matchup.objects.filter(season=Season.get_active(), league_id__in=League.objects.filter(type=League.BUNDESLIGA).values_list('sleeper_id')).aggregate(Max('week')).get('week__max')
    awards_service = AwardService(week, league_id)
    stat_service = StatService(week, league_id)
    stats = stat_service.get_all_for_league()
    awards = [award for award in awards_service.get_all_for_league() if award]
    league = League.objects.get(sleeper_id=league_id)

    return render(request, "stats/facts_and_figures.html", {
        "current_week": week,
        "stats": stats,
        "awards": awards,
        "league_name": league.sleeper_name
    })


def waiver_stats(request):
    waivers = WaiverPickup.objects.filter(season=Season.get_active(), changed_ts__gte=datetime.now()-timedelta(days=7))

    waiver_sums = {}
    for w in waivers:
        data = waiver_sums.get(w.player.id, {})
        sum = data.get('bid_sum', 0)
        sum += w.bid

        count = data.get('bid_count', 0)
        count += 1

        sum_success = data.get('bid_sum_success', 0)
        count_success = data.get('bid_count_success', 0)
        leagues = data.get('leagues', set())
        leagues.add(w.roster.league)

        if w.status == 'complete':
            sum_success += w.bid
            count_success += 1

        avg = sum / count
        avg_success = sum_success / (count_success or 1)

        waiver_sums[w.player.id] = {
            'player': w.player,
            'bid_sum': sum,
            'bid_count': count,
            'bid_avg': avg,
            'bid_sum_success': sum_success,
            'leagues': leagues,
            'bid_count_success': count_success,
            'bid_avg_success': avg_success
        }

    waivers = waivers.filter(status='complete').order_by('-bid')
    top20_bids_table = WaiverTopBids(waivers[:20])

    sorted_waivers = sorted(waiver_sums.values(), key=lambda item: -item.get('bid_sum'))
    top20_players_table = WaiverTopPlayers(sorted_waivers[:20])

    context = {}
    context["top20_bids_table"] = top20_bids_table
    context["top20_players_table"] = top20_players_table

    return render(request, "stats/waiver.html", context)


class StatService():
    def __init__(self, week=None, league_id=None):
        matchups = Matchup.objects.filter(season=Season.get_active(), league_id__in=League.objects.filter(type=League.BUNDESLIGA).values_list('sleeper_id'))

        if week:
            matchups = matchups.filter(week=week)

        self.matchups = matchups
        self.league_id = league_id
        self.rosters = Roster.objects.filter(league__season=Season.get_active(), league__type=League.BUNDESLIGA)

    def get_all_for_league(self):
        return [
            {'title': 'Liga Rang', 'value': self.league_ranking()},
            {'title': 'Ø-Punkte/Matchup (Liga)', 'value': self.avg_points_league()},
            {'title': 'Ø-Punkte/Matchup (DST)', 'value': self.avg_points()},
            {'title': 'Ø-FAAB/Spieler', 'value': self.avg_faab()},
            {'title': 'Median', 'value': self.median_points()},
        ]

    def get_all(self):
        return [
            {'title': 'Ø-Punkte/Matchup', 'value': self.avg_points()},
            {'title': 'Ø-FAAB/Spieler', 'value': self.avg_faab()},
        ]

    def avg_faab(self):
        rosters = self.rosters
        if self.league_id:
            rosters = rosters.filter(league__sleeper_id=self.league_id)
        avg_faab_used = rosters.aggregate(avg_faab_used=Avg('waiver_budget_used')).get('avg_faab_used') or 0
        return "{faab}$".format(faab=int(
            100 - avg_faab_used))

    def avg_points_league(self):
        matchups = self.matchups.filter(league_id=self.league_id)
        rosters = self.rosters.filter(league__sleeper_id=self.league_id)
        sum_points = matchups.aggregate(sum_points=Sum('points_one') + Sum('points_two')).get('sum_points')
        return "{:.2f}".format(sum_points / rosters.count())

    def avg_points(self):
        sum_points = self.matchups.aggregate(sum_points=Sum('points_one') + Sum('points_two')).get('sum_points')
        return "{:.2f}".format(sum_points / self.rosters.count())

    def league_ranking(self):
        leagues = self.matchups.values('league_id').annotate(sum_points=Sum('points_one') + Sum('points_two')).order_by(
            '-sum_points')
        ranking = list(leagues.values_list('league_id', flat=True)).index(self.league_id) + 1

        return "#{}".format(ranking)

    def median_loosing_points(self):
        matchups = self.matchups
        if self.league_id:
            matchups = matchups.filter(league_id=self.league_id)
        losing_values = [mu.points_one if mu.points_one < mu.points_two else mu.points_two for mu in matchups]

        return "{:.2f}".format(self._median(losing_values))

    def median_points(self):
        matchups = self.matchups
        if self.league_id:
            matchups = matchups.filter(league_id=self.league_id)
        point_values = [mu.points_one for mu in matchups]
        point_values.extend([mu.points_two for mu in matchups])

        return "{:.2f}".format(self._median(point_values))

    def _median(self, data):
        count = len(data)
        values = sorted(data)
        if count % 2 == 1:
            return values[int(round(count / 2))]
        else:
            return sum(values[int(count / 2 - 1):int(count / 2 + 1)]) / Decimal(2.0)
