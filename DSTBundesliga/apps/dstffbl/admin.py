from django.contrib import admin

from DSTBundesliga.apps.dstffbl.models import News, Announcement, SeasonUser


class NewsAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'content']
    ordering = ['-date']


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['valid_from', 'valid_to', 'content']
    ordering = ['-valid_from', '-valid_to']


class SeasonUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'sleeper_user', 'region', 'new_player', 'possible_commish', 'registration_ts']


admin.site.register(News, NewsAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(SeasonUser, SeasonUserAdmin)

