from django.contrib import admin

from DSTBundesliga.apps.dstffbl.models import News, Announcement


class NewsAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'content']
    ordering = ['-date']


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['valid_from', 'valid_to', 'content']
    ordering = ['-valid_from', '-valid_to']


admin.site.register(News, NewsAdmin)
admin.site.register(Announcement, AnnouncementAdmin)

