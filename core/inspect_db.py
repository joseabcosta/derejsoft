import os
import sys
import django

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'derejsoft.settings')
django.setup()

from core.models import Cliente, Factura, CuentaPorCobrar, Pago, Proyecto, Software

try:
    print("Clientes:", Cliente.objects.count())
    print("Facturas:", Factura.objects.count())
    print("Cuentas por cobrar:", CuentaPorCobrar.objects.count())
    print("Pagos:", Pago.objects.count())
    print("Proyectos:", Proyecto.objects.count())
    print("Softwares:", Software.objects.count())
except Exception as e:
    print("Error querying database:", e)
