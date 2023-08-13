from django.core.management import BaseCommand

from DSTBundesliga.apps.services.rss_service import update as update_rss


class Command(BaseCommand):
    help = "Updates News from Podcast-RSS-Feed"

    def handle(self, *args, **options):
        update_rss()
