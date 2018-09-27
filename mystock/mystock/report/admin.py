from django.contrib import admin
from report.models import *
# Register your models here.
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    actions = ['calculate_formulas']
    def calculate_formulas(self, request, queryset):
        for report in queryset:
            report.calculate()


@admin.register(Value)
class ValuesAdmin(admin.ModelAdmin):
    list_display = ['report','seq', 'item', 'amount_k', 'source']
    list_filter = ['report', 'item']
    search_fields = ['item__name']
    

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ['seq', 'name','manual']
    filter_horizontal = ['adds','minus']