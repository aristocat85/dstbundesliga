from django.core.management import BaseCommand

from DSTBundesliga.apps.services.data_services import get_current_week, update_trades


class Command(BaseCommand):
    help = 'Updates all Stats from Sleeper-API'

    def handle(self, *args, **options):
        weeks = range(1, get_current_week()+2)
        for week in weeks:
            update_trades(week)
