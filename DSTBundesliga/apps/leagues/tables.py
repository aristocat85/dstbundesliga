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
    ranking = tables.Column(verbose_name='Pl.', empty_values=(), orderable=False, attrs={"td": {"class": "ranking"}, "th": {"class": "ranking"}}, )
    playoff_indicator = tables.TemplateColumn(verbose_name='', template_name="Columns/playoff_indicator.html", empty_values=(), attrs={"td": {"class": "playoff-indicator"}, "th": {"class": "playoff-indicator"}})
    team_manager = tables.TemplateColumn(verbose_name='Team Manager', template_name="Columns/team_manager.html", empty_values=(), attrs={"td": {"class": "team-manager"}, "th": {"class": "team-manager"}})
    wins = tables.Column(verbose_name='W', attrs={"td": {"class": "wins"}, "th": {"class": "wins"}})
    losses = tables.Column(verbose_name='L', attrs={"td": {"class": "losses"}, "th": {"class": "losses"}})
    ties = tables.Column(verbose_name='T', attrs={"td": {"class": "ties"}, "th": {"class": "ties"}})
    fpts = tables.Column(verbose_name='Punkte', attrs={"td": {"class": "points"}, "th": {"class": "points"}})

    def render_ranking(self):
        self.ranking = getattr(self, 'ranking', itertools.count(start=1))
        return next(self.ranking)

    class Meta:
        model = Roster
        orderable = False
        fields = ['ranking', 'playoff_indicator', 'team_manager', 'wins', 'losses', 'ties', 'fpts']


