import random
from datetime import datetime

import django_tables2 as tables
import pytz
from django.db.models import Avg, ExpressionWrapper, F, DecimalField, IntegerField, Sum, Count, Min, Max, Window
from django.db.models.functions import Abs, RowNumber
from django.shortcuts import render
from django.template import Node
from django.template.loader import get_template, select_template
from django.urls import reverse

from DSTBundesliga.apps.leagues import services
from DSTBundesliga.apps.leagues.config import LEVEL_MAP, LOGO_MAP
from DSTBundesliga.apps.leagues.models import League, Roster, Draft, Pick, News, Player, DSTPlayer, Matchup
from DSTBundesliga.apps.leagues.tables import LeagueTable, RosterTable, DraftsADPTable, NextDraftsTable, \
    UpsetAndStealPickTable
from DSTBundesliga.settings import LISTENER_LEAGUE_ID


class LeagueView(tables.SingleTableView):
    table_class = LeagueTable
    queryset = League.objects.all().order_by('level', 'sleeper_name')
    template_name = "leagues/league_list.html"


def roster_list(request, league_id):
    league = League.objects.get(sleeper_id=league_id)

    title = league.sleeper_name
    table = RosterTable(Roster.objects.filter(league=league))

    return render(request, "leagues/roster_list.html", {
        "title": title,
        "table": table
    })


def level_detail(request, level=None, conference=None, region=None):
    league_objects = League.objects.all().order_by('sleeper_name')
    header_logo = None

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
        "draft_link": reverse('draft-board', kwargs={'league_id': league.sleeper_id}) if league.draft.status != 'pre_draft' else None
    } for league in league_objects]

    return render(request, "leagues/level_detail.html", {
        "leagues": leagues,
        "header_logo": header_logo
    })


def my_league(request):
    all_leagues = League.objects.all()
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
        context["draft_link"] = reverse('draft-board', kwargs={'league_id': league.sleeper_id}) if league.draft.status != 'pre_draft' else None

    return render(request, "leagues/my_league.html", context)


def draft_stats(request, position=None):
    drafts = Draft.objects.all()

    drafts_done = drafts.filter(status='complete').count()
    drafts_running = drafts.filter(status__in=['drafting', 'paused']).count()
    drafts_overall = League.objects.all().count()
    drafts_done_percent = drafts_done / drafts_overall * 100

    picks = Pick.objects.all()
    players = Player.objects.annotate(adp=Avg("pick__pick_no"), pick_count=Count("pick__player__id"), highest_pick=Min('pick__pick_no'), lowest_pick=Max('pick__pick_no'))

    draft_value = ExpressionWrapper((F('pick__pick_no')-F('adp')) * 20 / F('pick__round'), output_field=IntegerField())

    if position:
        players = players.filter(position=position)
    else:
        players = players.filter(pick_count__gte=drafts_done*0.5)

    adp_table = DraftsADPTable(players.exclude(adp=None).order_by('adp')[:200])

    next_drafts_table = NextDraftsTable(drafts.exclude(start_time=None).exclude(start_time__lte=datetime.utcnow().replace(tzinfo=pytz.utc)).exclude(status__in=['complete', 'drafting', 'paused']).order_by('start_time', 'league__level', 'league__sleeper_name')[:10])

    adp_diff = ExpressionWrapper((F('pick_no')-F('adp')) * 20 / F('round'), output_field=IntegerField())
    upset_and_value_picks = picks.annotate(adp=Avg('player__pick__pick_no'), pick_count=Count('player__id')).filter(pick_count__gte=drafts_done*0.8).annotate(adp_diff=adp_diff)

    upset_players = []
    upset_picks = []
    for pick in upset_and_value_picks.order_by('adp_diff'):
        if pick.player not in upset_players:
            upset_picks.append(pick)

        upset_players.append(pick.player)
        if len(upset_picks) >= 5:
            break

    steal_players = []
    steal_picks = []
    for pick in upset_and_value_picks.order_by('-adp_diff'):
        if pick.player not in steal_players:
            steal_picks.append(pick)

        steal_players.append(pick.player)
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


def home(request):
    week = Matchup.objects.all().aggregate(Max('week')).get('week__max')
    awards_service = AwardService(week)
    awards = awards_service.get_random(4)
    news = News.objects.all().order_by('-date')[:3]

    return render(request, "leagues/home.html", {
        "news_list": news,
        "awards": awards
    })


def draftboard(request, league_id, players=12):
    if league_id == LISTENER_LEAGUE_ID:
        players = 14
    draft = Draft.objects.get(league__sleeper_id=league_id)
    picks = draft.picks.order_by('round', 'draft_slot')
    picks_count = picks.count()
    fill_picks = []
    fill_pick_round = 16
    fill_picks_at_front = True
    fill_pick_pos = picks_count
    if picks_count < 180:
        fill_picks = range(players - (((picks_count-1) % players) + 1))
        fill_pick_round = int(picks_count/players) + 1
        if fill_pick_round % 2 == 1:
            fill_picks_at_front = False
        else:
            fill_pick_round = int(picks_count/players)
            fill_pick_pos = fill_pick_round * players

    owners = DSTPlayer.objects.filter(sleeper_id__in=draft.draft_order.keys())

    draft_order = sorted([(draft.draft_order.get(owner.sleeper_id), owner) for owner in owners], key=lambda do: do[0])

    return render(request, "stats/draftboard.html", {
        "pick_width": "{:.2f}% !important".format(100/players),
        "draft": draft,
        "draft_order": draft_order,
        "picks": picks,
        "fill_picks": fill_picks,
        "fill_pick_pos": fill_pick_pos,
        "fill_picks_at_front": fill_picks_at_front
    })


def listener_league(request):
    league = League.objects.get(sleeper_id=LISTENER_LEAGUE_ID)
    title = "DST - Hörerliga"
    table = RosterTable(Roster.objects.filter(league=league))
    context = {}
    context["title"] = title
    context["table"] = table
    context["draft_link"] = reverse('draft-board', kwargs={'league_id': league.sleeper_id}) if league.draft.status != 'pre_draft' else None

    return render(request, "leagues/custom_league.html", context)


def cl_quali(request):
    context = {}
    table = RosterTable(Roster.objects.exclude(league_id=LISTENER_LEAGUE_ID).order_by("-fpts", "-fpts_decimal")[:12])
    context["table"] = table
    context["title"] = "Champions League Qualifikation"
    return render(request, "leagues/custom_league.html", context)


def facts_and_figures(request):
    week = Matchup.objects.all().aggregate(Max('week')).get('week__max')
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
        week = Matchup.objects.all().aggregate(Max('week')).get('week__max')
    awards_service = AwardService(week, league_id)
    stat_service = StatService(week, league_id)
    stats = stat_service.get_all_for_league()
    awards = awards_service.get_all()
    league = League.objects.get(sleeper_id=league_id)

    return render(request, "stats/facts_and_figures.html", {
        "current_week": week,
        "stats": stats,
        "awards": awards,
        "league_name": league.sleeper_name
    })


class StatService():
    def __init__(self, week=None, league_id=None):
        matchups = Matchup.objects.exclude(league_id=LISTENER_LEAGUE_ID)

        if week:
            matchups = matchups.filter(week=week)

        self.matchups = matchups
        self.league_id = league_id
        self.rosters = Roster.objects.exclude(league__sleeper_id=LISTENER_LEAGUE_ID)

    def get_all_for_league(self):
        return [
            {'title': 'Liga Rang', 'value': self.league_ranking()},
            {'title': 'Ø-Punkte/Matchup (Liga)', 'value': self.avg_points_league()},
            {'title': 'Ø-Punkte/Matchup (DST)', 'value': self.avg_points()},
            {'title': 'Ø-FAAB/Spieler', 'value': self.avg_faab()},
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
            100-avg_faab_used))

    def avg_points_league(self):
        matchups = self.matchups.filter(league_id=self.league_id)
        rosters = self.rosters.filter(league__sleeper_id=self.league_id)
        sum_points = matchups.aggregate(sum_points=Sum('points_one')+Sum('points_two')).get('sum_points')
        return "{:.2f}".format(sum_points / rosters.count())

    def avg_points(self):
        sum_points = self.matchups.aggregate(sum_points=Sum('points_one')+Sum('points_two')).get('sum_points')
        return "{:.2f}".format(sum_points / self.rosters.count())

    def league_ranking(self):
        leagues = self.matchups.values('league_id').annotate(sum_points=Sum('points_one')+Sum('points_two')).order_by('-sum_points')
        print([(l.get("sum_points"), l.get("league_id")) for l in leagues])
        ranking = list(leagues.values_list('league_id', flat=True)).index(self.league_id) + 1

        return "#{}".format(ranking)


class AwardService():
    def __init__(self, week=None, league_id=None):
        matchups = Matchup.objects.exclude(league_id=LISTENER_LEAGUE_ID)

        if week:
            matchups = matchups.filter(week=week)

        if league_id:
            matchups = matchups.filter(league_id=league_id)

        self.matchups = matchups
        self.narrow_matchups = matchups.annotate(point_difference=Abs(F('points_one')-F('points_two')))
        self.rosters = Roster.objects.exclude(league__sleeper_id=LISTENER_LEAGUE_ID)

    def get_all(self):
        return [
            self.get_highscorer(),
            self.get_lowscorer(),
            self.get_blowout_victory(),
            self.get_narrow_victory(),
            self.get_shootout(),
            self.get_buli_leader(),
            self.get_cffc_vs_affc(),
            self.get_cffc_leader(),
            self.get_affc_leader()
        ]

    def get_random(self, count=99):
        return random.sample(self.get_all(), count)

    def get_highscorer(self):
        mpo = self.matchups.order_by('-points_one').first()
        mpt = self.matchups.order_by('-points_two').first()

        if mpo.points_one >= mpt.points_two:
            most_points_score = mpo.points_one
            most_points_roster = self.rosters.get(league__sleeper_id=mpo.league_id, roster_id=mpo.roster_id_one)
        else:
            most_points_score = mpt.points_two
            most_points_roster = self.rosters.get(league__sleeper_id=mpt.league_id, roster_id=mpt.roster_id_two)

        context = {
            'roster': most_points_roster,
            'league': most_points_roster.league,
            'score': most_points_score
        }

        return HighscorerAward(context)

    def get_lowscorer(self):
        mpo = self.matchups.order_by('points_one').first()
        mpt = self.matchups.order_by('points_two').first()

        if mpo.points_one <= mpt.points_two:
            least_points_score = mpo.points_one
            least_points_roster = self.rosters.get(league__sleeper_id=mpo.league_id, roster_id=mpo.roster_id_one)
        else:
            least_points_score = mpt.points_two
            least_points_roster = self.rosters.get(league__sleeper_id=mpt.league_id, roster_id=mpt.roster_id_two)

        context = {
            'roster': least_points_roster,
            'league': least_points_roster.league,
            'score': least_points_score
        }

        return LowscorerAward(context)

    def get_narrow_victory(self):
        head_to_head = self.narrow_matchups.order_by('point_difference').first()
        roster_one = self.rosters.get(league__sleeper_id=head_to_head.league_id, roster_id=head_to_head.roster_id_one)
        roster_two = self.rosters.get(league__sleeper_id=head_to_head.league_id, roster_id=head_to_head.roster_id_two)

        context = {
            'roster_one': roster_one,
            'roster_two': roster_two,
            'score_one': head_to_head.points_one,
            'score_two': head_to_head.points_two,
            'league': roster_one.league
        }

        return RaceAward(context)

    def get_blowout_victory(self):
        blowout = self.narrow_matchups.order_by('-point_difference').first()
        roster_one = self.rosters.get(league__sleeper_id=blowout.league_id, roster_id=blowout.roster_id_one)
        roster_two = self.rosters.get(league__sleeper_id=blowout.league_id, roster_id=blowout.roster_id_two)

        context = {
            'roster_one': roster_one,
            'roster_two': roster_two,
            'score_one': blowout.points_one,
            'score_two': blowout.points_two,
            'league': roster_one.league
        }

        return BlowoutAward(context)

    def get_shootout(self):
        shootout = self.narrow_matchups.filter(point_difference__lte=10).annotate(points_sum=F('points_one')+F('points_two')).order_by('-points_sum').first()
        roster_one = self.rosters.get(league__sleeper_id=shootout.league_id, roster_id=shootout.roster_id_one)
        roster_two = self.rosters.get(league__sleeper_id=shootout.league_id, roster_id=shootout.roster_id_two)

        context = {
            'roster_one': roster_one,
            'roster_two': roster_two,
            'score_one': shootout.points_one,
            'score_two': shootout.points_two,
            'league': roster_one.league
        }

        return ShootoutAward(context)

    def get_cffc_vs_affc(self):
        cffc_league_ids = League.objects.filter(conference="CFFC").values_list('sleeper_id', flat=True)
        affc_league_ids = League.objects.filter(conference="AFFC").values_list('sleeper_id', flat=True)

        points_cffc = self.matchups.filter(league_id__in=cffc_league_ids).aggregate(point_sum=Sum('points_one')+Sum('points_two')).get("point_sum")
        points_affc = self.matchups.filter(league_id__in=affc_league_ids).aggregate(point_sum=Sum('points_one')+Sum('points_two')).get("point_sum")

        context = {
            'name_one': 'AFFC',
            'name_two': 'CFFC',
            'score_one': points_affc,
            'score_two': points_cffc
        }

        return CFFCvsAFFCAward(context)

    def get_buli_leader(self):
        leader = Roster.objects.filter(league__level=1).first()

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return BuliLeader(context)

    def get_cffc_leader(self):
        leader = Roster.objects.filter(league__conference='CFFC').first()

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return CFFCLeader(context)

    def get_affc_leader(self):
        leader = Roster.objects.filter(league__conference='AFFC').first()

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return AFFCLeader(context)


class Award():
    template_name = ""
    must_be_first = False

    def __init__(self, context, title=None, icon=None):
        super().__init__()

        context.update({
            "title": title,
            "icon": icon
        })

        self.context = context

    def __str__(self):
        return self.render(self.context)

    def render(self, context):
        template_name = self.template_name

        if isinstance(template_name, str):
            template = get_template(template_name)
        else:
            # assume some iterable was given
            template = select_template(template_name)

        return template.render(context=context)


class HighscorerAward(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="Highest Scorer", icon="😎"):
        super().__init__(context, title, icon)


class LowscorerAward(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="Lowest Scorer", icon="💩"):
        super().__init__(context, title, icon)


class BlowoutAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, context, title="Biggest Blowout", icon="😂"):
        super().__init__(context, title, icon)


class RaceAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, context, title="Narrow Victory", icon="😱"):
        super().__init__(context, title, icon)


class ShootoutAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, context, title="Biggest Shootout", icon="💣"):
        super().__init__(context, title, icon)


class CFFCvsAFFCAward(Award):
    template_name = "awards/cffc_vs_affc.html"

    def __init__(self, context, title="AFFC vs CFFC", icon="🎙"):
        super().__init__(context, title, icon)


class BuliLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="#1 Bundesliga", icon="🏆"):
        super().__init__(context, title, icon)


class CFFCLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="#1 CFFC", icon="🔵"):
        super().__init__(context, title, icon)


class AFFCLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="#1 AFFC", icon="🔴"):
        super().__init__(context, title, icon)
