from django.core.management import BaseCommand

from DSTBundesliga.apps.services.services import update_leagues


class Command(BaseCommand):
    help = 'Updates all Leagues from Sleeper-API'

    def handle(self, *args, **options):
        update_leagues()
