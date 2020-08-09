import django_tables2 as tables
from django.db.models import Avg
from django.shortcuts import render

from DSTBundesliga.apps.leagues.config import LEVEL_MAP
from DSTBundesliga.apps.leagues.models import League, Roster, Draft, Pick, News
from DSTBundesliga.apps.leagues.tables import LeagueTable, RosterTable, DraftsADPTable, NextDraftsTable


class LeagueView(tables.SingleTableView):
    table_class = LeagueTable
    queryset = League.objects.all().order_by('level', 'sleeper_name')
    template_name = "league_list.html"


def roster_list(request, league_id):
    league = League.objects.get(sleeper_id=league_id)

    title = league.sleeper_name
    table = RosterTable(Roster.objects.filter(league=league))

    return render(request, "roster_list.html", {
        "title": title,
        "table": table
    })


def level_detail(request, level, region=None):
    league_objects = League.objects.filter(level=level).order_by('sleeper_name')
    if region:
        league_objects = league_objects.filter(region=region)
    leagues = [{
        "title": league.sleeper_name,
        "table": RosterTable(Roster.objects.filter(league=league))
    } for league in league_objects]

    return render(request, "level_detail.html", {
        "leagues": leagues
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
        context["my_league"] = my_league_id
        context["title"] = title
        context["table"] = table

    return render(request, "my_league.html", context)


def draft_stats(request, position=None):
    drafts_done = Draft.objects.filter(status='completed').count()
    drafts_overall = League.objects.all().count()
    drafts_done_percent = drafts_done / drafts_overall * 100

    picks = Pick.objects.all()

    if position:
        picks = picks.filter(player__position=position)

    adp_table = DraftsADPTable(picks.annotate(adp=Avg("pick_no")).order_by("adp"))

    drafts = Draft.objects.all()
    next_drafts_table = NextDraftsTable(drafts.exclude(start_time=None).exclude(status='completed').order_by('start_time')[:10])

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
        "drafts_overall": drafts_overall,
        "drafts_done_percent": drafts_done_percent,
        "adp_table": adp_table,
        "positions": positions,
        "selected_position": position or "",
        "next_drafts_table": next_drafts_table
    })


def home(request):
    drafts = Draft.objects.all()
    next_drafts_table = NextDraftsTable(drafts.exclude(start_time=None).order_by('start_time')[:10])

    news = News.objects.all().order_by('-date')[:3]

    return render(request, "home.html", {
        "next_drafts_table": next_drafts_table,
        "news_list": news
    })
