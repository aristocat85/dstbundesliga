# Generated by Django 3.1.13 on 2021-08-08 09:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0030_auto_20210725_1424'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='league',
            name='season',
        ),
        migrations.RemoveField(
            model_name='statsweek',
            name='season',
        ),
    ]