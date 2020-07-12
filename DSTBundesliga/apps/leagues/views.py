import django_tables2 as tables
from django.shortcuts import render

from DSTBundesliga.apps.leagues.models import League, Roster
from DSTBundesliga.apps.leagues.tables import LeagueTable, RosterTable


LEVEL_MAP = {
    1: "Bundesliga",
    2: "2. Bundesliga",
    3: "Divisionsliga",
    4: "Regionalliga"
}


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


def level_detail(request, level):
    league_objects = League.objects.filter(level=level).order_by('sleeper_name')
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
