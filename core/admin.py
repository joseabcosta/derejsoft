from django.contrib import admin

from .models import (
    Abono,
    Caja,
    Cliente,
    CuentaPorCobrar,
    DetalleFactura,
    Factura,
    MovimientoCaja,
    Pago,
    SistemaSoftware,
)


admin.site.register(Cliente)
admin.site.register(SistemaSoftware)
admin.site.register(Factura)
admin.site.register(DetalleFactura)
admin.site.register(Pago)
admin.site.register(Abono)
admin.site.register(CuentaPorCobrar)
admin.site.register(Caja)
admin.site.register(MovimientoCaja)
