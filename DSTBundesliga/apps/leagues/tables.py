import itertools
from collections import defaultdict
from datetime import datetime

import django_tables2 as tables
from django_tables2.utils import A
import pytz

from DSTBundesliga.apps.leagues.models import League, Roster, Pick, Draft, Player, PlayerDraftStats, WaiverPickup


def _get_date(record):
    if record.start_time < datetime.utcnow().replace(tzinfo=pytz.utc):
        return "Running"

    return record.start_time.astimezone(pytz.timezone('Europe/Berlin')).strftime("%d.%m. %H:%M")


class LeagueTable(tables.Table):

    class Meta:
        model = League
        orderable = False
        fields = ['league_title']

    league_title = tables.TemplateColumn(template_name="Columns/league_title.html", empty_values=())


class RosterTable(tables.Table):

    def __init__(self, data=None, ranking_offset=0):
        self.ranking_offset = ranking_offset
        super(RosterTable, self).__init__(data)

    class Meta:
        model = Roster
        orderable = False
        fields = ['ranking', 'playoff_indicator', 'team_manager', 'faab', 'wins', 'losses', 'ties', 'points']

    ranking = tables.Column(verbose_name='Pl.', empty_values=(), orderable=False, attrs={"td": {"class": "ranking"}, "th": {"class": "ranking"}}, )
    playoff_indicator = tables.TemplateColumn(verbose_name='', template_name="Columns/playoff_indicator.html", empty_values=(), attrs={"td": {"class": "playoff-indicator"}, "th": {"class": "playoff-indicator"}})
    team_manager = tables.TemplateColumn(verbose_name='Team Manager', template_name="Columns/team_manager.html", empty_values=(), attrs={"td": {"class": "team-manager"}, "th": {"class": "team-manager"}})
    faab = tables.Column(verbose_name='FAAB', accessor="waiver_budget_used")
    wins = tables.Column(verbose_name='W', attrs={"td": {"class": "wins"}, "th": {"class": "wins"}})
    losses = tables.Column(verbose_name='L', attrs={"td": {"class": "losses"}, "th": {"class": "losses"}})
    ties = tables.Column(verbose_name='T', attrs={"td": {"class": "ties"}, "th": {"class": "ties"}})
    points = tables.Column(verbose_name='Punkte', attrs={"td": {"class": "points"}, "th": {"class": "points"}})

    def render_ranking(self):
        self.ranking = getattr(self, 'ranking', itertools.count(start=1+self.ranking_offset))
        return next(self.ranking)

    def render_faab(self, value):
        return "{faab}$".format(faab=100-value)


class DraftsADPTable(tables.Table):

    def __init__(self, *args, **kwargs):
        self.pos_ranking_counter = defaultdict(int)
        super().__init__(*args, **kwargs)

    class Meta:
        empty_text = "Es haben noch keine Drafts stattgefunden"
        model = PlayerDraftStats
        orderable = False
        fields = ['ranking', 'player', 'pos', 'adp']

    ranking = tables.Column(verbose_name='Platz', empty_values=(), orderable=False, attrs={"td": {"class": "ranking"}, "th": {"class": "ranking"}}, )
    player = tables.TemplateColumn(verbose_name='Spieler', template_name="Columns/player_stats.html", empty_values=(), attrs={"td": {"class": "player"}, "th": {"class": "player"}})
    pos = tables.Column(verbose_name='Position', accessor="player_position", attrs={"td": {"class": "player_position"}, "th": {"class": "position"}})
    adp = tables.Column(verbose_name='ADP', attrs={"td": {"class": "adp"}, "th": {"class": "adp"}})
    highest_pick = tables.Column(verbose_name='Highest', attrs={"td": {"class": "highest_pick"}, "th": {"class": "highest_pick"}})
    lowest_pick = tables.Column(verbose_name='Lowest', attrs={"td": {"class": "lowest_pick"}, "th": {"class": "lowest_pick"}})

    def render_ranking(self):
        self.ranking = getattr(self, 'ranking', itertools.count(start=1))
        return next(self.ranking)

    def render_adp(self, value):
        return '{:0.1f}'.format(value)

    def render_pos(self, value):
        self.pos_ranking_counter[value] += 1
        return "{pos} {pos_rank}".format(pos=value, pos_rank=self.pos_ranking_counter[value])


class PlayerStatsTable(tables.Table):

    class Meta:
        empty_text = "Es gibt noch keine Stats"
        model = Player
        orderable = False
        fields = ['ranking', 'player', 'pos', 'points', 'avg_points', 'games_played', 'adp']

    ranking = tables.Column(verbose_name='Platz', empty_values=(), orderable=False, attrs={"td": {"class": "ranking"}, "th": {"class": "ranking"}}, )
    player = tables.TemplateColumn(verbose_name='Spieler', template_name="Columns/player.html", empty_values=(), attrs={"td": {"class": "player"}, "th": {"class": "player"}})
    pos = tables.Column(verbose_name='Position', accessor="position", attrs={"td": {"class": "position"}, "th": {"class": "position"}})
    points = tables.Column(verbose_name='Punkte', accessor="points", attrs={"td": {"class": "points"}, "th": {"class": "points"}})
    avg_points = tables.Column(verbose_name='Ø-Punkte', attrs={"td": {"class": "avg_points"}, "th": {"class": "avg_points"}})
    games_played = tables.Column(verbose_name='#Spiele', attrs={"td": {"class": "games_played"}, "th": {"class": "games_played"}})
    adp = tables.Column(verbose_name='ADP',  attrs={"td": {"class": "adp"}, "th": {"class": "adp"}})

    def render_ranking(self):
        self.ranking = getattr(self, 'ranking', itertools.count(start=1))
        return next(self.ranking)

    def render_adp(self, value):
        return '{:0.1f}'.format(value)

    def render_points(self, value):
        return '{:0.1f}'.format(value)

    def render_avg_points(self, value):
        return '{:0.1f}'.format(value)


class NextDraftsTable(tables.Table):

    class Meta:
        empty_text = "Alle Drafts abgeschlossen"
        model = Draft
        orderable = False
        fields = ['league', 'date']

    league = tables.Column(verbose_name='Liga', accessor="league__sleeper_name", attrs={"td": {"class": "league"}, "th": {"class": "league"}})
    date = tables.LinkColumn("draft-board", args=[A("league.sleeper_id")] , text=_get_date, verbose_name='Datum', attrs={"td": {"class": "date"}, "th": {"class": "date"}})


class UpsetAndStealPickTable(tables.Table):

    class Meta:
        empty_text = "Es haben noch nicht ausreichend Drafts stattgefunden"
        model = Pick
        orderable = False
        fields = ['ranking', 'player', 'pick_no', 'adp', 'picked_by']

    ranking = tables.Column(verbose_name='Platz', empty_values=(), orderable=False, attrs={"td": {"class": "ranking"}, "th": {"class": "ranking"}}, )
    player = tables.TemplateColumn(verbose_name='Spieler', template_name="Columns/player_pick.html", empty_values=(), attrs={"td": {"class": "player"}, "th": {"class": "player"}})
    pick_no = tables.Column(verbose_name='Picked at', attrs={"td": {"class": "pick_no"}, "th": {"class": "pick_no"}})
    adp = tables.Column(verbose_name='ADP', attrs={"td": {"class": "adp"}, "th": {"class": "adp"}})
    picked_by = tables.TemplateColumn(verbose_name='Team Manager', template_name="Columns/team_manager.html", empty_values=(), attrs={"td": {"class": "team-manager"}, "th": {"class": "team-manager"}})

    def render_ranking(self):
        self.ranking = getattr(self, 'ranking', itertools.count(start=1))
        return next(self.ranking)

    def render_adp(self, value):
        return '{:0.1f}'.format(value)


class WaiverTopBids(tables.Table):

    class Meta:
        empty_text = "Noch kein Waiver Daten vorhanden"
        model = WaiverPickup
        orderable = False
        fields = ['ranking', 'player', 'bid', 'picked_up_by', 'league']

    ranking = tables.Column(verbose_name='Platz', empty_values=(), orderable=False, attrs={"td": {"class": "ranking"}, "th": {"class": "ranking"}}, )
    player = tables.TemplateColumn(verbose_name='Spieler',  template_name="Columns/player_pick.html", empty_values=(), attrs={"td": {"class": "player"}, "th": {"class": "player"}})
    bid = tables.Column(verbose_name='Bid', empty_values=(), orderable=False, attrs={"td": {"class": "bid"}, "th": {"class": "bid"}}, )
    picked_up_by = tables.TemplateColumn(verbose_name='Team Manager', template_name="Columns/team_manager.html", empty_values=(), attrs={"td": {"class": "team-manager"}, "th": {"class": "team-manager"}})
    league = tables.Column(verbose_name='Liga', accessor="roster__league", attrs={"td": {"class": "league"}, "th": {"class": "league"}})

    def render_ranking(self):
        self.ranking = getattr(self, 'ranking', itertools.count(start=1))
        return next(self.ranking)

    def render_bid(self, value):
        return '{:0}$'.format(value)


class WaiverTopPlayers(tables.Table):

    class Meta:
        empty_text = "Noch kein Waiver Daten vorhanden"
        fields = ['ranking', 'player', 'bid_sum', 'bid_avg', 'bid_sum_success', 'bid_avg_success', 'bid_count', 'leagues']

    ranking = tables.Column(verbose_name='Platz', empty_values=(), orderable=False, attrs={"td": {"class": "ranking"}, "th": {"class": "ranking"}}, )
    player = tables.TemplateColumn(verbose_name='Spieler', orderable=False, template_name="Columns/player_pick.html", empty_values=(), attrs={"td": {"class": "player"}, "th": {"class": "player"}})

    bid_sum = tables.Column(verbose_name='Summe $FAAB', empty_values=(), orderable=False, attrs={"td": {"class": "bid_sum"}, "th": {"class": "bid_sum"}}, )
    bid_sum_success = tables.Column(verbose_name='Summe $FAAB (erfolgreich)', empty_values=(), orderable=False, attrs={"td": {"class": "bid_sum"}, "th": {"class": "bid_sum"}}, )
    bid_count = tables.Column(verbose_name='#Bids insgesamt', empty_values=(), orderable=False, attrs={"td": {"class": "bid_count"}, "th": {"class": "bid_count"}}, )
    leagues = tables.Column(verbose_name='#Beteiligte Ligen', empty_values=(), orderable=False, attrs={"td": {"class": "bid_count"}, "th": {"class": "bid_count"}}, )
    bid_avg = tables.Column(verbose_name='Ø $FAAB', empty_values=(), orderable=False, attrs={"td": {"class": "bid_avg"}, "th": {"class": "bid_avg"}}, )
    bid_avg_success = tables.Column(verbose_name='Ø $FAAB (erfolgreich)', empty_values=(), orderable=False, attrs={"td": {"class": "bid_avg"}, "th": {"class": "bid_avg"}}, )

    def render_ranking(self):
        self.ranking = getattr(self, 'ranking', itertools.count(start=1))
        return next(self.ranking)

    def render_bid_sum(self, value):
        return '{:0}$'.format(value)

    def render_bid_sum_success(self, value):
        return '{:0}$'.format(value)

    def render_bid_avg(self, value):
        return '{:0.1f}$'.format(value)

    def render_bid_avg_success(self, value):
        return '{:0.1f}$'.format(value)




