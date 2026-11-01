from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core.models import (
    Abono, Cliente, CuentaPorCobrar, Factura, Pago, SistemaSoftware
)

User = get_user_model()


class ClienteModelTest(TestCase):
    """Tests para verificar el modelo de Cliente."""

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre='Juan Perez',
            cedula='001-0000000-1',
            direccion='Calle 1, Santo Domingo',
            telefono_principal='809-000-0001',
            correo='juan@test.com',
        )

    def test_cliente_str(self):
        self.assertEqual(str(self.cliente), 'Juan Perez')

    def test_cliente_sin_deuda_inicial(self):
        self.assertEqual(self.cliente.total_deuda(), 0)


class FacturaYCuentaPorCobrarTest(TestCase):
    """
    Tests críticos para verificar que al crear una Factura
    se genera automáticamente la CuentaPorCobrar correspondiente,
    y que ésta se actualiza correctamente al registrar pagos.
    """

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre='Maria Gomez',
            cedula='002-0000000-2',
            direccion='Calle 2, Santiago',
            telefono_principal='809-000-0002',
            correo='maria@test.com',
        )
        self.user = User.objects.create_user(
            username='admin_test',
            password='admin1234'
        )

    def test_factura_crea_cuenta_por_cobrar_automaticamente(self):
        """Al guardar una factura activa, debe crearse una CuentaPorCobrar."""
        factura = Factura.objects.create(
            cliente=self.cliente,
            numero='INV-TEST-001',
            concepto='Licencia de software',
            monto=Decimal('10000.00'),
            impuestos=Decimal('1800.00'),
            condicion_pago='CREDITO',
        )
        self.assertEqual(factura.total, Decimal('11800.00'))
        cpc = CuentaPorCobrar.objects.filter(factura=factura).first()
        self.assertIsNotNone(cpc, "Debe existir una CuentaPorCobrar para la factura")
        self.assertEqual(cpc.total_adeudado, Decimal('11800.00'))
        self.assertEqual(cpc.monto_abonado, Decimal('0.00'))
        self.assertEqual(cpc.saldo_pendiente, Decimal('11800.00'))

    def test_pago_actualiza_cuenta_por_cobrar(self):
        """Al registrar un pago, el saldo pendiente debe reducirse correctamente."""
        factura = Factura.objects.create(
            cliente=self.cliente,
            numero='INV-TEST-002',
            concepto='Desarrollo web personalizado',
            monto=Decimal('20000.00'),
            impuestos=Decimal('3600.00'),
            condicion_pago='CREDITO',
        )
        # Saldo inicial debe ser 23600
        cpc = CuentaPorCobrar.objects.get(factura=factura)
        self.assertEqual(cpc.saldo_pendiente, Decimal('23600.00'))

        # Registrar un primer pago de RD$ 10,000
        Pago.objects.create(
            factura=factura,
            cliente=self.cliente,
            monto_pagado=Decimal('10000.00'),
            metodo='EFECTIVO',
            usuario=self.user,
        )
        cpc.refresh_from_db()
        self.assertEqual(cpc.monto_abonado, Decimal('10000.00'))
        self.assertEqual(cpc.saldo_pendiente, Decimal('13600.00'))

    def test_multiples_pagos_no_duplican_cuenta(self):
        """Múltiples pagos deben acumularse correctamente sin duplicar la cuenta."""
        factura = Factura.objects.create(
            cliente=self.cliente,
            numero='INV-TEST-003',
            concepto='Sistema ERP',
            monto=Decimal('50000.00'),
            impuestos=Decimal('0.00'),
            condicion_pago='CREDITO',
        )

        # 3 pagos parciales
        for monto in [Decimal('10000'), Decimal('15000'), Decimal('5000')]:
            Pago.objects.create(
                factura=factura,
                cliente=self.cliente,
                monto_pagado=monto,
                metodo='TRANSFERENCIA',
                usuario=self.user,
            )

        cpc = CuentaPorCobrar.objects.filter(factura=factura)
        # No debe haber duplicados – solo un registro CPC por factura
        self.assertEqual(cpc.count(), 1, "Solo debe existir 1 CuentaPorCobrar por factura")

        cpc = cpc.first()
        self.assertEqual(cpc.monto_abonado, Decimal('30000.00'))
        self.assertEqual(cpc.saldo_pendiente, Decimal('20000.00'))

    def test_factura_inactiva_elimina_cuenta_por_cobrar(self):
        """Al anular una factura (is_active=False), debe eliminarse la CuentaPorCobrar."""
        factura = Factura.objects.create(
            cliente=self.cliente,
            numero='INV-TEST-004',
            concepto='Anulación test',
            monto=Decimal('5000.00'),
            impuestos=Decimal('900.00'),
            condicion_pago='CREDITO',
        )
        self.assertEqual(CuentaPorCobrar.objects.filter(factura=factura).count(), 1)

        factura.is_active = False
        factura.save()

        self.assertEqual(
            CuentaPorCobrar.objects.filter(factura=factura).count(),
            0,
            "La CuentaPorCobrar debe eliminarse cuando la factura se anula"
        )

    def test_abono_actualiza_cuenta_por_cobrar(self):
        """Los abonos también deben actualizar el saldo de CuentaPorCobrar."""
        factura = Factura.objects.create(
            cliente=self.cliente,
            numero='INV-TEST-005',
            concepto='Abono test',
            monto=Decimal('15000.00'),
            impuestos=Decimal('2700.00'),
            condicion_pago='CREDITO',
        )
        Abono.objects.create(
            factura=factura,
            cliente=self.cliente,
            monto=Decimal('7000.00'),
            usuario=self.user,
        )
        cpc = CuentaPorCobrar.objects.get(factura=factura)
        self.assertEqual(cpc.monto_abonado, Decimal('7000.00'))
        self.assertEqual(cpc.saldo_pendiente, Decimal('10700.00'))


class ViewsAuthTest(TestCase):
    """Tests de las vistas principales con autenticación."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.cliente_obj = Cliente.objects.create(
            nombre='Cliente Test',
            cedula='003-0000000-3',
            direccion='Calle 3',
            telefono_principal='809-000-0003',
            correo='test@test.com',
        )

    def test_redirige_a_login_si_no_autenticado(self):
        """Vistas protegidas deben redirigir al login."""
        urls = [
            reverse('dashboard'),
            reverse('cliente_list'),
            reverse('cliente_create'),
            reverse('factura_list'),
            reverse('factura_create'),
            reverse('cuenta_por_cobrar_list'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"URL {url} debe redirigir al login")
            self.assertIn('login', response.url)

    def test_dashboard_carga_correctamente(self):
        """El dashboard debe renderizarse con status 200 cuando autenticado."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    def test_cliente_list_con_datos(self):
        """La lista de clientes debe mostrar los clientes existentes."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cliente_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test')

    def test_cliente_create_post_valido(self):
        """Crear un cliente válido via POST debe redirigir a la lista."""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'nombre': 'Nuevo Cliente',
            'cedula': '004-0000000-4',
            'direccion': 'Calle 4',
            'telefono_principal': '809-000-0004',
            'telefono_secundario': '',
            'correo': 'nuevo@test.com',
            'estado': 'ACTIVO',
        }
        response = self.client.post(reverse('cliente_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cliente.objects.filter(cedula='004-0000000-4').exists())

    def test_cliente_detail_existe(self):
        """La ficha del cliente debe cargarse correctamente."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cliente_detail', kwargs={'pk': self.cliente_obj.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test')

    def test_factura_create_post_valido(self):
        """Crear una factura válida debe crear también una CuentaPorCobrar."""
        self.client.login(username='testuser', password='testpass123')
        initial_count = CuentaPorCobrar.objects.count()
        data = {
            'cliente': self.cliente_obj.pk,
            'concepto': 'Servicio de desarrollo',
            'monto': '25000',
            'impuestos': '4500',
            'condicion_pago': 'CREDITO',
            'metodo_pago': 'EFECTIVO',
            'cuota_fija': '0',
            'fecha': date.today().strftime('%Y-%m-%d'),
        }
        response = self.client.post(reverse('factura_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CuentaPorCobrar.objects.count(), initial_count + 1)

    def test_cuenta_por_cobrar_list_carga(self):
        """La lista de cuentas por cobrar debe cargar correctamente."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cuenta_por_cobrar_list'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_carga(self):
        """La página de login debe cargarse sin autenticación."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_credenciales_invalidas(self):
        """Login con credenciales incorrectas debe fallar."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Permanece en el login
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_credenciales_validas(self):
        """Login con credenciales correctas debe redirigir al dashboard."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_busqueda_clientes(self):
        """La búsqueda de clientes debe filtrar correctamente."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cliente_list') + '?q=Cliente Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test')

    def test_busqueda_clientes_sin_resultados(self):
        """Búsqueda sin resultados debe mostrar el mensaje de vacío."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cliente_list') + '?q=INEXISTENTE_XYZ')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontraron clientes')

    def test_factura_contado_solo_nombre_cliente(self):
        """Venta al contado no requiere cliente registrado, solo nombre."""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'nombre_cliente': 'Cliente Casual SRL',
            'concepto': 'Software de Facturación Express',
            'monto': '15000',
            'impuestos': '0',
            'condicion_pago': 'CONTADO',
            'metodo_pago': 'TRANSFERENCIA',
            'fecha': date.today().strftime('%Y-%m-%d'),
        }
        response = self.client.post(reverse('factura_create'), data)
        self.assertEqual(response.status_code, 302)
        factura = Factura.objects.filter(nombre_cliente='Cliente Casual SRL').first()
        self.assertIsNotNone(factura)
        self.assertEqual(factura.get_nombre_cliente(), 'Cliente Casual SRL')
        self.assertIsNone(factura.cliente)
        # Al ser al contado, no debe generar cuenta por cobrar
        self.assertEqual(CuentaPorCobrar.objects.filter(factura=factura).count(), 0)

    def test_sistema_software_inventario(self):
        """Prueba de creación y listado de sistemas en inventario."""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'nombre': 'Sistema Clínico Premium',
            'categoria': 'GESTION',
            'precio': '45000',
            'descripcion': 'Gestión de pacientes y citas',
            'estado': 'ACTIVO',
        }
        response = self.client.post(reverse('sistema_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SistemaSoftware.objects.filter(nombre='Sistema Clínico Premium').exists())

        response = self.client.get(reverse('sistema_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sistema Clínico Premium')
        self.assertContains(response, '45,000')
