import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'derejsoft.settings')
django.setup()

from core.models import Factura

for f in Factura.objects.all():
    print(f"Factura #{f.numero} - Cliente: {f.cliente.nombre} - Total: RD$ {f.total} - Pagos: RD$ {f.pagos_totales()} - Saldo: RD$ {f.saldo_pendiente}")
