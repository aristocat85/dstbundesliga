from django.core.management import BaseCommand

from DSTBundesliga.apps.leagues.services import update_drafts


class Command(BaseCommand):
    help = 'Updaties all Leagues from Sleeper-API'

    def handle(self, *args, **options):
        update_drafts()
