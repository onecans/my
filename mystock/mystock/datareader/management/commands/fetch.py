from django.core.management.base import BaseCommand
from datareader.base import SE

class Command(BaseCommand):
    help = "Fetch data from SE"

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        se = SE()
        se.fetch()
