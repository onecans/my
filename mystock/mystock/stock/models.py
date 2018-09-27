from django.db import models
import re
# Create your models here.
class Stock(models.Model):
    code = models.CharField(max_length=10,  primary_key=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    pe = models.FloatField(blank=True, null=True)
    outstanding = models.FloatField(blank=True, null=True)
    totals = models.FloatField(blank=True, null=True)
    totalassets = models.FloatField(db_column='totalAssets', blank=True, null=True)  # Field name made lowercase.
    liquidassets = models.FloatField(db_column='liquidAssets', blank=True, null=True)  # Field name made lowercase.
    fixedassets = models.FloatField(db_column='fixedAssets', blank=True, null=True)  # Field name made lowercase.
    reserved = models.FloatField(blank=True, null=True)
    reservedpershare = models.FloatField(db_column='reservedPerShare', blank=True, null=True)  # Field name made lowercase.
    esp = models.FloatField(blank=True, null=True)
    bvps = models.FloatField(blank=True, null=True)
    pb = models.FloatField(blank=True, null=True)
    timetomarket = models.BigIntegerField(db_column='timeToMarket', blank=True, null=True)  # Field name made lowercase.
    undp = models.FloatField(blank=True, null=True)
    perundp = models.FloatField(blank=True, null=True)
    rev = models.FloatField(blank=True, null=True)
    profit = models.FloatField(blank=True, null=True)
    gpr = models.FloatField(blank=True, null=True)
    npr = models.FloatField(blank=True, null=True)
    holders = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ts_stocks'

    def __str__(self):
        return self.code + '-' + self.name

    @property
    def periods(self):
        qs = Value.objects.filter(stock=self).values_list('period', flat=True)
        s = set()
        for i in qs:
            s.add(i)

        return sorted(list(s))


    def calculate(self):
        seq = 10000
        Value.objects.filter(stock=self, item__report='formula').delete()
        formulas = Formula.objects.all()
        # formulas = chain(tmp1, tmp2, tmp3)
        for formula in formulas:
            print(formula)
            for period in self.periods:
                if formula.manual:
                    items = re.findall(r'{{([^{]*)}}', formula.manual)
                    tmp = formula.manual.replace(' ', '')
                    has_error = False
                    for item in items:
                        try:
                            print(item)
                            
                            value = Value.objects.get(stock=self,period=period, item__name=item).value
                            tmp = tmp.replace('{{%s}}' % item, str(value))
                        except Exception as e:
                            print(e.args)
                            has_error = True
                            break
                    if has_error:
                        continue
                    value = eval(tmp)
                    print(tmp, value)
                else:

                    adds = Value.objects.filter(stock=self,period=period, item__in=formula.adds.all()).aggregate(sum=models.Sum('value'))
                        
                    adds = adds['sum']
                    if adds is None:
                        continue
                    minus = Value.objects.filter(stock=self,period=period, item__in=formula.minus.all()
                                                ).aggregate(sum=models.Sum('value'))
                    minus = minus['sum'] if minus['sum'] else 0

                    value = adds - minus
                new_item_name = formula.name
                try:
                    item = Item.objects.get(name=new_item_name, report='formula')
                except Item.DoesNotExist:
                    item = Item(name=new_item_name, report='formula')
                    item.save()

                seq += 10
                try:
                    obj = Value.objects.get(stock=self, period=period, item=item)
                except Value.DoesNotExist:
                    obj = Value(stock=self, item=item, period=period)
                    
                obj.seq = seq
                # obj.source = 'formula: %s' % str(formula)

                obj.value = value
                obj.save()



class Item(models.Model):
    REPORT_NAME_CHOICES = (('xjllb', '现金流量表'), ('zcfzb', '资产负债表'), ('lrb', '利润表'), ('formula','计算值'))
    
    name = models.CharField(max_length=100)
    report = models.CharField(max_length=100,choices=REPORT_NAME_CHOICES)
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.report + '-' + self.name



class Value(models.Model):
    seq = models.IntegerField()
    # report = models.ForeignKey(Report, )
    item = models.ForeignKey(Item)
    period = models.CharField(max_length=10)
    value = models.FloatField()
    stock = models.ForeignKey(Stock)
    # source = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return '%s-%s-%s' % (str(self.stock), str(self.item), str(self.period))

    # @property
    # def amount(self):
    #     return self.value * self.report.unit

    @property
    def amount(self):
        return '{:,}'. format(self.value)

    class Meta:
        ordering = ['item__report','-period','seq']


class Formula(models.Model):
    seq = models.IntegerField()
    name = models.CharField(max_length=50)
    # stock = models.ForeignKey(Stock, blank=True, null=True)
    # report = models.ForeignKey(Report, blank=True, null=True)
    adds = models.ManyToManyField(Item, related_name='adds', blank=True)
    minus = models.ManyToManyField(Item, related_name='minus', blank=True)
    manual = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['seq']



class Group(models.Model):
    name = models.CharField(max_length=50)
    stocks = models.ManyToManyField(Stock)

    def __str__(self):
        return self.name
