from django.core.management import BaseCommand

from DSTBundesliga.apps.services.data_services import update_stats_for_weeks, get_current_week


class Command(BaseCommand):
    help = 'Updates all Stats from Sleeper-API'

    def handle(self, *args, **options):
        weeks = range(1, get_current_week()+1)
        update_stats_for_weeks(weeks)
