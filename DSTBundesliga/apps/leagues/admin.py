from django.contrib import admin

from DSTBundesliga.apps.leagues.models import News


class NewsAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'content']
    ordering = ['-date']


admin.site.register(News, NewsAdmin)
