from django.core.management import BaseCommand

from DSTBundesliga.apps.services.services import update_listener_league


class Command(BaseCommand):
    help = 'Update Hörerliga'

    def handle(self, *args, **options):
        update_listener_league()
