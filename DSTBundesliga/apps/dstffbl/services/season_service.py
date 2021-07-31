import csv
from smtplib import SMTPException

import sleeper_wrapper
from django.contrib.auth.models import User
from django.core.mail import send_mail

from DSTBundesliga.apps.dstffbl.models import SeasonUser, SeasonInvitation
from DSTBundesliga.apps.leagues.models import DSTPlayer, League, Season


import logging


def get_last_years_league(player: DSTPlayer):
    try:
        return League.objects.filter(id__in=[r.league.id for r in player.roster_set.all()]).get(type=League.BUNDESLIGA)
    except League.DoesNotExist:
        return None


def update_last_years_leagues():
    for su in SeasonUser.objects.filter(season=Season.get_active(), last_years_league=None):
        try:
            dst_player = DSTPlayer.objects.get(sleeper_id=su.sleeper_id)
            su.last_years_league = get_last_years_league(dst_player)
            if su.last_years_league:
                su.new_player = False
        except DSTPlayer.DoesNotExist:
            su.last_years_league = None
            su.new_player = True
            pass

        su.save()


def create_season_users(users):
    for user_tuple in users:
        last_years_league = None
        new_player = True

        email, sleeper_username, commish, region = user_tuple
        sleeper_user = sleeper_wrapper.User(sleeper_username)

        sleeper_id = sleeper_user.get_user_id()
        try:
            dst_player = DSTPlayer.objects.get(sleeper_id=sleeper_id)
            if dst_player:
                last_years_league = get_last_years_league(player=dst_player)
                new_player = False
        except DSTPlayer.DoesNotExist:
            dst_player, _ = DSTPlayer.objects.update_or_create(sleeper_id=sleeper_id, defaults={
                "display_name": sleeper_username
            })

        dummy_user, _ = User.objects.get_or_create(username=email, email=email)

        SeasonUser.objects.get_or_create(
            user=dummy_user,
            dst_player=dst_player,
            season=Season.get_active(),
            sleeper_id=sleeper_id,
            new_player=new_player,
            last_years_league=last_years_league,
            region=region,
            possible_commish=commish
        )

        DSTPlayer.objects.update_or_create(sleeper_id=sleeper_id, defaults={
            "display_name": sleeper_username
        })


def send_invitation_chunk(chunk_size=12):
    open_invitations = SeasonInvitation.objects.filter(send_ts=None).order_by('sleeper_league_id')[:chunk_size]
    for invitation in open_invitations:
        success = invitation.send_invitation()
        if success:
            print("Invitation send to {sleeper_name} for league {sleeper_league_id} - {sleeper_league_name}".format(
                sleeper_name=invitation.sleeper_username,
                sleeper_league_id=invitation.sleeper_league_id,
                sleeper_league_name=invitation.sleeper_league_name
            ))


def import_invitations(filepath):
    with open(filepath, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        for row in csv_reader:
            league_id = row.get("Liga-ID")
            league_name = row.get("Liga-Name")
            league_link = row.get("Einladungslink")

            players = [
                row.get("Teilnehmer1"),
                row.get("Teilnehmer2"),
                row.get("Teilnehmer3"),
                row.get("Teilnehmer4"),
                row.get("Teilnehmer5"),
                row.get("Teilnehmer6"),
                row.get("Teilnehmer7"),
                row.get("Teilnehmer8"),
                row.get("Teilnehmer9"),
                row.get("Teilnehmer10"),
                row.get("Teilnehmer11"),
                row.get("Teilnehmer12")
            ]

            if not all(players):
                print(f"League {league_id} - {league_name} incomplete!".format(league_id=league_id, league_name=league_name))
            else:
                print("Creating Invitations for league {league_id} - {league_name}".format(league_id=league_id, league_name=league_name))
                counter = 0
                for player in players:
                    try:
                        su, created = SeasonInvitation.objects.get_or_create(
                            season_user=SeasonUser.objects.get(dst_player__display_name=player),
                            sleeper_username=player,
                            sleeper_league_name=league_name,
                            sleeper_league_id=league_id,
                            sleeper_league_link=league_link
                        )
                        if created:
                            counter += 1
                    except SeasonUser.DoesNotExist:
                        print("SeasonUser for Sleeper-Name {sleeper_name} does not exist!".format(sleeper_name=player))

                print("Created {count} Invitations".format(count=counter))

        print("All done! There are now {count} open invitations".format(SeasonInvitation.objects.filter(send_ts=None).count()))
