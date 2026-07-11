import os
import sys
import django
import datetime

# Add project path dynamically
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huevoreal.settings')
django.setup()

from inventory.models import Inventory, InventoryMovement, Product

product = Product.objects.filter(is_active=True).first()

# Find all VENTA movements created for sales before July 8, 2026
movements = InventoryMovement.objects.filter(
    movement_type='VENTA',
    date__lt=datetime.date(2026, 7, 8),
    sale__isnull=False
)

print(f"Found {movements.count()} historical sale movements to revert.")

reverted_count = 0
for mov in movements:
    # Add back to Inventory
    inv, _ = Inventory.objects.get_or_create(location=mov.location, product=product, defaults={'quantity': 0})
    inv.quantity += mov.quantity
    inv.save()
    
    # Delete movement
    mov.delete()
    reverted_count += 1

print(f"Reverted {reverted_count} historical sales in inventory stock and deleted their movements.")
