from django.core.management import BaseCommand

from DSTBundesliga.apps.dstffbl.services.season_service import (
    import_invitations,
)


class Command(BaseCommand):
    help = "Import Invitations from CSV File"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="Path to CSV File")

    def handle(self, *args, **options):
        filepath = options["filepath"]
        import_invitations(filepath)
