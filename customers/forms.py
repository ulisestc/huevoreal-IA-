from django import forms
from .models import Customer, Fraccionamiento, Zona

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'address', 'phone_number', 'fraccionamiento', 'zona', 'latitude', 'longitude', 'observaciones']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 222 123 4567', 'maxlength': '12', 'inputmode': 'numeric'}),
            'fraccionamiento': forms.Select(attrs={'class': 'form-select'}),
            'zona': forms.Select(attrs={'class': 'form-select'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitud (ej: 19.043)', 'id': 'id_latitude', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitud (ej: -98.201)', 'id': 'id_longitude', 'step': '0.000001'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ej. 5 piezas a la semana, 10 quincenales, etc.', 'rows': 3}),
        }

    def clean_phone_number(self):
        import re
        phone = self.cleaned_data.get('phone_number', '').strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 13 and digits.startswith('521'):
            digits = digits[3:]
        elif len(digits) == 12 and digits.startswith('52'):
            digits = digits[2:]
        if len(digits) == 10:
            return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
        return phone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fraccionamiento'].queryset = Fraccionamiento.objects.all().order_by('name')
        self.fields['fraccionamiento'].empty_label = "Seleccione un fraccionamiento..."
        self.fields['fraccionamiento'].required = False
        
        self.fields['zona'].queryset = Zona.objects.all().order_by('name')
        self.fields['zona'].empty_label = "Seleccione una zona..."
        self.fields['zona'].required = False
        
        self.fields['last_name'].required = False
