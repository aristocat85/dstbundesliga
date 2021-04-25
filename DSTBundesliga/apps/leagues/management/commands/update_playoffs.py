from django.core.management import BaseCommand

from DSTBundesliga.apps.services.services import update_playoffs


class Command(BaseCommand):
    help = 'Updates all Playoffs from Sleeper-API'

    def handle(self, *args, **options):
        update_playoffs()
