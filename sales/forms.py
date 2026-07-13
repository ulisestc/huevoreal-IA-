from django import forms
from .models import Sale, Order, RecurringOrder
from customers.models import Customer
from inventory.models import Product, Location

class SaleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by('first_name', 'last_name')
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
        self.fields['product'].required = False
        self.fields['product'].empty_label = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.product:
            instance.product = Product.objects.filter(is_active=True).first()
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Sale
        fields = ['day', 'location', 'product', 'customer', 'sale_type', 'quantity_kg', 'quantity_piece', 'unit_price', 'price', 'amount_paid', 'is_paid', 'payment_date', 'payment_method']
        widgets = {
            'day': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}, format='%Y-%m-%d'),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}, format='%Y-%m-%d'),
            'location': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'product': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_product'}),
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

class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by('first_name', 'last_name')
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
        self.fields['location'].required = True
        self.fields['product'].required = False
        self.fields['product'].empty_label = None
        import datetime
        if not self.instance.pk:
            self.initial['delivery_date'] = datetime.date.today()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.product:
            instance.product = Product.objects.filter(is_active=True).first()
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Order
        fields = ['customer', 'location', 'product', 'sale_type', 'quantity_kg', 'quantity_piece', 'unit_price', 'total_price', 'payment_method', 'delivery_date']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'location': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'product': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_product'}),
            'sale_type': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_sale_type'}),
            'payment_method': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'quantity_kg': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'id': 'id_quantity_kg'}),
            'quantity_piece': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'id': 'id_quantity_piece'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'id': 'id_unit_price'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'readonly': 'readonly', 'id': 'id_price'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
        }

class RecurringOrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by('first_name', 'last_name')
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
        self.fields['location'].queryset = Location.objects.all().order_by('name')
        self.fields['location'].required = True
        self.fields['product'].required = False
        self.fields['product'].empty_label = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.product:
            instance.product = Product.objects.filter(is_active=True).first()
        if commit:
            instance.save()
        return instance

    class Meta:
        model = RecurringOrder
        fields = ['customer', 'location', 'product', 'sale_type', 'quantity_kg', 'quantity_piece', 'unit_price', 'total_price', 'payment_method', 'frequency', 'day_of_week', 'day_of_month', 'is_active']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'location': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'product': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_product'}),
            'sale_type': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_sale_type'}),
            'payment_method': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'quantity_kg': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'id': 'id_quantity_kg'}),
            'quantity_piece': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'id': 'id_quantity_piece'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'id': 'id_unit_price'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'readonly': 'readonly', 'id': 'id_price'}),
            'frequency': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'day_of_week': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'id': 'id_day_of_week'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 25px; height: 25px;'}),
        }
