from django.core.management.base import BaseCommand
from datareader.models import PeriodMinCnt

class Command(BaseCommand):
    help = "Fetch data from SE"

    def add_arguments(self, parser):
        parser.add_argument('--start', nargs='+')
        parser.add_argument('--year', nargs='+')
        parser.add_argument('--days', nargs='+')


    def handle(self, *args, **options):
        start = options['start'][0]
        year = options['year'][0]
        days = options['days'][0].split(',')
        objs = []
        for day  in days:
            if len(day) == 4:
                day = day[:2] + '-' + day[-2:]
            print(year+'-'+day)
            objs.append(PeriodMinCnt(where='ALL', period_start=start, period_end = year+'-'+day))

        PeriodMinCnt.objects.bulk_create(objs)



