from django.db import models
from django.conf import settings
from customers.models import Customer
from inventory.models import Location
import calendar

class Sale(models.Model):
    SALE_TYPE_CHOICES = (
        ('KILO', 'Kilo'),
        ('PIEZA', 'Pieza'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
    )

    day = models.DateField(verbose_name="Día")
    day_of_week = models.CharField(max_length=10, blank=True, verbose_name="Día de la semana")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Cliente")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, verbose_name="Ubicación") # Where stock is taken from
    sale_type = models.CharField(max_length=5, choices=SALE_TYPE_CHOICES, verbose_name="Tipo de Venta")
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cantidad (Kg)")
    quantity_piece = models.IntegerField(null=True, blank=True, verbose_name="Cantidad (Piezas)")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Unitario") # Price per Kg or Piece
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total") # Total Price
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Pagado")
    is_paid = models.BooleanField(default=True, verbose_name="Pagado")
    payment_date = models.DateField(verbose_name="Fecha de Pago")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Vendedor")
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, verbose_name="Método de Pago")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def save(self, *args, **kwargs):
        if self.day:
            self.day_of_week = calendar.day_name[self.day.weekday()]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Venta a {self.customer} el {self.day}'

    @property
    def payment_status(self):
        if self.is_paid or self.amount_paid >= self.price:
            return 'PAGADO'
        elif self.amount_paid > 0:
            return 'PARCIAL'
        else:
            return 'PENDIENTE'
