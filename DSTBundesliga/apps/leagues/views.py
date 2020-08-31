from datetime import datetime

import django_tables2 as tables
import pytz
from django.db.models import Avg, ExpressionWrapper, F, DecimalField, IntegerField, Sum, Count, Min, Max
from django.shortcuts import render
from django.urls import reverse

from DSTBundesliga.apps.leagues.config import LEVEL_MAP, LOGO_MAP
from DSTBundesliga.apps.leagues.models import League, Roster, Draft, Pick, News, Player, DSTPlayer
from DSTBundesliga.apps.leagues.tables import LeagueTable, RosterTable, DraftsADPTable, NextDraftsTable, \
    UpsetAndStealPickTable


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

    if position:
        players = players.filter(position=position)
    else:
        players = players.filter(pick_count__gte=drafts_done*0.5)

    adp_table = DraftsADPTable(players.exclude(adp=None).order_by('adp')[:200])

    next_drafts_table = NextDraftsTable(drafts.exclude(start_time=None).exclude(start_time__lte=datetime.utcnow().replace(tzinfo=pytz.utc)).exclude(status__in=['complete', 'drafting', 'paused']).order_by('start_time', 'league__level', 'league__sleeper_name')[:10])

    adp_diff = ExpressionWrapper((F('pick_no')-F('adp')) * 10, output_field=IntegerField())
    upset_and_value_picks = picks.annotate(adp=Avg('player__pick__pick_no'), pick_count=Count('player__id')).filter(pick_count__gte=drafts_done*0.8).annotate(adp_diff=adp_diff)
    upset_table = UpsetAndStealPickTable(upset_and_value_picks.order_by('adp_diff')[:5])
    steal_table = UpsetAndStealPickTable(upset_and_value_picks.order_by('-adp_diff')[:5])

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
    drafts = Draft.objects.all()
    next_drafts_table = NextDraftsTable(drafts.exclude(start_time=None).exclude(status='complete').order_by('start_time', 'league__level', 'league__sleeper_name')[:10])

    news = News.objects.all().order_by('-date')[:3]

    return render(request, "leagues/home.html", {
        "next_drafts_table": next_drafts_table,
        "news_list": news
    })


def draftboard(request, league_id):
    draft = Draft.objects.get(league__sleeper_id=league_id)
    picks = draft.picks.order_by('round', 'draft_slot')
    picks_count = picks.count()
    fill_picks = []
    fill_pick_round = 16
    fill_picks_at_front = True
    fill_pick_pos = picks_count
    if picks_count < 180:
        fill_picks = range(12 - (((picks_count-1) % 12) + 1))
        fill_pick_round = int(picks_count/12) + 1
        if fill_pick_round % 2 == 1:
            fill_picks_at_front = False
        else:
            fill_pick_round = int(picks_count/12)
            fill_pick_pos = fill_pick_round * 12

    owners = DSTPlayer.objects.filter(sleeper_id__in=draft.draft_order.keys())

    draft_order = sorted([(draft.draft_order.get(owner.sleeper_id), owner) for owner in owners], key=lambda do: do[0])

    return render(request, "stats/draftboard.html", {
        "draft": draft,
        "draft_order": draft_order,
        "picks": picks,
        "fill_picks": fill_picks,
        "fill_pick_pos": fill_pick_pos,
        "fill_picks_at_front": fill_picks_at_front
    })
