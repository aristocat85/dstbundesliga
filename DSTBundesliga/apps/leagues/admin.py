from django.contrib import admin

from DSTBundesliga.apps.leagues.models import News, Season


class NewsAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'content']
    ordering = ['-date']


class SeasonAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'active']


admin.site.register(News, NewsAdmin)
admin.site.register(Season, SeasonAdmin)
