import csv
import datetime
import time

import sleeper_wrapper
from django.contrib.auth.models import User
from django.db.models import Window, F
from django.db.models.functions import RowNumber
from django.core.mail import get_connection
from django.utils import timezone
from django.core.mail.message import EmailMultiAlternatives

from DSTBundesliga.apps.dstffbl.models import (
    SeasonUser,
    SeasonInvitation,
    SeasonRegistration,
    DSTEmail,
)
from DSTBundesliga.apps.leagues.models import DSTPlayer, League, Season
from DSTBundesliga.apps.services.data_services import (
    LeagueSetting,
    guess_level,
    guess_conference,
    guess_region,
    update_or_create_league,
    get_league_data,
)

EMAIL_SUBJECT = "Anmeldung erfolgreich!"

EMAIL_TEXT = """'
    Hallo {sleeper_name},
    
    Du bist für die Saison {current_season} angemeldet! 
    Die Einladungen zu den Ligen werden spätestens ab dem 24.08. versendet. Bitte melde dich bei uns unter probleme@fantasybundesliga.de falls du bis zum 26.8. um 10 Uhr keine Einladung erhalten hast.
    
    Beste Grüße von
    Michael und dem gesamten Organisationsteam der DSTFanFooBL
    """

EMAIL_HTML = """
    <p>Hallo {sleeper_name},</p>
    
    <p>Du bist für die Saison {current_season} angemeldet!</p>
    <p>Die Einladungen zu den Ligen werden spätestens ab dem 24.08. versendet. Bitte melde dich bei uns unter probleme@fantasybundesliga.de falls du bis zum 26.8. um 10 Uhr keine Einladung erhalten hast.</p>
    
    <p>Beste Grüße von<br>
    Michael und dem gesamten Organisationsteam der DSTFanFooBL</p>
    """


def get_last_years_league(player: DSTPlayer):
    try:
        return League.objects.filter(
            season=Season.get_last(),
            id__in=[r.league.id for r in player.roster_set.all()],
        ).get(type=League.BUNDESLIGA)
    except League.DoesNotExist:
        return None


def update_last_years_leagues():
    for su in SeasonUser.objects.filter(
        season=Season.get_active(), last_years_league=None
    ):
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
        print(f"Creating season user for {email}...")


        sleeper_user = sleeper_wrapper.User(sleeper_username)

        sleeper_id = sleeper_user.get_user_id()
        try:
            dst_player = DSTPlayer.objects.get(sleeper_id=sleeper_id)
            if dst_player:
                last_years_league = get_last_years_league(player=dst_player)
                new_player = False
        except DSTPlayer.DoesNotExist:
            dst_player, _ = DSTPlayer.objects.update_or_create(
                sleeper_id=sleeper_id, defaults={"display_name": sleeper_username}
            )

        dummy_user, _ = User.objects.get_or_create(username=email, email=email)

        sr, _ = SeasonRegistration.objects.get_or_create(
            user=dummy_user,
            dst_player=dst_player,
            season=Season.get_active(),
            sleeper_id=sleeper_id,
            new_player=new_player,
            last_years_league=last_years_league,
            region=region,
            possible_commish=commish,
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
            possible_commish=commish,
        )

        DSTPlayer.objects.update_or_create(
            sleeper_id=sleeper_id, defaults={"display_name": sleeper_username}
        )

        DSTEmail.objects.create(
            recipient=su.user.email,
            subject=EMAIL_SUBJECT,
            text=EMAIL_TEXT.format(
                sleeper_name=su.dst_player.display_name, current_season=su.season
            ),
            html=EMAIL_HTML.format(
                sleeper_name=su.dst_player.display_name, current_season=su.season
            ),
            type=2,
        )

        print("...done!")


# Rate limit is 60/h
def send_email_chunk(batch_size=200):
    open_mails = list(DSTEmail.objects.filter(send_ts=None))[:batch_size]
    total_open_mails = len(open_mails)
    print(f"Insgesamt zu versendende E-Mails: {total_open_mails}\n")

    connection = get_connection(fail_silently=False)
    total_sent = 0
    has_error = False
    error_message = None

    mails = []
    send_mails = []

    # ---------------------------------------------------------
    # 3. Batch-Versand mit Fehlerabfangung
    # ---------------------------------------------------------
    for m in open_mails:
        mail = EmailMultiAlternatives(
            m.subject, m.text, None, [m.recipient], connection=connection
        )
        mail.attach_alternative(m.html, "text/html")

        mails.append(mail)
        send_mails.append(m)

        try:
            send_mail_batch(mails, send_mails)
            total_sent += len(mails)

            remaining = total_open_mails - total_sent
            print(
                f"[Batch Erfolgreich] Versendet: {total_sent}/{total_open_mails} | "
                f"Noch nicht versendet: {remaining}"
            )

            mails = []
            send_mails = []
            time.sleep(60)

        except Exception as e:
            has_error = True
            error_message = str(e)
            print(f"\n[FEHLER] Fehler beim Senden des Batches: {e}")
            print("Versand wird abgebrochen...\n")
            break

    # ---------------------------------------------------------
    # 4. Zusammenfassung des Status
    # ---------------------------------------------------------
    remaining_unsent = total_open_mails - total_sent

    print("\n" + "=" * 45)
    print("             ZUSAMMENFASSUNG STATUS             ")
    print("=" * 45)
    print(f"Zu Beginn offene Mails gesamt:   {total_open_mails}")
    print(f"Erfolgreich versendet:           {total_sent}")
    print(f"Verblieben (nicht versendet):    {remaining_unsent}")
    print(
        f"Endstatus:                       "
        f"{'ABGEBROCHEN (Fehler)' if has_error else 'ERFOLGREICH ABGESCHLOSSEN'}"
    )
    if has_error:
        print(f"Fehlermeldung:                   {error_message}")
    print("=" * 45)
    open_mails = DSTEmail.objects.filter(send_ts=None)[:batch_size]
    send_mail_batch(open_mails)


def send_mail_batch(mails_to_send, db_objects):
    """Hilfsfunktion zum Senden und Aktualisieren der DB-Einträge."""
    connection = get_connection(fail_silently=False)
    connection.send_messages(mails_to_send)
    now = timezone.now()
    for sm in db_objects:
        sm.send_ts = now
        sm.save()


def resend_error_email_chunk():
    # 1. Fehlerhafte Mails zu Beginn ermitteln und ausgeben
    invalid_emails = DSTEmail.objects.filter(has_erros=True, send_ts__gte=datetime.date(year=2026, month=8, day=6))
    print(f"Anzahl fehlerhafter E-Mails zu Beginn: {len(invalid_emails)}\n")
    
    for m in invalid_emails:
        m.send_ts=None  
        m.has_erros=False   
        m.error_message=""  
        m.save()

def import_invitations(filepath):
    with open(filepath, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=";")
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
                row.get("Teilnehmer12"),
            ]

            if not all(players):
                print(
                    f"League {league_id} - {league_name} incomplete!".format(
                        league_id=league_id, league_name=league_name
                    )
                )
            else:
                print(
                    "Creating Invitations for league {league_id} - {league_name}".format(
                        league_id=league_id, league_name=league_name
                    )
                )
                counter = 0
                for player in players:
                    try:
                        su, created = SeasonInvitation.objects.get_or_create(
                            season_user=SeasonUser.objects.get(
                                dst_player__display_name=player,
                                season=Season.get_active(),
                            ),
                            sleeper_username=player,
                            sleeper_league_name=league_name,
                            sleeper_league_id=league_id,
                            sleeper_league_link=league_link,
                        )
                        if created:
                            su.create_mail()
                            counter += 1
                    except SeasonUser.DoesNotExist:
                        print(
                            "SeasonUser for Sleeper-Name {sleeper_name} does not exist!".format(
                                sleeper_name=player
                            )
                        )

                print("Created {count} Invitations".format(count=counter))

        print("All done!")


def create_leagues_from_invitations():
    for si in SeasonInvitation.objects.filter(season_user__season=Season.get_active()):
        league_settings = LeagueSetting(
            id=si.sleeper_league_id,
            name=si.sleeper_league_name,
            level=guess_level(si.sleeper_league_name),
            conference=guess_conference(si.sleeper_league_name),
            region=guess_region(si.sleeper_league_name),
            type=League.BUNDESLIGA,
        )

        league_data = get_league_data(si.sleeper_league_id)

        update_or_create_league(league_settings, league_data)


def get_waiting_list():
    return (
        SeasonUser.objects.exclude(
            id__in=SeasonInvitation.objects.values_list("season_user", flat=True)
        )
        .filter(season=Season.get_active())
        .order_by("registration__registration_ts", "sleeper_id")
    )
