from django.db import models
from django.conf import settings

class Fraccionamiento(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")

    class Meta:
        verbose_name = "Fraccionamiento"
        verbose_name_plural = "Fraccionamientos"
        ordering = ['name']

    def __str__(self):
        return self.name

class Zona(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['name']

    def __str__(self):
        return self.name

class Customer(models.Model):
    first_name = models.CharField(max_length=255, verbose_name="Nombre")
    last_name = models.CharField(max_length=255, verbose_name="Apellido", blank=True)
    address = models.CharField(max_length=255, verbose_name="Dirección")
    phone_number = models.CharField(max_length=20, verbose_name="Teléfono")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Vendedor")
    fraccionamiento = models.ForeignKey(Fraccionamiento, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fraccionamiento")
    zona = models.ForeignKey(Zona, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zona")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

