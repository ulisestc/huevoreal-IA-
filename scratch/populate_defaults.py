import os
import sys
import django

# Add project path dynamically
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huevoreal.settings')
django.setup()

from inventory.models import Supplier, Product, Inventory, InventoryMovement
from sales.models import Sale, Order

# 1. Create default supplier
supplier, _ = Supplier.objects.get_or_create(
    name="Producción Propia",
    defaults={'contact_name': "Tío Paul", 'is_active': True}
)
print(f"Supplier: {supplier}")

# 2. Create default product
product, _ = Product.objects.get_or_create(
    name="Huevo Propio",
    defaults={
        'supplier': None, # None means own production
        'category': 'HUEVO',
        'unit_type': 'PIEZA',
        'cost_price': 0,
        'sale_price': 0,
        'is_active': True
    }
)
print(f"Product: {product}")

# 3. Associate existing Sales and Reconcile Inventory
sales_to_update = Sale.objects.filter(product__isnull=True)
print(f"Found {sales_to_update.count()} sales without product.")

sales_updated_count = 0
reconciled_count = 0

for sale in sales_to_update:
    sale.product = product
    sale.save()
    sales_updated_count += 1
    
    # Reconcile inventory for sales that missed inventory subtraction
    qty = sale.quantity_piece if sale.sale_type == 'PIEZA' else sale.quantity_kg
    if qty and qty > 0 and sale.location:
        has_movement = InventoryMovement.objects.filter(sale=sale, movement_type='VENTA').exists()
        if not has_movement:
            # Subtract from Inventory
            inv, _ = Inventory.objects.get_or_create(location=sale.location, product=product, defaults={'quantity': 0})
            inv.quantity -= qty
            inv.save()
            # Create movement
            InventoryMovement.objects.create(
                location=sale.location,
                product=product,
                quantity=qty,
                movement_type='VENTA',
                date=sale.day,
                sale=sale
            )
            reconciled_count += 1

print(f"Updated {sales_updated_count} existing sales.")
print(f"Reconciled {reconciled_count} sales in inventory stock and movements.")

# 4. Associate existing Orders
orders_updated = Order.objects.filter(product__isnull=True).update(product=product)
print(f"Updated {orders_updated} existing orders.")

# 5. Associate existing Inventory Movements
movements_updated = InventoryMovement.objects.filter(product__isnull=True).update(product=product)
print(f"Updated {movements_updated} existing inventory movements.")

# 6. Associate existing Inventory
for inv in Inventory.objects.filter(product__isnull=True):
    dup = Inventory.objects.filter(location=inv.location, product=product).first()
    if dup:
        dup.quantity += inv.quantity
        dup.save()
        inv.delete()
        print(f"Merged duplicate inventory for location {inv.location.name}")
    else:
        inv.product = product
        inv.save()
        print(f"Updated inventory for location {inv.location.name}")

print("Default data population completed successfully!")
