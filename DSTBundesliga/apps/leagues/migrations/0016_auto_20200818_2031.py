# Generated by Django 3.0.7 on 2020-08-18 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0015_league_conference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roster',
            name='players',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='roster',
            name='reserve',
            field=models.CharField(max_length=100, null=True),
        ),
    ]