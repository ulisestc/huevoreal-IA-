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

    day = models.DateField()
    day_of_week = models.CharField(max_length=10, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True) # Where stock is taken from
    sale_type = models.CharField(max_length=5, choices=SALE_TYPE_CHOICES)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity_piece = models.IntegerField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Price per Kg or Piece
    price = models.DecimalField(max_digits=10, decimal_places=2) # Total Price
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES)

    def save(self, *args, **kwargs):
        self.day_of_week = calendar.day_name[self.day.weekday()]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Venta a {self.customer} el {self.day}'
