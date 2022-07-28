from django.core.management import BaseCommand

from DSTBundesliga.apps.leagues.models import Season
from DSTBundesliga.apps.services.season_service import calc_final_standings


class Command(BaseCommand):
    help = 'Calculate the final standings for the given season'

    def add_arguments(self, parser):
        parser.add_argument(
            'season',
            type=int
        )

    def handle(self, *args, **options):
        season = Season.objects.get(year=options['season'])

        calc_final_standings(season)
