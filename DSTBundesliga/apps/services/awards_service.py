import random
from datetime import datetime, timedelta

from django.db.models.functions import Abs
from django.db.models import F, Sum, Count
from django.template import RequestContext
from django.template.loader import get_template, select_template, render_to_string

from DSTBundesliga.apps.leagues.models import Matchup, Roster, League, Season, WaiverPickup, Player


class AwardService():
    def __init__(self, request, week=None, league_id=None):
        matchups = Matchup.objects.filter(season=Season.get_active(), league_id__in=League.objects.filter(type=League.BUNDESLIGA).values_list('sleeper_id'))
        waivers = WaiverPickup.objects.filter(season=Season.get_active(), changed_ts__gte=datetime.now()-timedelta(days=7))

        if week:
            matchups = matchups.filter(week=week)

        if league_id:
            matchups = matchups.filter(league_id=league_id)
            waivers = waivers.filter(roster__league__sleeper_id=league_id)

        self.league_id = league_id
        self.week = week
        self.matchups = matchups
        self.narrow_matchups = matchups.annotate(point_difference=Abs(F('points_one') - F('points_two')))
        self.rosters = Roster.objects.filter(league__season=Season.get_active(), league__type=League.BUNDESLIGA)
        self.waivers = waivers

        self.request = request

    def get_all(self):
        awards = []

        if self.matchups.count() > 0:
            awards.extend([
                self.get_highscorer(),
                self.get_lowscorer(),
                self.get_blowout_victory(),
                self.get_narrow_victory(),
                self.get_shootout(),
                self.get_buli_leader(),
                self.get_cffc_vs_affc(),
                self.get_cffc_leader(),
                self.get_affc_leader()
            ])

        if self.waivers.count() > 0:
            awards.extend(
                [
                    self.get_most_wanted_waiver(),
                    self.get_highest_bid_waiver()
                ]
            )

        return awards

    def get_all_for_league(self):
        awards = []

        if self.matchups.count() > 0:
            awards.extend([
                self.get_highscorer(),
                self.get_lowscorer(),
                self.get_blowout_victory(),
                self.get_narrow_victory(),
                self.get_shootout(),
            ])

        if self.waivers.count() > 0:
            awards.extend(
                [
                    self.get_most_wanted_waiver(),
                    self.get_highest_bid_waiver()
                ]
            )

        return awards

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

        return HighscorerAward(self.request, context)

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

        return LowscorerAward(self.request, context)

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

        return RaceAward(self.request, context)

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

        return BlowoutAward(self.request, context)

    def get_shootout(self):
        shootout = self.narrow_matchups.filter(point_difference__lte=10).annotate(
            points_sum=F('points_one') + F('points_two')).order_by('-points_sum').first()

        if not shootout:
            shootout = self.narrow_matchups.filter(point_difference__lte=20).annotate(
                points_sum=F('points_one') + F('points_two')).order_by('-points_sum').first()

        if not shootout:
            shootout = self.narrow_matchups.annotate(points_sum=F('points_one') + F('points_two')).order_by(
                '-points_sum').first()

        roster_one = self.rosters.get(league__sleeper_id=shootout.league_id, roster_id=shootout.roster_id_one)
        roster_two = self.rosters.get(league__sleeper_id=shootout.league_id, roster_id=shootout.roster_id_two)

        context = {
            'roster_one': roster_one,
            'roster_two': roster_two,
            'score_one': shootout.points_one,
            'score_two': shootout.points_two,
            'league': roster_one.league
        }

        return ShootoutAward(self.request, context)

    def get_cffc_vs_affc(self):
        cffc_league_ids = League.objects.get_active().filter(conference="CFFC").values_list('sleeper_id', flat=True)
        affc_league_ids = League.objects.get_active().filter(conference="AFFC").values_list('sleeper_id', flat=True)

        points_cffc = self.matchups.filter(league_id__in=cffc_league_ids).aggregate(
            point_sum=Sum('points_one') + Sum('points_two')).get("point_sum")
        points_affc = self.matchups.filter(league_id__in=affc_league_ids).aggregate(
            point_sum=Sum('points_one') + Sum('points_two')).get("point_sum")

        context = {
            'name_one': 'AFFC',
            'name_two': 'CFFC',
            'score_one': points_affc,
            'score_two': points_cffc
        }

        return CFFCvsAFFCAward(self.request, context)

    def get_buli_leader(self):
        leader = Roster.objects.filter(league__season=Season.get_active(), league__level=1).first()

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return BuliLeader(self.request, context)

    def get_cffc_leader(self):
        leader = Roster.objects.filter(league__season=Season.get_active(), league__conference='CFFC').first()
        if not leader:
            return None

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return CFFCLeader(self.request, context)

    def get_affc_leader(self):
        leader = Roster.objects.filter(league__season=Season.get_active(), league__conference='AFFC').first()
        if not leader:
            return None

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return AFFCLeader(self.request, context)

    def get_most_wanted_waiver(self):
        waiver_pickup = self.waivers.values('player').annotate(target_count=Count('player')).order_by('-target_count').first()

        player = Player.objects.get(id=waiver_pickup.get("player"))

        context = {
            'player': player,
            'bid': "{bids} bids".format(bids=waiver_pickup.get("target_count"))
        }

        return WaiverMostWanted(self.request, context)

    def get_highest_bid_waiver(self):
        waiver_pickup = self.waivers.filter(status='complete').order_by('-bid').first()

        context = {
            'player': waiver_pickup.player,
            'bid': "{bid}$".format(bid=waiver_pickup.bid)
        }

        return WaiverMostSpent(self.request, context)


class Award():
    template_name = ""
    must_be_first = False

    def __init__(self, request, context, title=None, icon=None):
        super().__init__()

        self.request = request

        context.update({
            "title": title,
            "icon": icon
        })

        self.context = context

    def __str__(self):
        return self.render(self.context)

    def render(self, context):
        return render_to_string(self.template_name, context=context, request=self.request)


class HighscorerAward(Award):
    template_name = "awards/player_award.html"

    def __init__(self, request, context, title="Highest Scorer", icon="😎"):
        super().__init__(request, context, title, icon)


class LowscorerAward(Award):
    template_name = "awards/player_award.html"

    def __init__(self, request, context, title="Lowest Scorer", icon="💩"):
        super().__init__(request, context, title, icon)


class BlowoutAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, request, context, title="Biggest Blowout", icon="😂"):
        super().__init__(request, context, title, icon)


class RaceAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, request, context, title="Narrow Victory", icon="😱"):
        super().__init__(request, context, title, icon)


class ShootoutAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, request, context, title="Biggest Shootout", icon="💣"):
        super().__init__(request, context, title, icon)


class CFFCvsAFFCAward(Award):
    template_name = "awards/cffc_vs_affc.html"

    def __init__(self, request, context, title="AFFC vs CFFC", icon="🎙"):
        super().__init__(request, context, title, icon)


class BuliLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, request, context, title="#1 Bundesliga", icon="🏆"):
        super().__init__(request, context, title, icon)


class CFFCLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, request, context, title="#1 CFFC", icon="🔵"):
        super().__init__(request, context, title, icon)


class AFFCLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, request, context, title="#1 AFFC", icon="🔴"):
        super().__init__(request, context, title, icon)


class WaiverMostWanted(Award):
    template_name = "awards/waiver_award.html"

    def __init__(self, request, context, title="#1 Waiver Target", icon="📈"):
        super().__init__(request, context, title, icon)


class WaiverMostSpent(Award):
    template_name = "awards/waiver_award.html"

    def __init__(self, request, context, title="#1 Waiver Spent", icon="💸"):
        super().__init__(request, context, title, icon)
