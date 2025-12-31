from django.contrib import admin
from .models import Location, Inventory, InventoryMovement

admin.site.register(Location)
admin.site.register(Inventory)
admin.site.register(InventoryMovement)