import csv

from datetime import datetime

from attr import dataclass
from pytz import timezone

import sleeper_wrapper

from django.conf import settings

from DSTBundesliga.apps.leagues.models import League, DSTPlayer, Roster, Draft, Pick, Player, Team


def get_league_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_league()


def update_league(league_setting, league_data):
    league, _ = League.objects.update_or_create(sleeper_id=league_setting.id, defaults={
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
        "draft_id": league_data.get("draft_id"),
        "avatar_id": league_data.get("avatar"),
        "level": league_setting.level,
        "region": guess_region(league_data.get("name"))
    })
    return league


def delete_old_leagues(league_settings):
    League.objects.exclude(sleeper_id__in=[l.id for l in league_settings]).delete()


def update_or_create_dst_player(league_id, player_data):
    player, _ = DSTPlayer.objects.update_or_create(sleeper_id=player_data.get("user_id"), defaults={
        "display_name": player_data.get("display_name"),
        "avatar_id": player_data.get("avatar")
    })

    league = League.objects.get(sleeper_id=league_id)
    player.leagues.add(league)

    player.save()
    return player


def get_dst_player_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_users()


def update_dst_players_for_league(league_id, player_data):
    players = []
    for dst_player in player_data:
        players.append(update_or_create_dst_player(league_id, dst_player))

    return players


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
                                                    "fpts_against_decimal": roster_settings.get("fpts_against_decimal",
                                                                                                0),
                                                    "fpts_against": roster_settings.get("fpts_against", 0),
                                                    "fpts": roster_settings.get("fpts", 0),
                                                    "settings": roster_settings,
                                                    "reserve": roster_data.get("reserve"),
                                                    "players": roster_data.get("players"),
                                                    "owner": DSTPlayer.objects.filter(sleeper_id=owner_id).first()
                                                })
    roster.save()
    return roster


def get_roster_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_rosters()


def update_rosters_for_league(league_id, roster_data, dst_player_data):
    rosters = []
    dst_player_data_by_id = {
        pd.get("user_id"): pd for pd in dst_player_data
    }
    for roster in roster_data:
        rosters.append(update_or_create_roster(league_id, roster, dst_player_data_by_id))

    return rosters


def guess_region(name):
    if "Nord" in name:
        return "Nord"
    elif "Ost" in name:
        return "Ost"
    elif "Süd" in name:
        return "Süd"
    elif "West" in name:
        return "West"
    elif "CFFC" in name:
        return "CFFC"
    elif "AFFC" in name:
        return "AFFC"
    else:
        return None


def guess_level(name):
    if "2. Bundesliga" in name:
        return 2
    elif "Bundesliga" in name:
        return 1
    elif "Conference" in name:
        return 3
    elif "Divisionsliga" in name:
        return 4
    elif "Regionalliga" in name:
        return 5
    else:
        return 6


def update_or_create_draft(league_id, draft_data):
    start_time = draft_data.get('start_time')
    if start_time:
        start_time = datetime.fromtimestamp(start_time / 1000, tz=timezone('Europe/Berlin'))

    draft, _ = Draft.objects.update_or_create(
        draft_id=draft_data.get('draft_id'),
        league=League.objects.get(sleeper_id=league_id),
        defaults={
            "draft_type": draft_data.get('draft_id', ''),
            "status": draft_data.get('status', ''),
            "start_time": start_time,
            "settings": draft_data.get('settings', {}),
            "season_type": draft_data.get('season_type', ''),
            "season": draft_data.get('season', 0),
            "metadata": draft_data.get('metadata', {}),
            "last_picked": datetime.fromtimestamp(draft_data.get('last_picked') / 1000, tz=timezone('Europe/Berlin')),
            "last_message_time": datetime.fromtimestamp(draft_data.get('last_message_time') / 1000, tz=timezone('Europe/Berlin')),
            "last_message_id": draft_data.get('last_message_id'),
            "draft_order": draft_data.get('draft_order')
        }
    )

    draft.save()
    return draft


def get_draft_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_all_drafts()


def update_drafts_for_league(league_id, drafts_data):
    drafts = []
    for draft in drafts_data:
        drafts.append(update_or_create_draft(league_id, draft))

    return drafts


def update_or_create_pick(draft_id, pick_data):
    pick, _ = Pick.objects.update_or_create(
        draf=Draft.objects.get(draft_id=draft_id),
        defaults={
            "player": Player.objects.get(sleeper_id=pick_data.get('player_id')),
            "user": DSTPlayer.objects.get(sleeper_id=pick_data.get('picked_by')),
            "roster": Roster.objects.get(roster_id=pick_data.get('roster_id')),
            "round": pick_data.get('round', 1),
            "draft_slot": pick_data.get('draft_slot', 1),
            "pick_no": pick_data.get('pick_no', 1),
            "metadata": pick_data.get('metadata', {}),
        }
    )

    pick.save()
    return pick


def get_pick_data(draft_id):
    draft_service = sleeper_wrapper.Drafts(draft_id)
    return draft_service.get_all_picks()


def update_picks_for_draft(draft_id, picks_data):
    picks = []
    for pick in picks_data:
        picks.append(update_or_create_pick(draft_id, pick))

    return picks


def update_everything():
    update_players()
    update_drafts()
    update_leagues()


def update_leagues():
    league_settings = get_league_settings()
    for league in league_settings:
        league_data = get_league_data(league.id)
        update_league(league, league_data)

        dst_player_data = get_dst_player_data(league.id)
        update_dst_players_for_league(league.id, dst_player_data)

        roster_data = get_roster_data(league.id)
        update_rosters_for_league(league.id, roster_data, dst_player_data)

    delete_old_leagues(league_settings)


def update_drafts():
    for league in get_league_settings():
        drafts_data = get_draft_data(league.id)
        drafts = update_drafts_for_league(league.id, drafts_data)

        for draft in drafts:
            picks_data = get_pick_data(draft.draft_id)
            update_picks_for_draft(draft.draft_id, picks_data)


def update_or_create_player(player_id, player_data):
    weight = player_data.get("weight") or 0
    age = player_data.get("age") or 0
    number = player_data.get("number") or 0
    fantasy_positions = player_data.get("fantasy_positions", []) or []
    type = Player.PLAYER
    try:
        int(player_id)
    except ValueError:
        type = Player.TEAM

    player, _ = Player.objects.update_or_create(sleeper_id=player_id, defaults={
        "type": type,
        "hashtag": player_data.get("hashtag", ''),
        "depth_chart_position": player_data.get("depth_chart_position"),
        "status": player_data.get("status", ''),
        "fantasy_positions": ','.join(fantasy_positions),
        "number": number,
        "last_name": player_data.get("last_name", ''),
        "first_name": player_data.get("first_name", ''),
        "weight": int(weight),
        "position": player_data.get("position"),
        "height": player_data.get("height") ,
        "age": age,
        "espn_id": player_data.get("espn_id"),
        "yahoo_id": player_data.get("yahoo_id"),
    })

    team_abbr = player_data.get("team")
    if team_abbr:
        player.team, _ = Team.objects.get_or_create(abbr=team_abbr)

    player.save()
    return player


def get_player_data():
    player_service = sleeper_wrapper.Players()
    return player_service.get_all_players()


def update_players():
    players = []
    for player_id, player_data in get_player_data().items():
        players.append(update_or_create_player(player_id, player_data))

    return players


@dataclass
class LeagueSetting:
    id: str
    name: str
    level: int
    region: str


def get_league_settings(filepath=settings.DEFAULT_LEAGUE_SETTINGS_PATH):
    with open(filepath, encoding='utf-8') as leagues_csv:
        leagues_reader = csv.DictReader(leagues_csv, delimiter=';')
        settings = [
            LeagueSetting(id=row.get('Ligakennung Sleeper'),
                          name=row.get('Name der Liga'),
                          level=guess_level(row.get('Name der Liga')),
                          region=guess_region(row.get('Name der Liga')))
            for row in leagues_reader
        ]

        return settings

