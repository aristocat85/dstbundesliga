# Generated by Django 3.0.7 on 2020-06-28 09:04

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Draft",
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
                ("draft_type", models.CharField(max_length=20)),
                ("status", models.CharField(max_length=20)),
                ("start_time", models.DateTimeField()),
                ("settings", jsonfield.fields.JSONField()),
                ("season_type", models.CharField(max_length=20)),
                ("season", models.IntegerField()),
                ("metadata", jsonfield.fields.JSONField()),
                ("last_picked", models.DateTimeField()),
                ("last_message_time", models.DateTimeField()),
                ("last_message_id", models.CharField(max_length=50)),
                ("draft_id", models.CharField(max_length=50)),
                ("draft_order", jsonfield.fields.JSONField()),
                ("slot_to_roster_id", jsonfield.fields.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="DSTPlayer",
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
                (
                    "sleeper_id",
                    models.CharField(db_index=True, max_length=50, unique=True),
                ),
                ("display_name", models.CharField(db_index=True, max_length=50)),
                ("avatar_id", models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="League",
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
                ("level", models.IntegerField(default=0)),
                ("total_rosters", models.IntegerField(default=12)),
                ("status", models.CharField(max_length=20)),
                ("sport", models.CharField(max_length=30)),
                ("settings", jsonfield.fields.JSONField()),
                ("season_type", models.CharField(max_length=30)),
                ("season", models.IntegerField(default=2020)),
                ("scoring_settings", jsonfield.fields.JSONField()),
                ("roster_positions", jsonfield.fields.JSONField()),
                ("previous_league_id", models.CharField(max_length=100, null=True)),
                ("sleeper_name", models.CharField(max_length=50)),
                (
                    "sleeper_id",
                    models.CharField(db_index=True, max_length=50, unique=True),
                ),
                ("draft_id", models.CharField(max_length=50)),
                ("avatar_id", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Team",
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
                ("name", models.CharField(max_length=50)),
                ("abbr", models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name="Roster",
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
                ("name", models.CharField(max_length=100, null=True)),
                ("starters", models.CharField(max_length=100)),
                ("settings", jsonfield.fields.JSONField()),
                ("roster_id", models.IntegerField()),
                ("reserve", models.CharField(max_length=100)),
                ("players", models.CharField(max_length=255)),
                (
                    "league",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="leagues.League"
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="leagues.DSTPlayer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Player",
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
                ("sleeper_id", models.IntegerField()),
                ("hashtag", models.CharField(max_length=50)),
                ("depth_chart_position", models.IntegerField()),
                ("status", models.CharField(max_length=20)),
                ("fantasy_positions", models.CharField(max_length=50)),
                ("number", models.IntegerField()),
                ("last_name", models.CharField(max_length=50)),
                ("first_name", models.CharField(max_length=50)),
                ("weight", models.IntegerField()),
                ("position", models.CharField(max_length=50)),
                ("height", models.CharField(max_length=10)),
                ("age", models.IntegerField()),
                ("espn_id", models.CharField(max_length=50)),
                ("yahoo_id", models.CharField(max_length=50)),
                (
                    "team",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="leagues.Team",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Pick",
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
                ("round", models.IntegerField(default=1)),
                ("draft_slot", models.IntegerField(default=1)),
                ("pick_no", models.IntegerField(default=1)),
                ("metadata", jsonfield.fields.JSONField()),
                (
                    "draft",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="leagues.Draft"
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="leagues.Player"
                    ),
                ),
                (
                    "roster",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="leagues.Roster"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="leagues.DSTPlayer",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="dstplayer",
            name="leagues",
            field=models.ManyToManyField(to="leagues.League"),
        ),
        migrations.AddField(
            model_name="draft",
            name="league",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="leagues.League"
            ),
        ),
    ]
