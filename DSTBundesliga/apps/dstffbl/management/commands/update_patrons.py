from django.core.management import BaseCommand

from DSTBundesliga.apps.dstffbl.services.patreon_service import (
    update_patrons
)

class Command(BaseCommand):
    help = "Updates all Patrons from Patreon API"

    def handle(self, *args, **options):
        update_patrons()

