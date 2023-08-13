from django.core.management import BaseCommand

from DSTBundesliga.apps.dstffbl.services.season_service import (
    create_leagues_from_invitations,
)


class Command(BaseCommand):
    help = "Create Leagues from the given Invitations"

    def handle(self, *args, **options):
        create_leagues_from_invitations()
