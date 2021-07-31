from django.core.management import BaseCommand

from DSTBundesliga.apps.dstffbl.services.season_service import send_invitation_chunk


class Command(BaseCommand):
    help = 'Send Open Invitations for the current Season.'

    def handle(self, *args, **options):
        send_invitation_chunk()
