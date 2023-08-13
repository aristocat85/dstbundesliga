# Generated by Django 3.0.7 on 2020-09-13 07:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0017_auto_20200903_2012"),
    ]

    operations = [
        migrations.CreateModel(
            name="Matchup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("week", models.IntegerField(db_index=True)),
                ("matchup_id", models.IntegerField(db_index=True)),
                ("league_id", models.CharField(db_index=True, max_length=50)),
                ("roster_id_one", models.IntegerField()),
                ("starters_one", models.CharField(max_length=255, null=True)),
                ("players_one", models.CharField(max_length=255, null=True)),
                ("points_one", models.DecimalField(decimal_places=3, max_digits=6)),
                ("roster_id_two", models.IntegerField()),
                ("starters_two", models.CharField(max_length=255, null=True)),
                ("players_two", models.CharField(max_length=255, null=True)),
                ("points_two", models.DecimalField(decimal_places=3, max_digits=6)),
            ],
        ),
    ]
