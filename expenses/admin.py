from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'amount', 'category', 'user')
    list_filter = ('date', 'category', 'user')
    search_fields = ('description',)