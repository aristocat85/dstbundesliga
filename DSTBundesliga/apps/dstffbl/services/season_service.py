import sleeper_wrapper
from django.contrib.auth.models import User

from DSTBundesliga.apps.dstffbl.models import SeasonUser
from DSTBundesliga.apps.leagues.models import DSTPlayer, League, Season


def get_last_years_league(player: DSTPlayer):
    try:
        return League.objects.filter(id__in=[r.league.id for r in player.roster_set.all()]).get(type=League.BUNDESLIGA)
    except League.DoesNotExist:
        return None


def update_last_years_leagues():
    for su in SeasonUser.objects.filter(season=Season.get_active()):
        try:
            dst_player = DSTPlayer.objects.get(sleeper_id=su.sleeper_id)
            su.last_years_league = get_last_years_league(dst_player)
        except DSTPlayer.DoesNotExist:
            su.last_years_league = None
            su.new_player = False
            pass

    su.save()


def create_season_users(users):
    for user_tuple in users:
        dst_player = None
        last_years_league = None

        email, sleeper_username, commish, region = user_tuple
        sleeper_user = sleeper_wrapper.User(sleeper_username)

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

        DSTPlayer.objects.update_or_create(sleeper_id=sleeper_id, defaults={
            "display_name": sleeper_username
        })
