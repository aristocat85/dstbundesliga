from django.core.management import BaseCommand

from DSTBundesliga.apps.services.data_services import get_draft_data, update_drafts_for_league, \
    get_pick_data, update_picks_for_draft


class Command(BaseCommand):
    help = 'Update Draft for selected League'

    def add_arguments(self, parser):
        parser.add_argument(
            'league_id',
            type=str,
            help='Force delete (instead of dry run)'
        )

    def handle(self, *args, **options):
        league_id = options['league_id']
        drafts_data = get_draft_data(league_id)
        drafts = update_drafts_for_league(league_id, drafts_data)

        for draft in drafts:
            picks_data = get_pick_data(draft.draft_id)
            update_picks_for_draft(draft.draft_id, picks_data)
