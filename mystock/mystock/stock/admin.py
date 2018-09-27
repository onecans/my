from django.contrib import admin
from stock.models import *
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.html import format_html, format_html_join
# Register your models here.


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    search_fields = ['code', 'name']
    list_display = ['code', 'name', 'periods']

    actions = ['import_report_data', 'calculate']

    def import_report_data(self, request, query_set):
        if len(query_set) > 1:
            self.message_user(request, '一次只能处理一个', messages.WARNING)

        code = query_set[0].code
        return HttpResponseRedirect('/stock/report_handler/{code}'.format(code=code))

    def calculate(self, request, query_set):
        if len(query_set) > 1:
            self.message_user(request, '一次只能处理一个', messages.WARNING)

        stock = query_set[0]
        stock.calculate()


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ['stocks']
    list_display = ['name', 'import_report_data_urls']
    actions = ['calculate']

    def import_report_data_urls(self, obj):
        link = '<a href="/stock/report_handler/{}">{}</a><br/>'
        # content = []
        # for stock in obj.stocks:
        #     content.append(link.format(code=stock.code, name=str(stock)))

        return format_html_join(sep='\n', format_string=link, args_generator=[(stock.code, str(stock)) for stock in obj.stocks.all()])
    
    def calculate(self, request, query_set):
        for group in query_set:
            for stock in group.stocks.all():
                stock.calculate()


@admin.register(Value)
class ValuesAdmin(admin.ModelAdmin):
    list_display = ['seq', 'stock', 'item', 'period', 'amount']
    list_filter = ['stock', 'item__report', 'period', 'item']
    search_fields = ['item__name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    filter_horizontal = ['adds','minus']
