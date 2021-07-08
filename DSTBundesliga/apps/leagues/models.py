from django.db import models
from django.urls import reverse

from jsonfield import JSONField
from datetime import datetime


class Season(models.Model):
    year = models.IntegerField(default=datetime.now().year)
    name = models.CharField(max_length=50)
    active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.active:
            Season.objects.filter(active=True).update(active=False)

        super(Season, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    @staticmethod
    def get_active():
        current_year = datetime.now().year
        season, _ = Season.objects.get_or_create(active=True, defaults={
            'year': current_year,
            'name': 'Saison {current_year}/{next_year}'.format(current_year=current_year, next_year=current_year+1)
        })

        return season


class League(models.Model):
    level = models.IntegerField(default=0)
    conference = models.CharField(max_length=30, null=True)
    region = models.CharField(max_length=30, null=True)

    # Sleeper Data
    total_rosters = models.IntegerField(default=12)
    status = models.CharField(max_length=20)
    sport = models.CharField(max_length=30)
    settings = JSONField()
    season_type = models.CharField(max_length=30)
    season = models.IntegerField(default=2020)
    scoring_settings = JSONField()
    roster_positions = JSONField()
    previous_league_id = models.CharField(max_length=100, null=True)
    sleeper_name = models.CharField(max_length=50)
    sleeper_id = models.CharField(max_length=50, db_index=True, unique=True)
    draft_id = models.CharField(max_length=50)
    avatar_id = models.CharField(max_length=100)

    @property
    def draft(self):
        return self.drafts.first()

    def __str__(self):
        return "{name} - {id}".format(name=self.sleeper_name, id=self.sleeper_id)

    @property
    def url(self):
        return reverse('league-detail', kwargs={'league_id': self.sleeper_id})


class DSTPlayer(models.Model):
    # Sleeper Data
    sleeper_id = models.CharField(max_length=50, db_index=True, unique=True)
    display_name = models.CharField(max_length=50, db_index=True)
    avatar_id = models.CharField(max_length=100, null=True)
    leagues = models.ManyToManyField(League)

    def __str__(self):
        return "{display_name} - {sleeper_id}".format(display_name=self.display_name, sleeper_id=self.sleeper_id)


class Team(models.Model):
    name = models.CharField(max_length=50)
    abbr = models.CharField(max_length=10)


class Player(models.Model):
    PLAYER = 1
    TEAM = 2
    TYPES = [
        (PLAYER, 'Player'),
        (TEAM, 'Team')
    ]

    type = models.IntegerField(choices=TYPES, default=PLAYER)
    # Sleeper Data
    sleeper_id = models.CharField(max_length=10, db_index=True, unique=True)
    last_name = models.CharField(max_length=50, default='')
    first_name = models.CharField(max_length=50, default='')
    fantasy_positions = models.CharField(max_length=50, default='')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    hashtag = models.CharField(max_length=50, null=True)
    depth_chart_position = models.CharField(max_length=50, null=True)
    status = models.CharField(max_length=20, null=True)
    number = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)
    position = models.CharField(max_length=50, null=True)
    height = models.CharField(max_length=10, null=True)
    age = models.IntegerField(default=0)
    espn_id = models.CharField(max_length=50, null=True)
    yahoo_id = models.CharField(max_length=50, null=True)

    @property
    def name(self):
        return "{first_name} {last_name}".format(first_name=self.first_name, last_name=self.last_name)

    def __str__(self):
        return self.name


class Roster(models.Model):
    class Meta:
        ordering = ["-wins", "-ties", "-fpts", "-fpts_decimal"]

    # Sleeper Data
    name = models.CharField(max_length=100, null=True)
    starters = models.CharField(max_length=100)
    wins = models.IntegerField(default=0)
    waiver_position = models.IntegerField(default=1)
    waiver_budget_used = models.IntegerField(default=0)
    total_moves = models.IntegerField(default=0)
    ties = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    fpts_decimal = models.IntegerField(default=0)
    fpts_against_decimal = models.IntegerField(default=0)
    fpts_against = models.IntegerField(default=0)
    fpts = models.IntegerField(default=0)
    settings = JSONField()
    roster_id = models.IntegerField()
    reserve = models.CharField(max_length=100, null=True)
    players = models.CharField(max_length=255, null=True)
    owner = models.ForeignKey(DSTPlayer, on_delete=models.CASCADE, null=True)
    league = models.ForeignKey(League, related_name='rosters', on_delete=models.CASCADE)

    @property
    def points(self):
        return "{}.{}".format(self.fpts, self.fpts_decimal)


class Draft(models.Model):
    # Sleeper Data
    draft_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    start_time = models.DateTimeField(blank=True, null=True)
    settings = JSONField()
    season_type = models.CharField(max_length=20)
    season = models.IntegerField()
    metadata = JSONField()
    league = models.ForeignKey(League, related_name="drafts", on_delete=models.CASCADE)
    last_picked = models.DateTimeField(null=True)
    last_message_time = models.DateTimeField(null=True)
    last_message_id = models.CharField(max_length=50, null=True)
    draft_id = models.CharField(max_length=50)
    draft_order = JSONField(blank=True, null=True)
    slot_to_roster_id = JSONField(blank=True, null=True)


class Pick(models.Model):
    # Sleeper Data
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="picks")
    owner = models.ForeignKey(DSTPlayer, related_name="picks", on_delete=models.CASCADE, null=True)
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE)
    draft = models.ForeignKey(Draft, related_name="picks", on_delete=models.CASCADE)
    round = models.IntegerField(default=1)
    draft_slot = models.IntegerField(default=1)
    pick_no = models.IntegerField(default=1)
    metadata = JSONField()

    def __str__(self):
        return "{round}.{draft_slot} ({pick_no}) - {player}".format(round=self.round,
                                                                    draft_slot=self.draft_slot,
                                                                    pick_no=self.pick_no,
                                                                    player=self.player.name)


class Matchup(models.Model):
    week = models.IntegerField(db_index=True)
    matchup_id = models.IntegerField(db_index=True)
    league_id = models.CharField(max_length=50, db_index=True)
    roster_id_one = models.IntegerField()
    starters_one = models.CharField(max_length=255, null=True)
    players_one = models.CharField(max_length=255, null=True)
    points_one = models.DecimalField(max_digits=6, decimal_places=3)
    roster_id_two = models.IntegerField()
    starters_two = models.CharField(max_length=255, null=True)
    players_two = models.CharField(max_length=255, null=True)
    points_two = models.DecimalField(max_digits=6, decimal_places=3)


class PlayoffMatchup(models.Model):
    bracket = models.CharField(max_length=20, db_index=True)
    round = models.IntegerField(db_index=True)
    matchup_id = models.IntegerField(db_index=True)
    league_id = models.CharField(max_length=50, db_index=True)
    roster_id_one = models.IntegerField(null=True)
    roster_id_two = models.IntegerField(null=True)
    winner = models.IntegerField(null=True)
    loser = models.IntegerField(null=True)
    rank = models.IntegerField(null=True)


class StatsWeek(models.Model):
    week = models.IntegerField(db_index=True)
    season_type = models.CharField(max_length=30)
    season = models.IntegerField(default=2020)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="stats")
    points = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    stats = JSONField()
    projected_points = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    projected_stats = JSONField()
