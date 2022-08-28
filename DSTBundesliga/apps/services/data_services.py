from datetime import datetime
import requests
from typing import List
from dataclasses import dataclass
from pytz import timezone

from django.db.models import Count, Avg

import sleeper_wrapper
from sleeper_wrapper import BaseApi

from DSTBundesliga.apps.leagues.config import POSITIONS
from DSTBundesliga.apps.leagues.models import League, DSTPlayer, Roster, Draft, Pick, Player, Team, Matchup, StatsWeek, \
    PlayoffMatchup, Season, PlayerDraftStats, WaiverPickup
from DSTBundesliga.apps.services.state_service import StateService


@dataclass
class LeagueSetting:
    id: str
    name: str
    type: int or None
    level: int
    conference: str or None
    region: str or None


def get_league_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    return league_service.get_league()


def update_or_create_league(league_setting: LeagueSetting, league_data):
    league, _ = League.objects.update_or_create(sleeper_id=league_setting.id, defaults={
        "total_rosters": league_data.get("total_rosters"),
        "status": league_data.get("status"),
        "sport": league_data.get("sport"),
        "settings": league_data.get("settings"),
        "season_type": league_data.get("season_type"),
        "scoring_settings": league_data.get("scoring_settings"),
        "roster_positions": league_data.get("roster_positions"),
        "previous_league_id": league_data.get("previous_league_id"),
        "sleeper_name": league_data.get("name"),
        "draft_id": league_data.get("draft_id"),
        "avatar_id": league_data.get("avatar"),
        "type": league_setting.type or League.BUNDESLIGA,
        "level": league_setting.level,
        "conference": league_setting.conference,
        "region": league_setting.region
    })
    return league


def update_league(league: League, league_data):
    league.total_rosters = league_data.get("total_rosters")
    league.status = league_data.get("status")
    league.sport = league_data.get("sport")
    league.settings = league_data.get("settings")
    league.season_type = league_data.get("season_type")
    league.scoring_settings = league_data.get("scoring_settings")
    league.roster_positions = league_data.get("roster_positions")
    league.previous_league_id = league_data.get("previous_league_id")
    league.sleeper_name = league_data.get("name")
    league.draft_id = league_data.get("draft_id")
    league.avatar_id = league_data.get("avatar")

    league.save()

    return league


def delete_old_leagues(league_settings: List[LeagueSetting], dry_run=True):
    leagues_to_delete = League.objects.exclude(sleeper_id__in=[l.id for l in league_settings])
    if dry_run:
        print("DRY RUN - Would delete the following Leagues:")
        for league in leagues_to_delete:
            print(league)
        print("Use --force to delete leagues.")
    else:
        print("Deleting Leagues now...")
        leagues_to_delete.delete()


def delete_old_drafts(league_id, draft_id):
    if draft_id:
        drafts_to_delete = Draft.objects.filter(league__sleeper_id=league_id).exclude(draft_id=draft_id)
        if drafts_to_delete.count() > 0:
            print('Deleting old drafts for league %s' % league_id)
        for draft in drafts_to_delete:
            print(draft.id, draft.start_time)
        drafts_to_delete.delete()


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
    else:
        return None


def guess_conference(name):
    if "CFFC" in name:
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
    elif "ConfL" in name or "Conference" in name:
        return 3
    elif "DivL" in name or "Divisionsliga" in name:
        return 4
    elif "RL" in name or "Regionalliga" in name:
        return 5
    else:
        return 6


def update_or_create_draft(league_id, draft_data):
    start_time = draft_data.get('start_time')
    if start_time:
        start_time = datetime.fromtimestamp(start_time / 1000, tz=timezone('Europe/Berlin'))

    last_picked = draft_data.get('last_picked')
    if last_picked:
        last_picked = datetime.fromtimestamp(last_picked / 1000, tz=timezone('Europe/Berlin'))

    last_message_time = draft_data.get('last_message_time')
    if last_message_time:
        last_message_time = datetime.fromtimestamp(last_message_time / 1000, tz=timezone('Europe/Berlin'))

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
            "last_picked": last_picked,
            "last_message_time": last_message_time,
            "last_message_id": draft_data.get('last_message_id'),
            "draft_order": draft_data.get('draft_order')
        }
    )

    draft.save()
    return draft


def get_draft_data(league_id):
    league_service = sleeper_wrapper.League(league_id)
    response = league_service.get_all_drafts()
    if isinstance(response, requests.exceptions.HTTPError):
        print(f"Error for league {league_id}")
        return []

    return response



def update_drafts_for_league(league_id):
    drafts_data = get_draft_data(league_id)

    latest_draft_data = max(drafts_data, key=lambda d: d.get('start_time'))
    draft = update_or_create_draft(league_id, latest_draft_data)
    delete_old_drafts(league_id, draft.draft_id)

    return draft


def update_or_create_pick(draft_id, pick_data):
    try:
        draft = Draft.objects.get(draft_id=draft_id)
        pick, _ = Pick.objects.update_or_create(
            draft=draft,
            pick_no=pick_data.get('pick_no'),
            defaults={
                "player": Player.objects.get(sleeper_id=pick_data.get('player_id')),
                "owner": DSTPlayer.objects.get(sleeper_id=pick_data.get('picked_by')),
                "roster": Roster.objects.get(roster_id=pick_data.get('roster_id'),
                                             owner__sleeper_id=pick_data.get('picked_by'),
                                             league=draft.league),
                "round": pick_data.get('round', 1),
                "draft_slot": pick_data.get('draft_slot', 1),
                "metadata": pick_data.get('metadata', {})
            }
        )
        pick.save()
        return pick

    except Roster.DoesNotExist as e:
        print("Draft: ", draft_id, "Roster: ", pick_data.get('roster_id'), "Picked by: ", pick_data.get('picked_by'))

    except DSTPlayer.DoesNotExist as e:
        print("Draft: ", draft_id, "Roster: ", pick_data.get('roster_id'), "Picked by: ", pick_data.get('picked_by'))


def get_pick_data(draft_id):
    draft_service = sleeper_wrapper.Drafts(draft_id)
    return draft_service.get_all_picks()


def update_picks_for_draft(draft_id, picks_data):
    picks = []
    for pick in picks_data:
        picks.append(update_or_create_pick(draft_id, pick))

    update_player_draft_stats_from_picks(Season.get_active())

    return picks


def update_draft_stats():
    # Alle Picks mit mindestens 5 Picks je Spieler, sortiert nach Differenz zwischen adp und pick_no
    # Relevante Spieler:
    relevant_players = Pick.objects.all().values('player__id').annotate(pick_count=Count('player__id')).filter(
        pick_count__gte=5).values_list('player_id', flat=True)
    relevant_picks = Pick.objects.filter(player__id__in=relevant_players)
    for pick in relevant_picks.annotate(adp=Avg('pick_no')):
        pass


def update_everything():
    update_players()
    update_leagues()
    update_drafts()


def update_leagues():
    for league in League.objects.get_active():
        print("Updating League {league}".format(league=league.sleeper_name))
        try:
            league_data = get_league_data(league.sleeper_id)
            update_league(league, league_data)

            dst_player_data = get_dst_player_data(league.sleeper_id)
            update_dst_players_for_league(league.sleeper_id, dst_player_data)

            roster_data = get_roster_data(league.sleeper_id)
            update_rosters_for_league(league.sleeper_id, roster_data, dst_player_data)

        except AttributeError as e:
            print(league.id, e)


def update_drafts():
    for league in League.objects.get_active():
        draft = update_drafts_for_league(league.sleeper_id)

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
        "height": player_data.get("height"),
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


def update_listener_league():
    listener_league_id = League.objects.get_active().get(type=League.LISTENER).sleeper_id
    league_data = get_league_data(listener_league_id)
    try:
        ls = LeagueSetting(id=listener_league_id,
                           name="DST Hörerliga",
                           level=99,
                           conference=None,
                           region=None)
        update_or_create_league(ls, league_data)
        dst_player_data = get_dst_player_data(listener_league_id)
        update_dst_players_for_league(listener_league_id, dst_player_data)

        roster_data = get_roster_data(listener_league_id)
        update_rosters_for_league(listener_league_id, roster_data, dst_player_data)

        week = get_current_week()
        update_matchup_for_league(listener_league_id, week)
    except AttributeError as e:
        print(listener_league_id, league_data.response)


def update_listener_draft():
    listener_league_id = League.objects.get_active().get(type=League.LISTENER).sleeper_id
    draft = update_drafts_for_league(listener_league_id)

    picks_data = get_pick_data(draft.draft_id)
    update_picks_for_draft(draft.draft_id, picks_data)


def update_matchups():
    week = get_current_week()
    print("Updating Matchups for week {week}".format(week=week))
    for league in League.objects.get_active():
        update_matchup_for_league(league.sleeper_id, week)
    print("All done!")


def update_matchup_for_league(league_id, week):
    matchups = {}
    league_service = sleeper_wrapper.League(league_id)
    matchup_data_list = league_service.get_matchups(week)
    for matchup_data in matchup_data_list:
        matchup_id = matchup_data.get("matchup_id")
        matchup = matchups.get(matchup_id)
        if not matchup:
            matchups[matchup_id] = {
                'one': matchup_data
            }
        else:
            matchups[matchup_id].update({
                'two': matchup_data
            })
    for id, data in matchups.items():
        Matchup.objects.update_or_create(
            league_id=league_id,
            week=week,
            matchup_id=id,
            defaults={
                "roster_id_one": data.get("one").get("roster_id"),
                "starters_one": ",".join(data.get("one").get("starters") or []),
                "players_one": ",".join(data.get("one").get("players") or []),
                "points_one": data.get("one").get("points") or 0,
                "roster_id_two": data.get("two").get("roster_id"),
                "starters_two": ",".join(data.get("two").get("starters") or []),
                "players_two": ",".join(data.get("two").get("players") or []),
                "points_two": data.get("two").get("points") or 0
            })


def update_playoffs():
    week = get_current_week()
    print("Updating Playoffs")
    for league in League.objects.get_active():
        update_playoffs_for_league(league.sleeper_id)
    print("All done!")


def update_playoffs_for_league(league_id):
    league_service = sleeper_wrapper.League(league_id)
    winner_bracket = league_service.get_playoff_winners_bracket()
    losers_bracket = league_service.get_playoff_losers_bracket()
    for matchup in winner_bracket:
        create_playoff_matchup(league_id, matchup, "Playoffs")

    for matchup in losers_bracket:
        create_playoff_matchup(league_id, matchup, "Toilet Bowl")


def create_playoff_matchup(league_id, matchup, bracket):
    PlayoffMatchup.objects.update_or_create(
        bracket=bracket,
        league_id=league_id,
        round=matchup.get("r"),
        matchup_id=matchup.get("m"),
        defaults={
            "roster_id_one": matchup.get("t1"),
            "roster_id_two": matchup.get("t2"),
            "winner": matchup.get("w"),
            "loser": matchup.get("l"),
            "rank": matchup.get("p")
        }
    )


def get_current_week():
    return StateService().get_current_week()


def update_stats_for_position(position, week):
    print("Updating Stats for Position {position} in week {week}".format(position=position, week=week))

    season_type = "regular"
    season = StateService().get_season()
    stats_service = StatsService()
    position_stats = stats_service.get_week_stats(season_type, season, position, week)

    for stats in position_stats:
        player_id = stats.get("player_id")
        try:
            player = Player.objects.get(sleeper_id=player_id)
            player_stats = stats.get("stats") or {}
            points = player_stats.get("pts_half_ppr") or 0
            season_object = Season.get_active()
            stats, created = StatsWeek.objects.update_or_create(
                week=week,
                season_type=season_type,
                season=season_object,
                player=player,
                defaults={
                    "points": points,
                    "stats": player_stats
                }
            )
            if not created:
                stats.points = points
                stats.stats = player_stats
                stats.save()

        except Player.DoesNotExist:
            print("Could not update Stats for unknown Player {player_id}".format(player_id=player_id))

    print("All done!")


def update_projections_for_position(position, week):
    print("Updating Projections for Position {position} in week {week}".format(position=position, week=week))

    season_type = "regular"
    season = StateService().get_season()
    stats_service = StatsService()
    position_stats = stats_service.get_week_projections(season_type, season, position, week)

    for stats in position_stats:
        player_id = stats.get("player_id")
        try:
            player = Player.objects.get(sleeper_id=player_id)
            player_projected_stats = stats.get("stats") or {}
            season_object = Season.get_active()
            projected_points = player_projected_stats.get("pts_half_ppr") or 0
            stats, created = StatsWeek.objects.update_or_create(
                week=week,
                season_type=season_type,
                season=season_object,
                player=player,
                defaults={
                    "projected_points": projected_points,
                    "projected_stats": player_projected_stats
                }
            )
            if not created:
                stats.projected_points = projected_points
                stats.player_projected_stats = player_projected_stats
                stats.save()

        except Player.DoesNotExist:
            print("Could not update Projections for unknown Player {player_id}".format(player_id=player_id))

    print("All done!")


def update_stats():
    week = get_current_week()
    for pos in POSITIONS:
        update_stats_for_position(pos, week)
        update_projections_for_position(pos, week)


def update_stats_for_weeks(weeks=None):
    if not weeks:
        weeks = []
    for week in weeks:
        for pos in POSITIONS:
            update_stats_for_position(pos, week)
            update_projections_for_position(pos, week)


def update_player_draft_stats_from_picks(season: Season):
    player_map = {}
    for pick in Pick.objects.filter(roster__league__season=season):
        player_stats = player_map.get(pick.player.sleeper_id, {})
        player_stats['name'] = pick.player.first_name + pick.player.last_name
        player_stats['team'] = pick.player.team.abbr if pick.player.team else '-'
        player_stats['position'] = pick.player.position
        player_stats['picked_positions'] = player_stats.get('picked_positions', []) + [pick.pick_no]
        player_map[pick.player.sleeper_id] = player_stats

    for player_id, player_stats in player_map.items():
        PlayerDraftStats.objects.update_or_create(season=season, player_id=player_id, defaults={
            'player_name': player_stats['name'],
            'player_team': player_stats['team'],
            'player_position': player_stats['position'],
            'pick_count': len(player_stats['picked_positions']),
            'adp': sum(player_stats['picked_positions']) / len(player_stats['picked_positions']),
            'highest_pick': min(player_stats['picked_positions']),
            'lowest_pick': max(player_stats['picked_positions'])
        })


def update_trades(week=None):
    for league in League.objects.filter(season=Season.get_active()):
        print("Updating trades for {league}.".format(league=league))
        update_trades_for_league(league.sleeper_id, week)


def update_trades_for_league(league_id, week=None):
    if not week:
        week = get_current_week()

    league_service = sleeper_wrapper.League(league_id)
    trades = league_service.get_transactions(week)
    for trade in trades:
        if trade.get('type') == 'waiver':
            roster = Roster.objects.get(league__sleeper_id=league_id, roster_id=trade.get('roster_ids')[0])
            status = trade.get('status')
            bid = trade.get('settings', {}).get('waiver_bid', 0)
            player = Player.objects.get(sleeper_id=next(iter(trade.get('adds'))))
            changed_ts = datetime.fromtimestamp(trade.get('status_updated') / 1000, tz=timezone('Europe/Berlin'))
            WaiverPickup.objects.update_or_create(season=Season.get_active(), week=week, roster=roster, player=player, defaults={
                'status': status,
                'bid': bid,
                'changed_ts': changed_ts
            })


class StatsService(BaseApi):
    def __init__(self):
        self._base_stats_url = "https://api.sleeper.app/stats/{}".format("nfl")
        self._base_projections_url = "https://api.sleeper.app/projections/{}".format("nfl")

    def get_all_stats(self, season_type, season, position):
        return self._call(
            "{base_url}/{season}?season_type={season_type}&position[]={positionorder_by=pts_half_ppr".format(
                base_url=self._base_stats_url, season=season, season_type=season_type, position=position))

    def get_week_stats(self, season_type, season, position, week):
        return self._call(
            "{base_url}/{season}/{week}?season_type={season_type}&position[]={position}&order_by=pts_half_ppr".format(
                base_url=self._base_stats_url, season=season, season_type=season_type, position=position, week=week))

    def get_all_projections(self, season_type, season, position):
        return self._call(
            "{base_url}/{season}?season_type={season_type}&position[]={positionorder_by=pts_half_ppr".format(
                base_url=self._base_projections_url, season=season, season_type=season_type, position=position))

    def get_week_projections(self, season_type, season, position, week):
        return self._call(
            "{base_url}/{season}/{week}?season_type={season_type}&position[]={position}&order_by=pts_half_ppr".format(
                base_url=self._base_projections_url, season=season, season_type=season_type, position=position,
                week=week))


