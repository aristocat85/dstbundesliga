import random

from django.db.models.functions import Abs
from django.db.models import F, Sum
from django.template.loader import get_template, select_template

from DSTBundesliga.apps.leagues.models import Matchup, Roster, League
from DSTBundesliga.settings import LISTENER_LEAGUE_ID


class AwardService():
    def __init__(self, week=None, league_id=None):
        matchups = Matchup.objects.exclude(league_id=LISTENER_LEAGUE_ID)

        if week:
            matchups = matchups.filter(week=week)

        if league_id:
            matchups = matchups.filter(league_id=league_id)

        self.matchups = matchups
        self.narrow_matchups = matchups.annotate(point_difference=Abs(F('points_one') - F('points_two')))
        self.rosters = Roster.objects.exclude(league__sleeper_id=LISTENER_LEAGUE_ID)

    def get_all(self):
        return [
            self.get_highscorer(),
            self.get_lowscorer(),
            self.get_blowout_victory(),
            self.get_narrow_victory(),
            self.get_shootout(),
            self.get_buli_leader(),
            self.get_cffc_vs_affc(),
            self.get_cffc_leader(),
            self.get_affc_leader()
        ]

    def get_all_for_league(self):
        return [
            self.get_highscorer(),
            self.get_lowscorer(),
            self.get_blowout_victory(),
            self.get_narrow_victory(),
            self.get_shootout()
        ]

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

        return HighscorerAward(context)

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

        return LowscorerAward(context)

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

        return RaceAward(context)

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

        return BlowoutAward(context)

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

        return ShootoutAward(context)

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

        return CFFCvsAFFCAward(context)

    def get_buli_leader(self):
        leader = Roster.objects.filter(league__level=1).first()

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return BuliLeader(context)

    def get_cffc_leader(self):
        leader = Roster.objects.filter(league__conference='CFFC').first()

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return CFFCLeader(context)

    def get_affc_leader(self):
        leader = Roster.objects.filter(league__conference='AFFC').first()

        context = {
            'roster': leader,
            'league': leader.league,
            'score': float(leader.points)
        }

        return AFFCLeader(context)


class Award():
    template_name = ""
    must_be_first = False

    def __init__(self, context, title=None, icon=None):
        super().__init__()

        context.update({
            "title": title,
            "icon": icon
        })

        self.context = context

    def __str__(self):
        return self.render(self.context)

    def render(self, context):
        template_name = self.template_name

        if isinstance(template_name, str):
            template = get_template(template_name)
        else:
            # assume some iterable was given
            template = select_template(template_name)

        return template.render(context=context)


class HighscorerAward(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="Highest Scorer", icon="😎"):
        super().__init__(context, title, icon)


class LowscorerAward(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="Lowest Scorer", icon="💩"):
        super().__init__(context, title, icon)


class BlowoutAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, context, title="Biggest Blowout", icon="😂"):
        super().__init__(context, title, icon)


class RaceAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, context, title="Narrow Victory", icon="😱"):
        super().__init__(context, title, icon)


class ShootoutAward(Award):
    template_name = "awards/match_award.html"

    def __init__(self, context, title="Biggest Shootout", icon="💣"):
        super().__init__(context, title, icon)


class CFFCvsAFFCAward(Award):
    template_name = "awards/cffc_vs_affc.html"

    def __init__(self, context, title="AFFC vs CFFC", icon="🎙"):
        super().__init__(context, title, icon)


class BuliLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="#1 Bundesliga", icon="🏆"):
        super().__init__(context, title, icon)


class CFFCLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="#1 CFFC", icon="🔵"):
        super().__init__(context, title, icon)


class AFFCLeader(Award):
    template_name = "awards/player_award.html"

    def __init__(self, context, title="#1 AFFC", icon="🔴"):
        super().__init__(context, title, icon)
