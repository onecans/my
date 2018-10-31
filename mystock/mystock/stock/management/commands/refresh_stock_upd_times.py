from django.core.management.base import BaseCommand


from collections import OrderedDict

import pandas as pd

from contrib.tslib import *

class Command(BaseCommand):
    help = "Refresh Stock Upd Times below 15 times"

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        # coding=utf-8
        print ('code,name,上市以来最大涨幅')
        cnt = 0
        for idx, code in enumerate(get_code_list()):
            try:
                update = get_price_times(code=code)
                name = get_name(code)
                timeToMarket = get_timeToMarket(code)
                if not timeToMarket:
                    continue
                timeToMarket = timeToMarket.strftime('%Y-%m-%d')

                if update < 6:
                    print ( code, name, update)
            except:
                # print ('ERROR %s' % code, name)
                pass
                
