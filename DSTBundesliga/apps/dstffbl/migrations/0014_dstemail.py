# Generated by Django 3.1.14 on 2022-07-24 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dstffbl', '0013_auto_20220724_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='DSTEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient', models.EmailField(max_length=254)),
                ('subject', models.CharField(max_length=998)),
                ('text', models.TextField()),
                ('html', models.TextField()),
                ('send_ts', models.DateTimeField(null=True)),
                ('has_erros', models.BooleanField(default=False)),
                ('error_message', models.CharField(max_length=500)),
            ],
        ),
    ]
