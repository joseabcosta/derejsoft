from django.urls import path

from .views import (
    abono_create,
    abono_list,
    abono_pdf,
    cliente_create,
    cliente_detail,
    cliente_edit,
    cliente_list,
    cuenta_por_cobrar_list,
    dashboard,
    factura_create,
    factura_detail,
    factura_list,
    factura_liquidar,
    factura_pdf,
    proyecto_create,
    proyecto_detail,
    proyecto_edit,
    proyecto_list,
    sistema_create,
    sistema_detail,
    sistema_edit,
    sistema_list,
)

urlpatterns = [
    # Dashboard
    path('', dashboard, name='dashboard'),

    # Clientes
    path('clientes/', cliente_list, name='cliente_list'),
    path('clientes/nuevo/', cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/', cliente_detail, name='cliente_detail'),
    path('clientes/<int:pk>/editar/', cliente_edit, name='cliente_edit'),

    # Inventario de Sistemas
    path('inventario/', sistema_list, name='sistema_list'),
    path('inventario/nuevo/', sistema_create, name='sistema_create'),
    path('inventario/<int:pk>/', sistema_detail, name='sistema_detail'),
    path('inventario/<int:pk>/editar/', sistema_edit, name='sistema_edit'),

    # Retrocompatibilidad para Proyectos
    path('proyectos/', proyecto_list, name='proyecto_list'),
    path('proyectos/nuevo/', proyecto_create, name='proyecto_create'),
    path('proyectos/<int:pk>/', proyecto_detail, name='proyecto_detail'),
    path('proyectos/<int:pk>/editar/', proyecto_edit, name='proyecto_edit'),

    # Facturas
    path('facturas/', factura_list, name='factura_list'),
    path('facturas/nuevo/', factura_create, name='factura_create'),
    path('facturas/<int:pk>/', factura_detail, name='factura_detail'),
    path('facturas/<int:pk>/pdf/', factura_pdf, name='factura_pdf'),

    # Cuentas por Cobrar
    path('cuentas/', cuenta_por_cobrar_list, name='cuenta_por_cobrar_list'),
    path('cuentas/<int:factura_pk>/abonar/', abono_create, name='abono_create'),
    path('cuentas/<int:factura_pk>/liquidar/', factura_liquidar, name='factura_liquidar'),
    path('abonos/', abono_list, name='abono_list'),
    path('abonos/<int:pk>/pdf/', abono_pdf, name='abono_pdf'),
]
