from django.db import models

from jsonfield import JSONField


class League(models.Model):
    level = models.IntegerField(default=0)
    region = models.CharField(max_length=30, null=True)

    #Sleeper Data
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


class DSTPlayer(models.Model):
    #Sleeper Data
    sleeper_id = models.CharField(max_length=50, db_index=True, unique=True)
    display_name = models.CharField(max_length=50, db_index=True)
    avatar_id = models.CharField(max_length=100, null=True)
    leagues = models.ManyToManyField(League)


class Team(models.Model):
    name = models.CharField(max_length=50)
    abbr = models.CharField(max_length=10)


class Player(models.Model):
    #Sleeper Data
    sleeper_id = models.IntegerField()
    hashtag = models.CharField(max_length=50)
    depth_chart_position = models.IntegerField()
    status = models.CharField(max_length=20)
    fantasy_positions = models.CharField(max_length=50)
    number = models.IntegerField()
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    weight = models.IntegerField()
    position = models.CharField(max_length=50)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    height = models.CharField(max_length=10)
    age = models.IntegerField()
    espn_id = models.CharField(max_length=50)
    yahoo_id = models.CharField(max_length=50)


class Roster(models.Model):
    #Sleeper Data
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
    reserve = models.CharField(max_length=100)
    players = models.CharField(max_length=255)
    owner = models.ForeignKey(DSTPlayer, on_delete=models.CASCADE, null=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

    @property
    def avatar_id(self):
        if self.owner:
            return self.owner.avatar_id
        else:
            return None

    @property
    def owner_name(self):
        if self.owner:
            return self.owner.display_name
        else:
            return None


class Draft(models.Model):
    #Sleeper Data
    draft_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    start_time = models.DateTimeField()
    settings = JSONField()
    season_type = models.CharField(max_length=20)
    season = models.IntegerField()
    metadata = JSONField()
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    last_picked = models.DateTimeField()
    last_message_time = models.DateTimeField()
    last_message_id = models.CharField(max_length=50)
    draft_id = models.CharField(max_length=50)
    draft_order = JSONField()
    slot_to_roster_id = JSONField()


class Pick(models.Model):
    #Sleeper Data
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    user = models.ForeignKey(DSTPlayer, on_delete=models.CASCADE)
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE)
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE)
    round = models.IntegerField(default=1)
    draft_slot = models.IntegerField(default=1)
    pick_no = models.IntegerField(default=1)
    metadata = JSONField()