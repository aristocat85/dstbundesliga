import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from tinymce.models import HTMLField

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from DSTBundesliga.apps.leagues.models import Season, DSTPlayer


class SeasonUser(models.Model):
    REGIONS = (
        (1, 'Nord (Niedersachsen, Bremen, Hamburg, Mecklenburg-Vorpommern , Schleswig-Holstein)'),
        (2, 'Ost (Thüringen, Berlin, Sachsen, Sachsen-Anhalt, Brandenburg)'),
        (3, 'Süd (Bayern, Baden-Württemberg)'),
        (4, 'West (Nordrhein-Westfalen, Hessen, Saarland, Rheinland-Pfalz)'),
        (5, 'Ausland'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.DO_NOTHING, default=Season.get_active)
    sleeper_id = models.CharField(max_length=50)
    region = models.IntegerField(choices=REGIONS)
    new_player = models.BooleanField(default=False)
    possible_commish = models.BooleanField(default=False)


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
