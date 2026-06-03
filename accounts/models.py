from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrador'
    MANAGER = 'MANAGER', 'Gerente'
    SELLER = 'SELLER', 'Vendedor'
    CASHIER = 'CASHIER', 'Cajero'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SELLER,
        verbose_name='Rol',
    )
    phone = models.CharField(max_length=30, blank=True, verbose_name='Teléfono')
    address = models.CharField(max_length=255, blank=True, verbose_name='Dirección')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_administrador(self):
        return self.role == Role.ADMIN

    @property
    def is_gerente(self):
        return self.role == Role.MANAGER

    @property
    def is_vendedor(self):
        return self.role == Role.SELLER

    @property
    def is_cajero(self):
        return self.role == Role.CASHIER
