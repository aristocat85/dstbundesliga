from django.contrib.auth.models import User
from django.db import models

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
