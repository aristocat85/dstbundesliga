import csv

import sleeper_wrapper
from django.contrib.auth.models import User

from DSTBundesliga.apps.dstffbl.models import SeasonUser, SeasonInvitation, SeasonRegistration, DSTEmail
from DSTBundesliga.apps.leagues.models import DSTPlayer, League, Season
from DSTBundesliga.apps.services.data_services import LeagueSetting, guess_level, guess_conference, guess_region, \
    update_or_create_league, get_league_data

EMAIL_SUBJECT = 'Anmeldung erfolgreich!'

EMAIL_TEXT = ''''
    Hallo {sleeper_name},
    
    Du bist für die Saison {current_season} angemeldet! Weitere Infos folgen in einigen Tagen per Mail und über unsere 
    Social Media Seiten.
    
    Beste Grüße von
    Michael und dem gesamten Organisationsteam der DSTFanFooBL
    '''

EMAIL_HTML = '''
    <p>Hallo {sleeper_name},</p>
    
    <p>Du bist für die Saison {current_season} angemeldet! Weitere Infos folgen in einigen Tagen per Mail und über 
    unsere Social Media Seiten.</p>
    
    <p>Beste Grüße von<br>
    Michael und dem gesamten Organisationsteam der DSTFanFooBL</p>
    '''


def get_last_years_league(player: DSTPlayer):
    try:
        return League.objects.filter(season=Season.get_last(),
                                     id__in=[r.league.id for r in player.roster_set.all()]).get(type=League.BUNDESLIGA)
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

        sr, _ = SeasonRegistration.objects.get_or_create(
            user=dummy_user,
            dst_player=dst_player,
            season=Season.get_active(),
            sleeper_id=sleeper_id,
            new_player=new_player,
            last_years_league=last_years_league,
            region=region,
            possible_commish=commish
        )

        su, _ = SeasonUser.objects.get_or_create(
            user=dummy_user,
            registration=sr,
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

        DSTEmail.objects.create(
            recipient=su.user.email,
            subject=EMAIL_SUBJECT,
            text=EMAIL_TEXT.format(
                sleeper_name=su.dst_player.display_name,
                current_season=su.season
            ),
            html=EMAIL_HTML.format(
                sleeper_name=su.dst_player.display_name,
                current_season=su.season
            ),
            type=2
        )


def send_email_chunk(chunk_size=12):
    open_mails = DSTEmail.objects.filter(send_ts=None)[:chunk_size]
    for mail in open_mails:
        success = mail.send_mail()
        if success:
            print("{type} send to {email}".format(
                type=mail.type,
                email=mail.recipient
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
                print(f"League {league_id} - {league_name} incomplete!".format(league_id=league_id,
                                                                               league_name=league_name))
            else:
                print("Creating Invitations for league {league_id} - {league_name}".format(league_id=league_id,
                                                                                           league_name=league_name))
                counter = 0
                for player in players:
                    try:
                        su, created = SeasonInvitation.objects.get_or_create(
                            season_user=SeasonUser.objects.get(dst_player__display_name=player,
                                                               season=Season.get_active()),
                            sleeper_username=player,
                            sleeper_league_name=league_name,
                            sleeper_league_id=league_id,
                            sleeper_league_link=league_link
                        )
                        if created:
                            su.create_mail()
                            counter += 1
                    except SeasonUser.DoesNotExist:
                        print("SeasonUser for Sleeper-Name {sleeper_name} does not exist!".format(sleeper_name=player))

                print("Created {count} Invitations".format(count=counter))

        print("All done!")


def create_leagues_from_invitations():
    for si in SeasonInvitation.objects.filter(season_user__season=Season.get_active()):
        league_settings = LeagueSetting(
            id=si.sleeper_league_id,
            name=si.sleeper_league_name,
            level=guess_level(si.sleeper_league_name),
            conference=guess_conference(si.sleeper_league_name),
            region=guess_region(si.sleeper_league_name)
        )

        league_data = get_league_data(si.sleeper_league_id)

        update_or_create_league(league_settings, league_data)
