from django.core.management import BaseCommand

from DSTBundesliga.apps.leagues.services import delete_old_leagues, get_league_settings


class Command(BaseCommand):
    help = 'Delete old leagues.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_false',
            help='Force delete (instead of dry run)'
        )

    def handle(self, *args, **options):
        delete_old_leagues(get_league_settings(), dry_run=options['force'])
