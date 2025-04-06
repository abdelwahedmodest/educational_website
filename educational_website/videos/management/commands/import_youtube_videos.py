# videos/management/commands/import_youtube_videos.py
from django.core.management.base import BaseCommand
from utils.youtube_api import fetch_channel_videos

class Command(BaseCommand):
    help = 'Import videos from YouTube channel'

    def add_arguments(self, parser):
        parser.add_argument('channel_id', type=str, help='YouTube channel ID')

    def handle(self, *args, **options):
        channel_id = options['channel_id']
        count = fetch_channel_videos(channel_id)
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} videos'))
