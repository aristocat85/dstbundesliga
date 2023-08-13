from django.core.management import BaseCommand

from DSTBundesliga.apps.services.data_services import update_matchups


class Command(BaseCommand):
    help = "Updates all Matchups from Sleeper-API"

    def handle(self, *args, **options):
        update_matchups()
