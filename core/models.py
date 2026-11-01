from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import F, Sum
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone


class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
    ]

    nombre = models.CharField(max_length=200, verbose_name='Nombre completo')
    cedula = models.CharField(max_length=30, unique=True, verbose_name='Cédula')
    direccion = models.CharField(max_length=255, verbose_name='Dirección')
    telefono_principal = models.CharField(max_length=30, verbose_name='Teléfono principal')
    telefono_secundario = models.CharField(max_length=30, blank=True, verbose_name='Teléfono secundario')
    correo = models.EmailField(verbose_name='Correo electrónico')
    fecha_registro = models.DateField(default=timezone.now, verbose_name='Fecha de registro')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVO', verbose_name='Estado')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-fecha_registro']

    def __str__(self):
        return self.nombre

    def total_deuda(self):
        deuda = self.cuentas_por_cobrar.aggregate(total=Sum('saldo_pendiente'))['total']
        return deuda or 0

    def pagos_realizados(self):
        return Pago.objects.filter(cliente=self).aggregate(total=Sum('monto_pagado'))['total'] or 0


class SistemaSoftware(models.Model):
    """Inventario de sistemas/productos de software ofrecidos."""
    CATEGORIAS = [
        ('FACTURACION', 'Sistema de facturación'),
        ('GESTION', 'Sistema de gestión'),
        ('CITAS', 'Sistema de citas'),
        ('TIENDA', 'Tienda virtual'),
        ('PRESTAMOS', 'Sistema de préstamos'),
        ('RESTAURANTES', 'Sistema de restaurantes'),
        ('PERSONALIZADO', 'Aplicación personalizada'),
    ]
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('DESARROLLO', 'En desarrollo'),
        ('DESCONTINUADO', 'Descontinuado'),
    ]

    nombre = models.CharField(max_length=180, verbose_name='Nombre del sistema')
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='PERSONALIZADO', verbose_name='Categoría')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    precio = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Precio (RD$)')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO', verbose_name='Estado')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sistema de Software'
        verbose_name_plural = 'Inventario de Sistemas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Factura(models.Model):
    CONDICION_CHOICES = [
        ('CONTADO', 'Al Contado'),
        ('CREDITO', 'A Crédito'),
    ]
    METODO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CHEQUE', 'Cheque'),
    ]

    # Cliente vinculado (solo para crédito) o nombre libre (contado)
    cliente = models.ForeignKey(Cliente, related_name='facturas', on_delete=models.CASCADE,
                                null=True, blank=True, verbose_name='Cliente (crédito)')
    nombre_cliente = models.CharField(max_length=200, blank=True, verbose_name='Nombre del cliente')

    numero = models.CharField(max_length=30, unique=True)
    fecha = models.DateField(default=timezone.now)
    concepto = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    condicion_pago = models.CharField(max_length=10, choices=CONDICION_CHOICES, default='CONTADO',
                                      verbose_name='Condición de pago')
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES, default='EFECTIVO',
                                   verbose_name='Método de pago')
    cuota_fija = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                     verbose_name='Monto de cuota fija (RD$)')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha']

    def get_nombre_cliente(self):
        """Retorna el nombre del cliente sin importar si es vínculo o texto."""
        if self.cliente:
            return self.cliente.nombre
        return self.nombre_cliente or '—'

    def save(self, *args, **kwargs):
        self.total = self.monto + self.impuestos
        if not self.numero:
            prefijo = 'INV'
            self.numero = f'{prefijo}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        super().save(*args, **kwargs)
        self.actualizar_cuenta_por_cobrar()

    def __str__(self):
        return self.numero

    def total_pagos_y_abonos(self):
        pagos = self.pagos.aggregate(total=Sum('monto_pagado'))['total'] or 0
        abonos = self.abonos.aggregate(total=Sum('monto'))['total'] or 0
        return pagos + abonos

    def pagos_totales(self):
        return self.pagos.aggregate(total=Sum('monto_pagado'))['total'] or 0

    @property
    def saldo_pendiente(self):
        return self.total - self.pagos_totales()

    def actualizar_cuenta_por_cobrar(self):
        CuentaPorCobrar = apps.get_model('core', 'CuentaPorCobrar')
        if self.is_active and self.condicion_pago == 'CREDITO' and self.cliente:
            total_abonado = self.total_pagos_y_abonos()
            cpc, created = CuentaPorCobrar.objects.get_or_create(
                factura=self,
                defaults={
                    'cliente': self.cliente,
                    'total_adeudado': self.total,
                    'monto_abonado': total_abonado,
                    'saldo_pendiente': max(self.total - total_abonado, 0)
                }
            )
            if not created:
                cpc.cliente = self.cliente
                cpc.total_adeudado = self.total
                cpc.monto_abonado = total_abonado
                cpc.save()
        else:
            CuentaPorCobrar.objects.filter(factura=self).delete()


class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, related_name='detalles', on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    class Meta:
        verbose_name = 'Detalle de factura'
        verbose_name_plural = 'Detalles de factura'

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.descripcion} ({self.factura.numero})'


class Pago(models.Model):
    METODO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
    ]

    factura = models.ForeignKey(Factura, related_name='pagos', on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, related_name='pagos', on_delete=models.CASCADE)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES, default='EFECTIVO')
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='pagos', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cliente.nombre} - {self.monto_pagado}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.factura.actualizar_cuenta_por_cobrar()

    def delete(self, *args, **kwargs):
        factura = self.factura
        super().delete(*args, **kwargs)
        factura.actualizar_cuenta_por_cobrar()


class Abono(models.Model):
    factura = models.ForeignKey(Factura, related_name='abonos', on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, related_name='abonos', on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comentario = models.CharField(max_length=255, blank=True, verbose_name='Comentario o Referencia')
    fecha = models.DateField(default=timezone.now, verbose_name='Fecha del pago')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='abonos', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Abono'
        verbose_name_plural = 'Abonos'
        ordering = ['-fecha']

    def __str__(self):
        return f'Abono RD$ {self.monto} - {self.factura.numero}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.factura.actualizar_cuenta_por_cobrar()

    def delete(self, *args, **kwargs):
        factura = self.factura
        super().delete(*args, **kwargs)
        factura.actualizar_cuenta_por_cobrar()


@receiver(post_delete, sender=Abono)
def on_abono_deleted(sender, instance, **kwargs):
    if instance.factura_id:
        try:
            instance.factura.actualizar_cuenta_por_cobrar()
        except Exception:
            pass


@receiver(post_delete, sender=Pago)
def on_pago_deleted(sender, instance, **kwargs):
    if instance.factura_id:
        try:
            instance.factura.actualizar_cuenta_por_cobrar()
        except Exception:
            pass


class CuentaPorCobrar(models.Model):
    cliente = models.ForeignKey(Cliente, related_name='cuentas_por_cobrar', on_delete=models.CASCADE)
    factura = models.ForeignKey(Factura, related_name='cuentas_por_cobrar', on_delete=models.CASCADE)
    total_adeudado = models.DecimalField(max_digits=12, decimal_places=2)
    monto_abonado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cuenta por cobrar'
        verbose_name_plural = 'Cuentas por cobrar'

    def save(self, *args, **kwargs):
        self.saldo_pendiente = max(self.total_adeudado - self.monto_abonado, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.cliente.nombre} - {self.factura.numero}'


class Caja(models.Model):
    fecha_apertura = models.DateField(default=timezone.now)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cajas', on_delete=models.SET_NULL, null=True)
    monto_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_cierre = models.DateField(null=True, blank=True)
    total_vendido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cobrado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transferencias = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_final = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'

    def __str__(self):
        return f'Caja {self.fecha_apertura} - {self.usuario}'


class MovimientoCaja(models.Model):
    caja = models.ForeignKey(Caja, related_name='movimientos', on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    tipo = models.CharField(max_length=20, choices=[('INGRESO', 'Ingreso'), ('EGRESO', 'Egreso')], default='INGRESO')
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='movimientos_caja',
                                on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Movimiento de caja'
        verbose_name_plural = 'Movimientos de caja'

    def __str__(self):
        return f'{self.tipo} {self.monto} - {self.caja}'
