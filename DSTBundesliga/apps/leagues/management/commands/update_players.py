from django.core.management import BaseCommand

from DSTBundesliga.apps.services.data_services import update_players


class Command(BaseCommand):
    help = "Updates all Leagues from Sleeper-API"

    def handle(self, *args, **options):
        update_players()
