from django.contrib import admin

from DSTBundesliga.apps.leagues.models import Season, FinalSeasonStanding


class SeasonAdmin(admin.ModelAdmin):
    list_display = ['year', 'name', 'active']


class FinalSeasonStandingAdmin(admin.ModelAdmin):
    def get_owner(self, obj):
        return obj.dst_player

    list_display = ['points_ranking_overall', 'points_ranking_on_level', 'points_ranking_in_league', 'get_owner', 'league', 'season', 'rank_in_league', 'points', 'points_decimal']
    list_filter = ('season', 'league__level', 'points_ranking_on_level', 'points_ranking_in_league')


admin.site.register(Season, SeasonAdmin)
admin.site.register(FinalSeasonStanding, FinalSeasonStandingAdmin)


