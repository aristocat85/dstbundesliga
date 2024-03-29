from django.core.management import BaseCommand

from DSTBundesliga.apps.services.data_services import update_stats


class Command(BaseCommand):
    help = "Updates all Stats from Sleeper-API"

    def handle(self, *args, **options):
        update_stats()
