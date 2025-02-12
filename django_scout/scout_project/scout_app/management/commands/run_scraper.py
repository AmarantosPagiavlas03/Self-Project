# management/commands/scrape_epsath.py
from django.core.management.base import BaseCommand
from scout_app.scrapers.scraper import scrape_players

class Command(BaseCommand):
    help = 'Scrape EPSATH players and statistics'

    def handle(self, *args, **options):
        try:
            players = scrape_players()
            self.stdout.write(self.style.SUCCESS(f'Successfully scraped {len(players)} players'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error scraping data: {str(e)}'))