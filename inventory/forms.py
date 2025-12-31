from django import forms
from .models import InventoryMovement

class InventoryMovementForm(forms.ModelForm):
    class Meta:
        model = InventoryMovement
        fields = ['location', 'movement_type', 'quantity', 'merma']
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'movement_type': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_movement_type'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'merma': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow PRODUCCION for manual entry. Transfers and Sales are handled elsewhere.
        self.fields['movement_type'].choices = [('PRODUCCION', 'Producción')]