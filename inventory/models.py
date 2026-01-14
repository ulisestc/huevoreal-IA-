from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"

    def __str__(self):
        return self.name

class Inventory(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Ubicación")
    quantity = models.IntegerField(default=0, verbose_name="Cantidad")

    class Meta:
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"

    def __str__(self):
        return f'{self.location.name}: {self.quantity}'

class InventoryMovement(models.Model):
    MOVEMENT_CHOICES = (
        ('PRODUCCION', 'Producción'),
        ('VENTA', 'Venta'),
        ('TRASPASO_ENTRADA', 'Traspaso (Entrada)'),
        ('TRASPASO_SALIDA', 'Traspaso (Salida)'),
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Ubicación")
    quantity = models.IntegerField(verbose_name="Cantidad")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES, verbose_name="Tipo de Movimiento")
    merma = models.IntegerField(default=0, verbose_name="Merma")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

    def __str__(self):
        return f'{self.date} - {self.location.name}: {self.quantity} ({self.get_movement_type_display()})'