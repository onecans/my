import re
from django.db import models
from stock.models import *
from itertools import chain

# Create your models here.
# def __init__(self, verbose_name=None, name=None, primary_key=False,
#              max_length=None, unique=False, blank=False, null=False,
#              db_index=False, rel=None, default=NOT_PROVIDED, editable=True,
#              serialize=True, unique_for_date=None, unique_for_month=None,
#              unique_for_year=None, choices=None, help_text='', db_column=None,
#              db_tablespace=None, auto_created=False, validators=[],
#              error_messages=None):


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.description if self.description else self.name


class Report(models.Model):
    QUARTER_TYPE = 'QUARTER'
    YEAR_TYPE = 'YEAR'
    HALF_YEAR_TYPE = 'HALF_YEAR'
    # REPORT_TYPE_CHOICES = ((YEAR_TYPE, '年报'), (QUARTER_TYPE, '季报'), (HALF_YEAR_TYPE, '半年报'))
    REPORT_NAME_CHOICES = (('现金流量表', '现金流量表'), ('资产负债表', '资产负债表'), ('利润表', '利润表'))
    stock = models.ForeignKey(Stock)
    # report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    # year = models.IntegerField(blank=False)
    # quarter = models.IntegerField(blank=True, null=True)
    period = models.CharField(max_length=7)
    name = models.CharField(max_length=50, choices=REPORT_NAME_CHOICES)
    unit = models.IntegerField(default=1)

    def __str__(self):
        return str(self.stock) + ':' + self.period
        # if self.report_type == Report.YEAR_TYPE:
        #     return '%s %s %s 年报' % (str(self.stock), self.name, self.year)
        # if self.report_type == Report.HALF_YEAR_TYPE:
        #     return '%s %s %s 半年报' % (str(self.stock), self.name, self.year)
        # if self.report_type == Report.QUARTER_TYPE:
        #     return '%s %s %s 第%d季度报表' % (str(self.stock), self.year, self.name, self.quarter)

    def calculate(self):
        seq = 10000
        tmp1 = Formula.objects.filter(stock__isnull=True, report__isnull=True)
        tmp2 = Formula.objects.filter(stock=self.stock, report__isnull=True)
        tmp3 = Formula.objects.filter(stock=self.stock, report=self)
        formulas = chain(tmp1, tmp2, tmp3)
        for formula in formulas:
            print(formula.manual)
            if formula.manual:
                items = re.findall(r'{{([^{]*)}}', formula.manual)
                tmp = formula.manual.replace(' ', '')
                has_error = False
                for item in items:
                    try:
                        value = Value.objects.get(report=self, item__name=item).value
                        tmp = tmp.replace('{{%s}}' % item, str(value))
                    except Exception as e:
                        print(e.args)
                        has_error = True
                        break
                if has_error:
                    continue
                value = eval(tmp)
                value = value / self.unit
                print(tmp, value)
            else:

                adds = Value.objects.filter(report=self, item__in=formula.adds.all()).aggregate(sum=models.Sum('value'))
                    
                adds = adds['sum']
                if adds is None:
                    continue
                minus = Value.objects.filter(report=self, item__in=formula.minus.all()
                                             ).aggregate(sum=models.Sum('value'))
                minus = minus['sum'] if minus['sum'] else 0

                value = adds - minus
            new_item_name = formula.name
            try:
                item = Item.objects.get(name=new_item_name)
            except:
                item = Item(name=new_item_name)
                item.save()

            seq += 10
            try:
                obj = Value.objects.get(report=self, item=item)
            except:
                obj = Value(report=self, item=item)
            obj.seq = seq
            obj.source = 'formula: %s' % str(formula)

            obj.value = value
            obj.save()


class Value(models.Model):
    seq = models.IntegerField()
    report = models.ForeignKey(Report, )
    item = models.ForeignKey(Item, )
    value = models.FloatField()
    source = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return str(self.report) + ' ' + str(self.item)

    @property
    def amount(self):
        return self.value * self.report.unit

    @property
    def amount_k(self):
        return '{:,}'. format(self.amount / 1000)

    class Meta:
        ordering = ['report', 'seq']


class Formula(models.Model):
    seq = models.IntegerField()
    name = models.CharField(max_length=50)
    stock = models.ForeignKey(Stock, blank=True, null=True)
    report = models.ForeignKey(Report, blank=True, null=True)
    adds = models.ManyToManyField(Item, related_name='adds', blank=True)
    minus = models.ManyToManyField(Item, related_name='minus', blank=True)
    manual = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['seq']
