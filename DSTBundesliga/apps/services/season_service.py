import datetime

from django.conf import settings

from DSTBundesliga.apps.leagues.models import PlayoffMatchup, Season, League, FinalSeasonStanding, Roster


def is_registration_open():
    print(datetime.date.fromisoformat(settings.REGISTRATION_STARTS))
    return datetime.date.fromisoformat(settings.REGISTRATION_STARTS) \
           < datetime.date.today() \
           <= datetime.date.fromisoformat(settings.REGISTRATION_STOPS)


def calc_final_standings(season: Season):
    # Add per league points
    for league in League.objects.filter(season = season, type=League.BUNDESLIGA):
        for rank, roster in enumerate(league.rosters.order_by('-fpts', '-fpts_decimal'), 1):
            season_ranking, created = FinalSeasonStanding.objects.get_or_create(
                season=season,
                roster=roster,
                league=league
            )
            season_ranking.points_ranking_in_league = rank
            season_ranking.points = roster.fpts
            season_ranking.points_decimal = roster.fpts_decimal

            season_ranking.save()

    # Add per level points
    for level in sorted(list(set(League.objects.filter(type=League.BUNDESLIGA).values_list('level', flat=True)))):
        for rank, roster in enumerate(Roster.objects.filter(league__level=level, league__season=season).order_by('-fpts', '-fpts_decimal'), 1):
            season_ranking = FinalSeasonStanding.objects.get(
                season=season,
                roster=roster
            )
            season_ranking.points_ranking_on_level = rank

            season_ranking.save()

    # Add overall points
    for rank, roster in enumerate(Roster.objects.filter(league__type=League.BUNDESLIGA, league__season=season).order_by('-fpts', '-fpts_decimal'), 1):
        season_ranking = FinalSeasonStanding.objects.get(
            season=season,
            roster=roster
        )
        season_ranking.points_ranking_overall = rank

        season_ranking.save()


    # Add ranks per league
    all_bundesliga_league_ids = League.objects.filter(type=League.BUNDESLIGA, season=season).values_list("sleeper_id", flat=True)
    all_mus = PlayoffMatchup.objects.filter(season=season, league_id__in=all_bundesliga_league_ids)

    for rank in [1, 3, 5]:
        for mu in all_mus.filter(bracket="Playoffs", rank=rank):
            winner = Roster.objects.get(league__sleeper_id=mu.league_id, roster_id=mu.winner)
            season_ranking_winner = FinalSeasonStanding.objects.get(
                season=season,
                roster=winner
            )
            season_ranking_winner.rank_in_league = rank
            season_ranking_winner.save()

            loser = Roster.objects.get(league__sleeper_id=mu.league_id, roster_id=mu.loser)
            season_ranking_loser = FinalSeasonStanding.objects.get(
                season=season,
                roster=loser
            )
            season_ranking_loser.rank_in_league = rank + 1
            season_ranking_loser.save()

    for rank in [1, 3, 5]:
        for mu in all_mus.filter(bracket="Toilet Bowl", rank=rank):
            winner = Roster.objects.get(league__sleeper_id=mu.league_id, roster_id=mu.winner)
            season_ranking_winner = FinalSeasonStanding.objects.get(
                season=season,
                roster=winner
            )
            season_ranking_winner.rank_in_league = 13 - rank
            season_ranking_winner.save()

            loser = Roster.objects.get(league__sleeper_id=mu.league_id, roster_id=mu.loser)
            season_ranking_loser = FinalSeasonStanding.objects.get(
                season=season,
                roster=loser
            )
            season_ranking_loser.rank_in_league = 13 - 1 -rank
            season_ranking_loser.save()

