import os
import sys
import django

# Add project path dynamically
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huevoreal.settings')
django.setup()

from inventory.models import Inventory, InventoryMovement
from sales.models import Sale

# Find all VENTA movements associated with KILO sales
movements = InventoryMovement.objects.filter(
    movement_type='VENTA',
    sale__isnull=False,
    sale__sale_type='KILO'
)

print(f"Found {movements.count()} VENTA movements for KILO sales.")

updated_count = 0
for mov in movements:
    sale = mov.sale
    correct_pieces = sale.quantity_piece or 0
    current_pieces = mov.quantity
    
    if correct_pieces != current_pieces:
        difference = correct_pieces - current_pieces
        
        # Subtract the difference from the Inventory
        if mov.product and mov.location:
            inv, _ = Inventory.objects.get_or_create(location=mov.location, product=mov.product, defaults={'quantity': 0})
            inv.quantity -= difference
            inv.save()
            
            # Update the movement quantity
            mov.quantity = correct_pieces
            mov.save()
            
            updated_count += 1
            print(f"Reconciled movement {mov.pk} for Sale {sale.pk}: changed from {current_pieces} to {correct_pieces} pieces (subtracted additional {difference} pieces from {mov.location.name}).")

print(f"Successfully reconciled {updated_count} movements.")
