from django import forms
from django.contrib.auth import get_user_model
from .models import Customer, Fraccionamiento, Zona

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'address', 'phone_number', 'fraccionamiento', 'zona', 'observaciones', 'seller']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'fraccionamiento': forms.Select(attrs={'class': 'form-select'}),
            'zona': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ej. 5 piezas a la semana, 10 quincenales, etc.', 'rows': 3}),
            'seller': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields['seller'].queryset = User.objects.all().order_by('username')
        self.fields['seller'].empty_label = "Seleccione un vendedor..."
        self.fields['seller'].required = False
        
        self.fields['fraccionamiento'].queryset = Fraccionamiento.objects.all().order_by('name')
        self.fields['fraccionamiento'].empty_label = "Seleccione un fraccionamiento..."
        self.fields['fraccionamiento'].required = False
        
        self.fields['zona'].queryset = Zona.objects.all().order_by('name')
        self.fields['zona'].empty_label = "Seleccione una zona..."
        self.fields['zona'].required = False
        
        self.fields['last_name'].required = False
