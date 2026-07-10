from django.db import models
from django.conf import settings
from customers.models import Customer
from inventory.models import Location, Product
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
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto")
    sale_type = models.CharField(max_length=5, choices=SALE_TYPE_CHOICES, verbose_name="Tipo de Venta")
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cantidad (Kg)")
    quantity_piece = models.IntegerField(null=True, blank=True, verbose_name="Cantidad (Piezas)")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Unitario") # Price per Kg or Piece
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio de Costo") # Cost per unit at sale time
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

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    )
    SALE_TYPE_CHOICES = (
        ('KILO', 'Kilo'),
        ('PIEZA', 'Pieza'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Cliente")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, verbose_name="Ubicación")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto")
    sale_type = models.CharField(max_length=5, choices=SALE_TYPE_CHOICES, verbose_name="Tipo de Venta")
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cantidad (Kg)")
    quantity_piece = models.IntegerField(null=True, blank=True, verbose_name="Cantidad (Piezas)")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Unitario")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='EFECTIVO', verbose_name="Método de Pago")
    status = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='PENDIENTE', verbose_name="Estado")
    delivery_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Reparto")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Vendedor")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.id} - {self.customer}'

class RecurringOrder(models.Model):
    FREQUENCY_CHOICES = (
        ('SEMANAL', 'Semanal'),
        ('QUINCENAL', 'Quincenal'),
        ('MENSUAL', 'Mensual'),
    )
    DAY_OF_WEEK_CHOICES = (
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    )

    SALE_TYPE_CHOICES = (
        ('KILO', 'Kilo'),
        ('PIEZA', 'Pieza'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Cliente")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ubicación de Origen")
    sale_type = models.CharField(max_length=5, choices=SALE_TYPE_CHOICES, default='PIEZA', verbose_name="Tipo de Venta")
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cantidad (Kg)")
    quantity_piece = models.IntegerField(null=True, blank=True, verbose_name="Cantidad (Piezas)")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio Unitario")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total")
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='EFECTIVO', verbose_name="Método de Pago")
    
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, default='SEMANAL', verbose_name="Frecuencia")
    day_of_week = models.CharField(max_length=50, null=True, blank=True, verbose_name="Días de la Semana")
    day_of_month = models.IntegerField(null=True, blank=True, verbose_name="Día del Mes")
    last_generated_date = models.DateField(null=True, blank=True, verbose_name="Última Fecha Generada")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Pedido Recurrente"
        verbose_name_plural = "Pedidos Recurrentes"

    def __str__(self):
        qty = self.quantity_piece if self.sale_type == 'PIEZA' else self.quantity_kg
        unit = "pzas" if self.sale_type == 'PIEZA' else "kg"
        return f'Recurrente: {self.customer} - {self.product} ({qty} {unit})'

    def get_days_display(self):
        if not self.day_of_week:
            return "-"
        days_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        try:
            indices = [int(x.strip()) for x in str(self.day_of_week).split(',') if x.strip().isdigit()]
            return ", ".join([days_map[i] for i in indices if i in days_map])
        except Exception:
            return str(self.day_of_week)

