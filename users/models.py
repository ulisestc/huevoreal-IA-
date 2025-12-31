from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin Maestro'),
        ('VENDEDOR', 'Vendedor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)