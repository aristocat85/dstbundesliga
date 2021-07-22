import csv

from django.contrib import admin
from django.http import HttpResponse

from DSTBundesliga.apps.dstffbl.models import News, Announcement, SeasonUser


def download_season_users_csv(modeladmin, request, queryset):
    REGION = {
        1: 'Nord',
        2: 'Ost',
        3: 'Süd',
        4: 'West',
        5: 'Ausland',
    }

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=season_users.csv'
    writer = csv.writer(response)

    writer.writerow(["Email", "Sleeper Username", "Sleeper ID", "Region", "Neuer Spieler", "Liga letzte Saison", "Liga letzte Saison ID", "Potentieller Komissioner", "Anmeldezeitpunkt"])

    for su in queryset:
        sleeper_username, sleeper_id = su.sleeper_user().split(' - ') if su.sleeper_user() is not None else ("", "")
        new_player = "Ja" if su.new_player else "Nein"
        league, league_id = (su.last_years_league.sleeper_name, su.last_years_league.sleeper_id) if su.last_years_league else ("", "")
        commish = "Ja" if su.possible_commish else "Nein"
        region = REGION.get(su.region)
        writer.writerow([su.user.email, sleeper_username, sleeper_id, region, new_player, league, league_id, commish, su.registration_ts.strftime("%d.%m.%Y, %H:%M:%S")])

    return response


class NewsAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'content']
    ordering = ['-date']


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['valid_from', 'valid_to', 'content']
    ordering = ['-valid_from', '-valid_to']


class SeasonUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'sleeper_user', 'region', 'new_player', 'last_years_league', 'possible_commish', 'registration_ts']
    actions = [download_season_users_csv]


admin.site.register(News, NewsAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(SeasonUser, SeasonUserAdmin)

