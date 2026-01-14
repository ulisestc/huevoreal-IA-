from django import forms
from .models import Sale

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['day', 'location', 'customer', 'sale_type', 'quantity_kg', 'quantity_piece', 'unit_price', 'price', 'amount_paid', 'is_paid', 'payment_date', 'payment_method']
        widgets = {
            'day': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            'location': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'customer': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'sale_type': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_sale_type'}),
            'payment_method': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'quantity_kg': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'id': 'id_quantity_kg'}),
            'quantity_piece': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'id': 'id_quantity_piece'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'id': 'id_unit_price'}),
            'price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'readonly': 'readonly', 'id': 'id_price'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 25px; height: 25px;'}),
        }
