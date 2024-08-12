import logging
import datetime
import uuid

from django.urls import reverse
from loguru import logger
from smtplib import SMTPException
from tinymce.models import HTMLField
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone

from DSTBundesliga.apps.leagues.models import (
    Season,
    DSTPlayer,
    League,
    Roster,
    FinalSeasonStanding,
)
from DSTBundesliga.apps.services.state_service import StateService

state_service = StateService()


EMAIL_TYPES = (
    (1, "CONFIRM_REGISTRATION"),
    (2, "REGISTRATION_SUCCESSFUL"),
    (3, "LEAGUE_INVITATION"),
    (4, "PATREON_REQUEST")
)

REGIONS = (
    (
        1,
        "Nord (Niedersachsen, Bremen, Hamburg, Mecklenburg-Vorpommern , Schleswig-Holstein)",
    ),
    (2, "Ost (Thüringen, Berlin, Sachsen, Sachsen-Anhalt, Brandenburg)"),
    (3, "Süd (Bayern, Baden-Württemberg)"),
    (4, "West (Nordrhein-Westfalen, Hessen, Saarland, Rheinland-Pfalz)"),
)


class DSTEmail(models.Model):
    type = models.IntegerField(choices=EMAIL_TYPES)
    recipient = models.EmailField()
    subject = models.CharField(max_length=998)
    text = models.TextField()
    html = models.TextField()
    send_ts = models.DateTimeField(null=True)
    has_erros = models.BooleanField(default=False)
    error_message = models.CharField(max_length=500)

    def send_mail(self):
        success = False

        self.has_erros = False
        self.error_message = ""
        try:
            print("Sending Mail to {mail}".format(mail=self.recipient))
            send_mail(
                self.subject,
                self.text,
                None,
                [self.recipient],
                False,
                None,
                None,
                None,
                self.html,
            )
            success = True

        except SMTPException as e:
            self.has_erros = True
            self.error_message = str(e)

            logging.exception(self.error_message, exc_info=e)

        except models.ObjectDoesNotExist as e:
            self.has_erros = True
            self.error_message = "No Email for this User!"

            logging.exception(self.error_message, exc_info=e)

        except Exception as e:
            self.has_erros = True
            self.error_message = str(e)

            logging.exception(self.error_message, exc_info=e)

        finally:
            self.send_ts = timezone.now()
            self.save()

        return success


class EmailCreationMixin:
    def get_email_to(self):
        pass

    def get_email_subject(self):
        pass

    def get_email_text(self):
        pass

    def get_email_html(self):
        pass

    def create_mail(self):
        DSTEmail.objects.create(
            recipient=self.get_email_to(),
            subject=self.get_email_subject(),
            text=self.get_email_text(),
            html=self.get_email_html(),
            type=self.get_email_type(),
        )


class SeasonRegistration(models.Model, EmailCreationMixin):
    EMAIL_SUBJECT = "Bitte bestätige deine Anmmeldung zur Down, Set, Talk! Fantasy Football Bundesliga {current_season}"

    EMAIL_TEXT = """'
    Hallo {sleeper_name},

    bitte bestätige deine Anmeldung zur Saison {current_season}, indem du den folgenden Link aufrufst:
    {confirm_link}

    Beste Grüße von
    Michael und dem gesamten Organisationsteam der DSTFanFooBL
    """

    EMAIL_HTML = """
    <p>Hallo {sleeper_name},</p>

    <p>bitte bestätige deine Anmeldung zur Saison {current_season}, indem du den folgenden Link aufrufst:</p>

    <p><a href="{confirm_link}">{confirm_link}</a></p>

    <p>Beste Grüße von<br>
    Michael und dem gesamten Organisationsteam der DSTFanFooBL</p>
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dst_player = models.ForeignKey(DSTPlayer, on_delete=models.CASCADE, null=True)
    season = models.ForeignKey(
        Season, on_delete=models.DO_NOTHING, default=Season.get_active
    )
    sleeper_id = models.CharField(max_length=50)
    region = models.IntegerField(choices=REGIONS)
    new_player = models.BooleanField(default=False)
    last_years_league = models.ForeignKey(League, null=True, on_delete=models.SET_NULL)
    possible_commish = models.BooleanField(default=False)
    registration_ts = models.DateTimeField(auto_now_add=True)

    def email(self):
        return self.user.email

    def get_email_subject(self):
        return self.EMAIL_SUBJECT.format(current_season=Season.get_active())

    def get_confirm_link(self):
        return "https://www.fantasybundesliga.de" + reverse(
            "dstffbl:accept_invite", kwargs={"registration_id": self.id}
        )

    def get_email_text(self):
        return self.EMAIL_TEXT.format(
            current_season=state_service.get_season(),
            sleeper_name=self.dst_player.display_name,
            confirm_link=self.get_confirm_link(),
        )

    def get_email_html(self):
        return self.EMAIL_HTML.format(
            current_season=state_service.get_season(),
            sleeper_name=self.dst_player.display_name,
            confirm_link=self.get_confirm_link(),
        )

    def get_email_to(self):
        return self.user.email

    def get_email_type(self):
        return 1

    @property
    def url(self):
        return reverse("dstffbl:accept_invite", kwargs={"registration_id": self.id})


class SeasonUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dst_player = models.ForeignKey(DSTPlayer, on_delete=models.CASCADE, null=True)
    registration = models.ForeignKey(
        SeasonRegistration, on_delete=models.CASCADE, null=True
    )
    season = models.ForeignKey(
        Season, on_delete=models.DO_NOTHING, default=Season.get_active
    )
    sleeper_id = models.CharField(max_length=50)
    region = models.IntegerField(choices=REGIONS)
    new_player = models.BooleanField(default=False)
    last_years_league = models.ForeignKey(League, null=True, on_delete=models.SET_NULL)
    possible_commish = models.BooleanField(default=False)
    confirm_ts = models.DateTimeField(auto_now_add=True, null=True)

    def email(self):
        return self.user.email

    def get_last_season_roster(self):
        try:
            return Roster.objects.get(season=Season.get_last(), owner=self.dst_player)
        except Roster.DoesNotExist:
            return None

    def get_last_season_standing(self):
        try:
            FinalSeasonStanding.objects.get(roster=self.get_last_season_roster())
        except FinalSeasonStanding.DoesNotExist:
            return None


class SeasonInvitation(models.Model, EmailCreationMixin):
    EMAIL_SUBJECT = "Deine Einladung zur Down, Set, Talk! Fantasy Football Bundesliga {current_season}"

    EMAIL_TEXT = """'
    Hallo {sleeper_name},

    wir freuen uns sehr, dass du dich für die Saison {season} der Down, Set, Talk! Fantasy Football Bundesliga angemeldet hast. Jetzt dürfen wir dich in deine Liga einladen.

    Du wirst in der <b>{league_name}</b> spielen.
    In deine Liga kommst du über diesen Link: {league_link}

    Weitere Informationen findest du als angepinnte Nachricht in deiner Liga.
    Bitte beachte, dass du die Einladung in deine Liga bis zum 20. August 2022 um 24:00 Uhr angenommen haben musst. Ansonsten müssen wir deinen Platz leider an eine(n) andere(n) Mitspieler(in) vergeben. Da wir aber davon ausgehen, dass dies nicht erfolgen muss, wünschen wir dir viel Erfolg und vor allem Spaß in der kommenden Fantasy-Saison.

    Beste Grüße von
    Michael und dem gesamten Organisationsteam der DSTFanFooBL

    PS: Bei Fragen kannst du dich jederzeit gerne an uns wenden. Du findest uns bei Twitter und Instagram unter @dstfanfoobl. Hört auch gerne mal in unseren Podcast zur DSTFanFooBL rein: https://anchor.fm/dstfanfoobl
    """

    EMAIL_HTML = """
    <p>Hallo {sleeper_name},</p>

    <p>wir freuen uns sehr, dass du dich für die Saison {season} der Down, Set, Talk! Fantasy Football Bundesliga angemeldet hast. Jetzt dürfen wir dich in deine Liga einladen.</p>

    <p>Du wirst in der <b>{league_name}</b> spielen.
    In deine Liga kommst du über diesen Link: <a href="{league_link}">{league_link}</a></p>

    <p>Weitere Informationen findest du als angepinnte Nachricht in deiner Liga.
    Bitte beachte, dass du die Einladung in deine Liga bis zum <b>20. August 2022 um 24:00 Uhr</b> angenommen haben musst. Ansonsten müssen wir deinen Platz leider an eine(n) andere(n) Mitspieler(in) vergeben. Da wir aber davon ausgehen, dass dies nicht erfolgen muss, wünschen wir dir viel Erfolg und vor allem Spaß in der kommenden Fantasy-Saison.</p>

    <p>Beste Grüße von<br>
    Michael und dem gesamten Organisationsteam der DSTFanFooBL</p>

    <br>
    <p>PS: Bei Fragen kannst du dich jederzeit gerne an uns wenden. Du findest uns bei <a href="https://twitter.com/dstfanfoobl">Twitter</a> und <a href="https://www.instagram.com/dstfanfoobl/">Instagram</a> unter @dstfanfoobl. Hör auch gerne mal in unseren <a href="https://anchor.fm/dstfanfoobl">Podcast zur DSTFanFooBL</a> rein!</p>
    """

    season_user = models.ForeignKey(SeasonUser, on_delete=models.SET_NULL, null=True)
    sleeper_username = models.CharField(max_length=50)
    sleeper_league_name = models.CharField(max_length=100)
    sleeper_league_id = models.CharField(max_length=50)
    sleeper_league_link = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now=True)

    def get_email_subject(self):
        return self.EMAIL_SUBJECT.format(current_season=Season.get_active())

    def get_email_text(self):
        return self.EMAIL_TEXT.format(
            season=state_service.get_season(),
            sleeper_name=self.sleeper_username,
            league_name=self.sleeper_league_name,
            league_link=self.sleeper_league_link,
        )

    def get_email_html(self):
        return self.EMAIL_HTML.format(
            season=state_service.get_season(),
            sleeper_name=self.sleeper_username,
            league_name=self.sleeper_league_name,
            league_link=self.sleeper_league_link,
        )

    def get_email_to(self):
        return self.season_user.user.email

    def get_email_type(self):
        return 3


class AnnouncementManager(models.Manager):
    def get_valid(self):
        today = datetime.date.today()
        return self.filter(valid_from__lte=today, valid_to__gte=today)


class Announcement(models.Model):
    class Meta:
        verbose_name_plural = "Announcements"

    objects = AnnouncementManager()

    valid_from = models.DateField()
    valid_to = models.DateField()
    content = HTMLField()


class News(models.Model):
    class Meta:
        verbose_name_plural = "News"

    title = models.TextField()
    content = HTMLField()
    image = models.CharField(
        null=False, blank=False, default=settings.DEFAULT_NEWS_LOGO, max_length=255
    )
    date = models.DateTimeField(auto_now=True)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = user.email
        return user

    def authentication_error(
        self,
        request,
        provider_id,
        error=None,
        exception=None,
        extra_context=None,
    ):
        import traceback

        logger.exception(
            "\nerror: {error}\nexception: {exception}\nextra_content: {extra_context}\nstacktrace: {trace}\nrequest: {request}".format(
                error=error,
                exception=exception,
                extra_context=extra_context,
                trace=traceback.format_exc(),
                request=request.__dict__,
            )
        )
