import os
import sys
import django
import datetime

# Add project path dynamically
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huevoreal.settings')
django.setup()

from inventory.models import Inventory, InventoryMovement

# Find all COMPRA movements on or after July 13, 2026
movements = InventoryMovement.objects.filter(
    movement_type='COMPRA',
    date__gte=datetime.date(2026, 7, 13)
)

print(f"Found {movements.count()} COMPRA movements to reconcile.")

reconciled_count = 0
for mov in movements:
    if mov.location and mov.product:
        inv, _ = Inventory.objects.get_or_create(location=mov.location, product=mov.product, defaults={'quantity': 0})
        inv.quantity += mov.quantity
        inv.save()
        reconciled_count += 1
        print(f"Added {mov.quantity} pieces to inventory at {mov.location.name} from COMPRA on {mov.date}.")

print(f"Successfully reconciled {reconciled_count} COMPRA movements.")
