from django.core.management import BaseCommand

from DSTBundesliga.apps.services.data_services import update_listener_draft


class Command(BaseCommand):
    help = 'Update Hörerliga'

    def handle(self, *args, **options):
        update_listener_draft()
