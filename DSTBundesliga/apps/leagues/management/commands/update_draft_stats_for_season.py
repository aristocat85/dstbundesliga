from django.core.management import BaseCommand

from DSTBundesliga.apps.leagues.models import Season
from DSTBundesliga.apps.services.data_services import update_player_draft_stats_from_picks


class Command(BaseCommand):
    help = 'Update PlayerDraftStats for a given Season based on all Picks.'

    def add_arguments(self, parser):
        parser.add_argument(
            'season',
            type=str,
            help='Starting-Year of the Season, e.g. Season 2021/2022 the requested input is 2021'
        )

    def handle(self, *args, **options):
        season = Season.objects.get(year=options['season'])
        update_player_draft_stats_from_picks(season)
