from django.db import models
from django.conf import settings

class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('ALIMENTO', 'Alimento'),
        ('MEDICAMENTO', 'Medicamento'),
        ('SUELDOS', 'Sueldos'),
        ('TRANSPORTE', 'Transporte'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('OTROS', 'Otros'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
    )

    description = models.CharField(max_length=255, verbose_name="Descripción")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    date = models.DateField(verbose_name="Fecha")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTROS', verbose_name="Categoría")
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='EFECTIVO', verbose_name="Método de Pago")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - ${self.amount}"