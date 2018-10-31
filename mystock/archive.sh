cd ..
rm -f mystockservice.zip
rm -f mystock.zip
zip -x mystockservice/dump.rdb -x \*.ipynb -r mystockservice.zip  mystockservice
zip -x mystock/mystock/datareader/data/\* -x mystock/staticfiles/\* -x \*.ipynb -x mystock/mystock/datareader/data/\* -x \*__pycache__\* -r mystock.zip mystock


zip mystock_all.zip  mystockservice.zip mystock.zip



y =  '0000'
period_start = '1994-08-01'
for d in ('+1994','0913','+1995','0207','0522', '+1996','0119','1211','+1997','0512','0708','0923','+1998','0209','0604','0818','1117','+1999','0208'):
    if d.startswith('+'):
         y = d[1:]
         continue
    s = y+d
    date = datetime.datetime.strptime(s, '%Y%m%d')
    print(date)
    PeriodMinCnt(where='ALL', period_start=period_start,period_end=date).save()
