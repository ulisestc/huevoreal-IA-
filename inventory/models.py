from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Inventory(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.location.name}: {self.quantity}'

class InventoryMovement(models.Model):
    MOVEMENT_CHOICES = (
        ('PRODUCCION', 'Producción'),
        ('VENTA', 'Venta'),
        ('TRASPASO_ENTRADA', 'Traspaso (Entrada)'),
        ('TRASPASO_SALIDA', 'Traspaso (Salida)'),
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    merma = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.date} - {self.location.name}: {self.quantity} ({self.get_movement_type_display()})'
