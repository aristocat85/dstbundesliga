import itertools

import django_tables2 as tables

from DSTBundesliga.apps.leagues.models import League, Roster


class LeagueTable(tables.Table):
    league_title = tables.TemplateColumn(template_name="Columns/league_title.html", empty_values=())

    class Meta:
        model = League
        orderable = False
        fields = ['league_title']


class RosterTable(tables.Table):
    roster_avatar = tables.TemplateColumn(template_name="Columns/avatar.html", empty_values=())
    roster_name = tables.TemplateColumn(template_name="Columns/roster_name.html", empty_values=())
    counter = tables.Column(empty_values=(), orderable=False)

    def render_counter(self):
        self.row_counter = getattr(self, 'row_counter', itertools.count(start=1))
        return next(self.row_counter)

    class Meta:
        model = Roster
        orderable = False
        fields = ['counter', 'roster_avatar', 'roster_name']


