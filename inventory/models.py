import datetime
from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitud")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitud")

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del Proveedor")
    contact_name = models.CharField(max_length=255, blank=True, verbose_name="Nombre de Contacto")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Correo Electrónico")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.name

class Product(models.Model):
    CATEGORY_CHOICES = (
        ('HUEVO', 'Huevo'),
    )
    UNIT_CHOICES = (
        ('KILO', 'Kilo'),
        ('PIEZA', 'Pieza'),
    )
    name = models.CharField(max_length=255, verbose_name="Nombre del Producto")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='HUEVO', verbose_name="Categoría")
    unit_type = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KILO', verbose_name="Unidad de Medida")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio de Costo (Proveedor)")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio de Venta Sugerido")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        if self.supplier:
            return f"{self.name} ({self.supplier.name})"
        return f"{self.name} (Producción Propia)"

class Inventory(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Ubicación")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto", null=True, blank=True)
    quantity = models.IntegerField(default=0, verbose_name="Cantidad")

    class Meta:
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"
        unique_together = ('location', 'product')

    def __str__(self):
        prod_name = self.product.name if self.product else "Huevo Propio"
        return f'{self.location.name} - {prod_name}: {self.quantity}'

class InventoryMovement(models.Model):
    MOVEMENT_CHOICES = (
        ('PRODUCCION', 'Producción'),
        ('COMPRA', 'Compra a Proveedor (Entrada)'),
        ('VENTA', 'Venta'),
        ('TRASPASO_ENTRADA', 'Traspaso (Entrada)'),
        ('TRASPASO_SALIDA', 'Traspaso (Salida)'),
        ('CORRECCION', 'Corrección de Inventario'),
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Ubicación")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto", null=True, blank=True)
    quantity = models.IntegerField(verbose_name="Cantidad")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES, verbose_name="Tipo de Movimiento")
    merma = models.IntegerField(default=0, verbose_name="Merma")
    date = models.DateField(default=datetime.date.today, verbose_name="Fecha")
    sale = models.ForeignKey('sales.Sale', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Venta", related_name="inventory_movements")

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

    def __str__(self):
        prod_name = self.product.name if self.product else "Huevo Propio"
        return f'{self.date} - {self.location.name} ({prod_name}): {self.quantity} ({self.get_movement_type_display()})'