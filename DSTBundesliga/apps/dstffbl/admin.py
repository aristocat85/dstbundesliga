import csv

import pytz
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from DSTBundesliga.apps.dstffbl.models import (
    News,
    Announcement,
    SeasonUser,
    SeasonInvitation,
    SeasonRegistration,
    DSTEmail,
)


def download_season_users_csv(modeladmin, request, queryset):
    REGION = {
        1: "Nord",
        2: "Ost",
        3: "Süd",
        4: "West",
        5: "Ausland",
    }

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment;filename=season_users.csv"
    writer = csv.writer(response)

    writer.writerow(
        [
            "Email",
            "Sleeper Username",
            "Sleeper ID",
            "Region",
            "Neuer Spieler",
            "Liga letzte Saison",
            "Liga letzte Saison ID",
            "Potentieller Komissioner",
            "Anmeldezeitpunkt",
        ]
    )

    for su in queryset:
        new_player = "Ja" if su.new_player else "Nein"
        league, league_id = (
            (su.last_years_league.sleeper_name, su.last_years_league.sleeper_id)
            if su.last_years_league
            else ("", "")
        )
        commish = "Ja" if su.possible_commish else "Nein"
        region = REGION.get(su.region)
        writer.writerow(
            [
                su.user.email,
                su.dst_player.display_name,
                su.sleeper_id,
                region,
                new_player,
                league,
                league_id,
                commish,
                su.registration.registration_ts.astimezone(
                    pytz.timezone("Europe/Berlin")
                ).strftime("%d.%m.%Y, %H:%M:%S"),
            ]
        )

    return response


def download_season_registrations_csv(modeladmin, request, queryset):
    REGION = {
        1: "Nord",
        2: "Ost",
        3: "Süd",
        4: "West",
        5: "Ausland",
    }

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment;filename=season_registrations.csv"
    writer = csv.writer(response)

    writer.writerow(
        [
            "Email",
            "Sleeper Username",
            "Sleeper ID",
            "Region",
            "Neuer Spieler",
            "Liga letzte Saison",
            "Liga letzte Saison ID",
            "Potentieller Komissioner",
            "Registrierzeitpunkt",
        ]
    )

    for su in queryset:
        new_player = "Ja" if su.new_player else "Nein"
        league, league_id = (
            (su.last_years_league.sleeper_name, su.last_years_league.sleeper_id)
            if su.last_years_league
            else ("", "")
        )
        commish = "Ja" if su.possible_commish else "Nein"
        region = REGION.get(su.region)
        writer.writerow(
            [
                su.user.email,
                su.dst_player.display_name,
                su.sleeper_id,
                region,
                new_player,
                league,
                league_id,
                commish,
                su.registration_ts.astimezone(
                    pytz.timezone("Europe/Berlin")
                ).strftime("%d.%m.%Y, %H:%M:%S"),
            ]
        )

    return response


class NewsAdmin(admin.ModelAdmin):
    list_display = ["date", "title", "content"]
    ordering = ["-date"]


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["valid_from", "valid_to", "content"]
    ordering = ["-valid_from", "-valid_to"]


class SeasonUserAdmin(admin.ModelAdmin):
    def get_sleeper_username(self, obj):
        return obj.dst_player.display_name

    get_sleeper_username.short_description = "Sleeper Username"

    list_display = [
        "email",
        "get_sleeper_username",
        "sleeper_id",
        "region",
        "new_player",
        "last_years_league",
        "possible_commish",
        "confirm_ts",
    ]
    search_fields = [
        "user__email",
        "dst_player__display_name",
        "sleeper_id",
        "last_years_league__sleeper_name",
    ]
    list_filter = ("season", "region", "new_player", "possible_commish")
    actions = [download_season_users_csv]


class SeasonRegistrationAdmin(admin.ModelAdmin):
    def get_sleeper_username(self, obj):
        return obj.dst_player.display_name

    get_sleeper_username.short_description = "Sleeper Username"

    list_display = [
        "email",
        "get_sleeper_username",
        "sleeper_id",
        "region",
        "new_player",
        "last_years_league",
        "possible_commish",
        "registration_ts",
        "confirm_registration",
    ]
    search_fields = [
        "user__email",
        "dst_player__display_name",
        "sleeper_id",
        "last_years_league__sleeper_name",
    ]
    list_filter = ("season", "region", "new_player", "possible_commish")
    actions = [download_season_registrations_csv]

    def confirm_registration(self, obj):
        return format_html("<a href='{url}'>Registrierung bestätigen</a>", url=obj.url)


class SeasonInvitationAdmin(admin.ModelAdmin):
    def get_sleeper_username(self, obj):
        return obj.season_user.dst_player.display_name

    list_display = [
        "get_sleeper_username",
        "sleeper_league_name",
        "sleeper_league_id",
        "sleeper_league_link",
        "created",
    ]
    ordering = ["-created", "sleeper_league_id"]


class DSTEmailAdmin(admin.ModelAdmin):
    list_display = ["type", "recipient", "subject", "send_ts", "has_erros"]
    list_filter = ("type", "has_erros")
    search_fields = ["recipient"]
    ordering = ["-send_ts"]


admin.site.register(News, NewsAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(SeasonUser, SeasonUserAdmin)
admin.site.register(SeasonRegistration, SeasonRegistrationAdmin)
admin.site.register(SeasonInvitation, SeasonInvitationAdmin)
admin.site.register(DSTEmail, DSTEmailAdmin)
