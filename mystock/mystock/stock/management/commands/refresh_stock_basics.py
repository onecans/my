from django.core.management.base import BaseCommand
import tushare as ts
from django.conf import settings
from sqlalchemy import create_engine, types


class Command(BaseCommand):
    help = "Refresh Stock Basics From Tushares"

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        print(db)
        df = ts.get_stock_basics()
        engine = create_engine('mysql://root:root@localhost/mystock?charset=utf8', encoding='utf-8')

        df.to_sql(con=engine, name='ts_stocks', if_exists='replace', dtype={'code': types.VARCHAR(
            10), 'name': types.VARCHAR(200), 'industry': types.VARCHAR(100), 'area': types.VARCHAR(100)})
