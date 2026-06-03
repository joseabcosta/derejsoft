import os
import sys
import django

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'derejsoft.settings')
django.setup()

from core.models import Factura, CuentaPorCobrar

print("Iniciando sincronización de Cuentas por Cobrar...")
facturas = Factura.objects.all()
count = 0
for f in facturas:
    f.actualizar_cuenta_por_cobrar()
    count += 1

print(f"Sincronización completada. Se procesaron {count} facturas.")
print(f"Cuentas por cobrar en la base de datos: {CuentaPorCobrar.objects.count()}")
