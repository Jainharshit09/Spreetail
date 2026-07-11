from django.contrib import admin
from .models import Group, Membership, Currency, Expense, ExpenseSplit, Settlement, ImportLog

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'start_date', 'end_date')
    search_fields = ('user__username', 'group__name')
    list_filter = ('start_date', 'end_date')

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'exchange_rate', 'last_updated')
    search_fields = ('code', 'name')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'paid_by', 'amount', 'group')
    search_fields = ('description', 'paid_by__username', 'group__name')
    list_filter = ('date', 'split_type', 'group')

@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ('expenditure', 'user', 'amount')
    search_fields = ('user__username', 'expenditure__description')
    list_filter = ('expenditure__date',)

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('payer', 'payee', 'amount', 'date', 'status')
    search_fields = ('payer__username', 'payee__username', 'group__name')
    list_filter = ('status', 'date')

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ('filename', 'imported_at', 'status')
    search_fields = ('filename',)
    list_filter = ('status', 'imported_at')
