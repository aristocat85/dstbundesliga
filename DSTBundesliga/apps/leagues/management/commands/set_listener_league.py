from django.core.management import BaseCommand

from DSTBundesliga.apps.leagues.models import League
from DSTBundesliga.apps.services.data_services import LeagueSetting, get_league_data, update_or_create_league, \
    update_drafts_for_league


class Command(BaseCommand):
    help = 'Update Draft for selected League'

    def add_arguments(self, parser):
        parser.add_argument(
            'league_id',
            type=str
        )

    def handle(self, *args, **options):
        league_id = options['league_id']
        league_settings = LeagueSetting(
            id=league_id,
            name='DST Hörerliga',
            type=League.LISTENER,
            level=99,
            conference=None,
            region=None
        )

        league_data = get_league_data(league_id)

        update_or_create_league(league_settings, league_data)
        update_drafts_for_league(league_id)
