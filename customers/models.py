from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    address = models.CharField(max_length=255, verbose_name="Dirección")
    phone_number = models.CharField(max_length=20, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.name
