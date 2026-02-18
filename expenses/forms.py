from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'description', 'amount', 'category']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}, format='%Y-%m-%d'),
            'description': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select form-select-lg'}),
        }
