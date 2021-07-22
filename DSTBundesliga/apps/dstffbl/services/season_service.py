import sleeper_wrapper
from django.contrib.auth.models import User

from DSTBundesliga.apps.dstffbl.models import SeasonUser
from DSTBundesliga.apps.leagues.models import DSTPlayer, League, Season


def get_last_years_league(player: DSTPlayer):
    return League.objects.filter(id__in=[r.league.id for r in player.roster_set.all()]).get(type=League.BUNDESLIGA)


def update_last_years_leagues():
    for su in SeasonUser.objects.filter(season=Season.get_active()):
        dst_player = DSTPlayer.objects.get(sleeper_id = su.sleeper_id)
        if dst_player:
            su.last_years_league = get_last_years_league(dst_player)
            su.save()


def create_season_users(users):
    dst_player = None
    last_years_league = None

    for user_tuple in users:
        email, sleeper_user, commish, region = user_tuple
        sleeper_user = sleeper_wrapper.User(sleeper_user)

        sleeper_id = sleeper_user.get_user_id()
        try:
            dst_player = DSTPlayer.objects.get(sleeper_id=sleeper_id)
            if dst_player:
                last_years_league = get_last_years_league(player=dst_player)
        except:
            pass

        dummy_user, _ = User.objects.get_or_create(username=email, email=email)

        SeasonUser.objects.get_or_create(
            user=dummy_user,
            season=Season.get_active(),
            sleeper_id=sleeper_id,
            new_player=dst_player is None,
            last_years_league=last_years_league,
            region=region,
            possible_commish=commish
        )
