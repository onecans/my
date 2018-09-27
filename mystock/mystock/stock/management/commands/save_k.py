from django.core.management.base import BaseCommand

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from contrib.tslib import *
BASE_DIR = '/data/k/'


def handler_df(df):
    df.index = pd.DatetimeIndex(df.index)
    df.sort_index(ascending=True, inplace=True)
    df['amount'] = df.amount / 100000000
    return df

def show2(df,df2, title=None, fig_size=(20, 10), vlines=None, file_name=None):
    
    df = handler_df(df)
    df2 = handler_df(df2)

    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    days = mdates.DayLocator()  # every day
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter('%m')
    
    rects = [
        [0.1, 0.7, 0.8, 0.25],
        [0.1, 0.55, 0.8, 0.1],
        [0.1, 0.2, 0.8, 0.25],
        [0.1, 0.05, 0.8, 0.1]]
    

    fig = plt.figure(figsize=fig_size)

    ax3 = fig.add_axes(rects[3])
    ax3.xaxis.set_major_locator(years)
    ax3.xaxis.set_major_formatter(yearsFmt)
    # ax3.xaxis.set_minor_locator(months)
    # ax3.xaxis.set_minor_formatter(monthsFmt)
    fig.autofmt_xdate()
    ax3.plot(df2.index, df2.amount, c='r', LineWidth=2)
    ax2 = fig.add_axes(rects[2], sharex=ax3)
    ax2.plot(df2.index, df2.high, c='r', LineWidth=2)

    ax1 = fig.add_axes(rects[1], sharex=ax3)
    ax1.plot(df.index, df.high, c='r', LineWidth=2)
    fig.autofmt_xdate()
    ax0 = fig.add_axes(rects[0], sharex=ax3)
    ax0.plot(df.index, df.high, c='r', LineWidth=2)
     
    ax0.set_title(title)


    # ax1.xaxis.set_major_locator(years)
    # ax1.xaxis.set_major_formatter(yearsFmt)
    # # ax1.xaxis.set_minor_locator(months)
    # # ax1.xaxis.set_minor_formatter(monthsFmt)

    # ax3.xaxis.set_major_locator(years)
    # ax3.xaxis.set_major_formatter(yearsFmt)
    # # ax3.xaxis.set_minor_locator(months)
    # # ax3.xaxis.set_minor_formatter(monthsFmt)

    for malab in ax0.get_xticklabels(minor=False):
        malab.set_visible(False)

    for milab in ax0.get_xticklabels(minor=True):
        milab.set_visible(False)

    for malab in ax2.get_xticklabels(minor=False):
        malab.set_visible(False)

    for milab in ax2.get_xticklabels(minor=True):
        milab.set_visible(False)


    ax1.grid(True, which='minor')
    ax2.grid(True, which='minor')
    ax3.grid(True, which='minor')
    ax0.grid(True, which='minor')

    if vlines:
        for l in vlines:
            ax0.axvline(x=l, c='r', alpha=1, linestyle='--', linewidth=1)
            ax2.axvline(x=l, c='r', alpha=1, linestyle='--', linewidth=1)


    fig.autofmt_xdate()
    if file_name:
        plt.savefig(file_name, fig_size=fig_size)
    else:
        plt.show()

def show(df, title=None, fig_size=(20,10), vlines=None, file_name=None ):
    df.index = pd.DatetimeIndex(df.index)
    df.sort_index(ascending=True, inplace=True)
    df['amount'] = df.amount / 100000000
    
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    days=mdates.DayLocator() #every day
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter('%m')
    
    rect1 = [0.1, 0.4, 0.8, 0.5]
    rect2 = [0.1, 0.1, 0.8, 0.2]
    fig = plt.figure(figsize=fig_size)
    # fig.size = fig_size

    ax2 = fig.add_axes(rect2)
    ax2.plot(df.index, df.amount, c='r', LineWidth=2)
    fig.autofmt_xdate()

    ax1 = fig.add_axes(rect1,  sharex=ax2)
    ax1.plot(df.index, df.high,c='r',LineWidth=2,)

    ax2.xaxis.set_major_locator(years)
    ax2.xaxis.set_major_formatter(yearsFmt)
    ax2.xaxis.set_minor_locator(months)
    ax2.xaxis.set_minor_formatter(monthsFmt)

    for malab in ax1.get_xticklabels(minor=False):
        malab.set_visible(False)

    for milab in ax1.get_xticklabels(minor=True):
        milab.set_visible(False)

    # format the coords message box
#     def price(x):
#         return '%@@@1.2f' % x
    ax1.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    # ax1.format_ydata = price
    ax1.grid(True, which='minor')
    ax1.set_title(title)
    ax1.set_ylabel('High')

    if vlines:
        for l in vlines:
            ax1.axvline(x=l, c='r', alpha=1, linestyle='--', linewidth=1 )

#     def amount(x):
#         return '%$$$1.2f' % x

    ax2.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    # ax2.format_ydata = amount
    ax2.grid(True, which='minor')
    ax2.set_ylabel('Amount')

    # rotates and right aligns the x labels, and moves the bottom of the
    # axes up to make room for them
    fig.autofmt_xdate()
    if file_name:
        plt.savefig(file_name, fig_size=fig_size)
    else:
        plt.show()

class Command(BaseCommand):
    help = '''Save K
    python manage.py save_k 1997-05-01 1998-08-30 9798
    Base Dir: %s''' % BASE_DIR

    def add_arguments(self, parser):
        parser.add_argument('start', nargs='+')
        parser.add_argument('end', nargs='+')
        parser.add_argument('dir', nargs='+')

    def handle(self, *args, **options):
        start = options['start'][0]
        end = options['end'][0]
        
        plt.rc('lines', linewidth=0.2, color='r')
        plt.rc('axes', grid=True)

        codes = get_sh_code_list()
        
        for code in codes:
            code = '600688'
            name = get_name(code)
            
            df = get_qfq(code=code, bdate=start, edate=end)
            df2 = get_qfq(code='000001', bdate=start, edate=end, index=True)
            total_amount = round(get_totals_amount(code),2)
            if  df is None or df.empty :
                continue

            dir = options['dir'][0] 
            if total_amount > 400:
                dir = dir + '_b'
            elif total_amount > 100:
                dir = dir + '_s'
            else:
                dir = dir + '_m'
            
            dir = os.path.join(BASE_DIR, dir)
            if not os.path.exists(dir):
                os.makedirs(dir)

            file_name = '%s/%s-%s-%s_%s_%d.png' % (dir, code, name,start, end, int(total_amount))
            print(file_name)
            file_name=''
            # show(df, title=code,fig_size=(20,10), file_name=file_name, vlines=['1997-05-12','1998-06-03','1998-08-18'])
            show2(df,df2, title=code,fig_size=(20,10), file_name=file_name, vlines=['1997-05-12','1998-06-03','1998-08-18'])
            # plt.close()
            break