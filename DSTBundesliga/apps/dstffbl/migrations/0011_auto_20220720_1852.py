# Generated by Django 3.1.14 on 2022-07-20 16:52

import DSTBundesliga.apps.leagues.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0037_auto_20220720_1847"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dstffbl", "0010_seasoninvitation"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="seasonuser",
            name="registration_ts",
        ),
        migrations.AddField(
            model_name="seasonuser",
            name="confirm_ts",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.CreateModel(
            name="SeasonRegistration",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("sleeper_id", models.CharField(max_length=50)),
                (
                    "region",
                    models.IntegerField(
                        choices=[
                            (
                                1,
                                "Nord (Niedersachsen, Bremen, Hamburg, Mecklenburg-Vorpommern , Schleswig-Holstein)",
                            ),
                            (
                                2,
                                "Ost (Thüringen, Berlin, Sachsen, Sachsen-Anhalt, Brandenburg)",
                            ),
                            (3, "Süd (Bayern, Baden-Württemberg)"),
                            (
                                4,
                                "West (Nordrhein-Westfalen, Hessen, Saarland, Rheinland-Pfalz)",
                            ),
                            (5, "Ausland"),
                        ]
                    ),
                ),
                ("new_player", models.BooleanField(default=False)),
                ("possible_commish", models.BooleanField(default=False)),
                ("registration_ts", models.DateTimeField(auto_now_add=True)),
                (
                    "dst_player",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="leagues.dstplayer",
                    ),
                ),
                (
                    "last_years_league",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="leagues.league",
                    ),
                ),
                (
                    "season",
                    models.ForeignKey(
                        default=DSTBundesliga.apps.leagues.models.Season.get_active,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="leagues.season",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="seasonuser",
            name="registration",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="dstffbl.seasonregistration",
            ),
        ),
    ]
