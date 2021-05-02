from django.contrib import admin

from DSTBundesliga.apps.leagues.models import Season


class SeasonAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'active']


admin.site.register(Season, SeasonAdmin)
