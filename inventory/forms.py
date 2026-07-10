from django import forms
from .models import InventoryMovement, Product, Supplier, Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nombre de la Ubicación'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Latitud (ej: 19.043)', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Longitud (ej: -98.201)', 'step': '0.000001'}),
        }

class InventoryMovementForm(forms.ModelForm):
    class Meta:
        model = InventoryMovement
        fields = ['location', 'product', 'movement_type', 'quantity', 'merma', 'date']
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'product': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'movement_type': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_movement_type'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'merma': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow PRODUCCION and COMPRA for manual entry. Transfers and Sales are handled elsewhere.
        self.fields['movement_type'].choices = [
            ('PRODUCCION', 'Producción Propia'),
            ('COMPRA', 'Compra a Proveedor (Entrada)')
        ]
        self.fields['product'].queryset = Product.objects.filter(is_active=True)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.product:
            instance.product = Product.objects.filter(is_active=True).first()
        if commit:
            instance.save()
        return instance

class InventoryCorrectionForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        required=False,
        widget=forms.HiddenInput()
    )
    real_quantity = forms.IntegerField(label="Cantidad Real en Físico", widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg'}))

    def __init__(self, *args, **kwargs):
        location = kwargs.pop('location', None)
        super().__init__(*args, **kwargs)
        self.fields['product'].initial = Product.objects.filter(is_active=True).first()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('product'):
            cleaned_data['product'] = Product.objects.filter(is_active=True).first()
        return cleaned_data


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'supplier', 'unit_type', 'cost_price', 'sale_price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nombre del Producto'}),
            'supplier': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'unit_type': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 25px; height: 25px;'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'phone', 'email', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nombre del Proveedor'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nombre de Contacto'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Correo Electrónico'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 25px; height: 25px;'}),
        }


