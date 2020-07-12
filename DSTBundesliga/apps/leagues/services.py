import json

import sleeper_wrapper

from django.conf import settings

from DSTBundesliga.apps.leagues.models import League, DSTPlayer, Roster


def get_league_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_league()


def update_league(league_id, league_data):
    league, _ = League.objects.update_or_create(sleeper_id=league_id, defaults={
        "total_rosters": league_data.get("total_rosters"),
        "status": league_data.get("status"),
        "sport": league_data.get("sport"),
        "settings": league_data.get("settings"),
        "season_type": league_data.get("season_type"),
        "season": league_data.get("season"),
        "scoring_settings": league_data.get("scoring_settings"),
        "roster_positions": league_data.get("roster_positions"),
        "previous_league_id": league_data.get("previous_league_id"),
        "sleeper_name": league_data.get("name"),
        "sleeper_id": league_data.get("league_id"),
        "draft_id": league_data.get("draft_id"),
        "avatar_id": league_data.get("avatar"),
        "level": settings.LEAGUES.get(league_id, {}).get('level'),
        "region": guess_region(league_data.get("name"))
    })


def update_or_create_dst_player(league_id, player_data):
    player, _ = DSTPlayer.objects.update_or_create(sleeper_id=player_data.get("user_id"), defaults={
        "display_name": player_data.get("display_name"),
        "avatar_id": player_data.get("avatar")
    })

    league = League.objects.get(sleeper_id=league_id)
    player.leagues.add(league)

    player.save()


def get_dst_player_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_users()


def update_dst_players_for_league(league_id, player_data):
    for dst_player in player_data:
        update_or_create_dst_player(league_id, dst_player)


def update_or_create_roster(league_id, roster_data, dst_player_data):
    owner_id = roster_data.get("owner_id")
    roster_settings = roster_data.get("settings", {})

    roster, _ = Roster.objects.update_or_create(roster_id=roster_data.get("roster_id"),
                                                league=League.objects.get(sleeper_id=league_id),
                                                defaults={
                                                    "name": dst_player_data.get(owner_id, {}).get("metadata", {}).get(
                                                        "team_name"),
                                                    "starters": roster_data.get("starters"),
                                                    "wins": roster_settings.get("wins", 0),
                                                    "waiver_position": roster_settings.get("waiver_position", 1),
                                                    "waiver_budget_used": roster_settings.get("waiver_budget_used", 0),
                                                    "total_moves": roster_settings.get("total_moves", 0),
                                                    "ties": roster_settings.get("ties", 0),
                                                    "losses": roster_settings.get("losses", 0),
                                                    "fpts_decimal": roster_settings.get("fpts_decimal", 0),
                                                    "fpts_against_decimal": roster_settings.get("fpts_against_decimal", 0),
                                                    "fpts_against": roster_settings.get("fpts_against", 0),
                                                    "fpts": roster_settings.get("fpts", 0),
                                                    "settings": roster_settings,
                                                    "reserve": roster_data.get("reserve"),
                                                    "players": roster_data.get("players"),
                                                    "owner": DSTPlayer.objects.filter(sleeper_id=owner_id).first()
                                                })
    roster.save()


def get_roster_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_rosters()


def update_rosters_for_league(league_id, roster_data, dst_player_data):
    dst_player_data_by_id = {
        pd.get("user_id"): pd for pd in dst_player_data
    }
    for roster in roster_data:
        update_or_create_roster(league_id, roster, dst_player_data_by_id)


def guess_region(name):
    if "Nord" in name:
        return "Nord"
    elif "Ost" in name:
        return "Ost"
    elif "Süd" in name:
        return "Süd"
    elif "West" in name:
        return "West"
    else:
        return None


def update_everything():
    for league_id in settings.LEAGUES.keys():
        league_data = get_league_data(league_id)
        update_league(league_id, league_data)

        dst_player_data = get_dst_player_data(league_id)
        update_dst_players_for_league(league_id, dst_player_data)

        roster_data = get_roster_data(league_id)
        update_rosters_for_league(league_id, roster_data, dst_player_data)
