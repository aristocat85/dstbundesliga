import django_tables2 as tables
from django.shortcuts import render

from DSTBundesliga.apps.leagues.models import League, Roster
from DSTBundesliga.apps.leagues.tables import LeagueTable, RosterTable


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
