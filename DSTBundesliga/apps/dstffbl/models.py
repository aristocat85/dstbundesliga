import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from tinymce.models import HTMLField
from loguru import logger
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from DSTBundesliga.apps.leagues.models import Season, DSTPlayer, League


class SeasonUser(models.Model):
    REGIONS = (
        (1, 'Nord (Niedersachsen, Bremen, Hamburg, Mecklenburg-Vorpommern , Schleswig-Holstein)'),
        (2, 'Ost (Thüringen, Berlin, Sachsen, Sachsen-Anhalt, Brandenburg)'),
        (3, 'Süd (Bayern, Baden-Württemberg)'),
        (4, 'West (Nordrhein-Westfalen, Hessen, Saarland, Rheinland-Pfalz)'),
        (5, 'Ausland'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dst_player = models.ForeignKey(DSTPlayer, on_delete=models.CASCADE, null=True)
    season = models.ForeignKey(Season, on_delete=models.DO_NOTHING, default=Season.get_active)
    sleeper_id = models.CharField(max_length=50)
    region = models.IntegerField(choices=REGIONS)
    new_player = models.BooleanField(default=False)
    last_years_league = models.ForeignKey(League, null=True, on_delete=models.SET_NULL)
    possible_commish = models.BooleanField(default=False)
    registration_ts = models.DateTimeField(auto_now_add=True)

    def email(self):
        return self.user.email


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
    image = models.CharField(null=False, blank=False, default=settings.DEFAULT_NEWS_LOGO, max_length=255)
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
            "\nerror: {error}\nexception: {exception}\nextra_content: {extra_context}\nstacktrace: {trace}\nrequest: {request}".format(error=error, exception=exception, extra_context=extra_context, trace=traceback.format_exc(), request=request.__dict__)
        )
