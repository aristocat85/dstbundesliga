from django.core.management import BaseCommand

from DSTBundesliga.apps.dstffbl.services.season_service import update_last_years_leagues


class Command(BaseCommand):
    help = 'Updates Season Users last years leagues'

    def handle(self, *args, **options):
        update_last_years_leagues()
