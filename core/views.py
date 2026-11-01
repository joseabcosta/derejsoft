from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from .forms import AbonoForm, ClienteForm, FacturaForm, SistemaSoftwareForm
from .models import Abono, Cliente, CuentaPorCobrar, Factura, Pago, SistemaSoftware


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    today = date.today()
    ventas_dia = Factura.objects.filter(fecha=today, is_active=True).aggregate(total=Sum('total'))['total'] or 0
    ventas_mes = Factura.objects.filter(fecha__month=today.month, is_active=True).aggregate(total=Sum('total'))['total'] or 0
    ventas_ano = Factura.objects.filter(fecha__year=today.year, is_active=True).aggregate(total=Sum('total'))['total'] or 0
    total_clientes = Cliente.objects.count()
    total_sistemas = SistemaSoftware.objects.count()
    cuentas_por_cobrar = CuentaPorCobrar.objects.aggregate(total=Sum('saldo_pendiente'))['total'] or 0
    pagos_recibidos = Pago.objects.aggregate(total=Sum('monto_pagado'))['total'] or 0
    cuentas_por_cobrar_este_ano = CuentaPorCobrar.objects.filter(
        factura__fecha__year=today.year
    ).aggregate(total=Sum('saldo_pendiente'))['total'] or 0
    balance_general = max(ventas_ano - cuentas_por_cobrar_este_ano, 0)

    ventas_por_mes, ingresos_por_mes, clientes_nuevos, pagos_por_mes, meses = [], [], [], [], []
    for month in range(1, 13):
        meses.append(date(today.year, month, 1).strftime('%b'))
        ventas_por_mes.append(
            float(Factura.objects.filter(fecha__month=month, fecha__year=today.year, is_active=True)
                  .aggregate(total=Sum('total'))['total'] or 0)
        )
        ingresos_por_mes.append(
            float(Pago.objects.filter(fecha__month=month, fecha__year=today.year)
                  .aggregate(total=Sum('monto_pagado'))['total'] or 0)
        )
        clientes_nuevos.append(
            Cliente.objects.filter(fecha_registro__month=month, fecha_registro__year=today.year).count()
        )
        pagos_por_mes.append(
            Pago.objects.filter(fecha__month=month, fecha__year=today.year).count()
        )

    context = {
        'ventas_dia': ventas_dia,
        'ventas_mes': ventas_mes,
        'ventas_ano': ventas_ano,
        'total_clientes': total_clientes,
        'total_sistemas': total_sistemas,
        'total_proyectos': total_sistemas,
        'cuentas_por_cobrar': cuentas_por_cobrar,
        'pagos_recibidos': pagos_recibidos,
        'balance_general': balance_general,
        'meses': meses,
        'ventas_por_mes': ventas_por_mes,
        'ingresos_por_mes': ingresos_por_mes,
        'clientes_nuevos': clientes_nuevos,
        'pagos_por_mes': pagos_por_mes,
    }
    return render(request, 'core/dashboard.html', context)


# ─────────────────────────────────────────────
#  CLIENTES
# ─────────────────────────────────────────────

@login_required
def cliente_list(request):
    query = request.GET.get('q', '')
    clientes = Cliente.objects.all()
    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query) | Q(cedula__icontains=query) | Q(correo__icontains=query)
        )
    return render(request, 'core/cliente_list.html', {'clientes': clientes, 'query': query})


@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado exitosamente.')
            return redirect('cliente_list')
    else:
        form = ClienteForm()
    return render(request, 'core/cliente_form.html', {'form': form, 'titulo': 'Registrar Cliente', 'accion': 'Guardar'})


@login_required
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Información del cliente actualizada.')
            return redirect('cliente_detail', pk=pk)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'core/cliente_form.html', {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar: {cliente.nombre}',
        'accion': 'Actualizar',
    })


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    facturas = cliente.facturas.filter(is_active=True).order_by('-fecha')
    pagos = cliente.pagos.all().order_by('-fecha')
    abonos = Abono.objects.filter(cliente=cliente).order_by('-fecha')
    saldo_pendiente = cliente.total_deuda()
    return render(request, 'core/cliente_detail.html', {
        'cliente': cliente,
        'facturas': facturas,
        'pagos': pagos,
        'abonos': abonos,
        'saldo_pendiente': saldo_pendiente,
    })


# ─────────────────────────────────────────────
#  INVENTARIO DE SISTEMAS
# ─────────────────────────────────────────────

@login_required
def sistema_list(request):
    query = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    sistemas = SistemaSoftware.objects.all()
    if query:
        sistemas = sistemas.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )
    if categoria:
        sistemas = sistemas.filter(categoria=categoria.upper())
    total_valor = sistemas.aggregate(total=Sum('precio'))['total'] or 0
    return render(request, 'core/sistema_list.html', {
        'sistemas': sistemas,
        'query': query,
        'categoria': categoria,
        'total_valor': total_valor,
        'categorias': SistemaSoftware.CATEGORIAS,
    })


@login_required
def sistema_create(request):
    if request.method == 'POST':
        form = SistemaSoftwareForm(request.POST)
        if form.is_valid():
            sistema = form.save()
            messages.success(request, f'Sistema "{sistema.nombre}" registrado en inventario.')
            return redirect('sistema_list')
    else:
        form = SistemaSoftwareForm()
    return render(request, 'core/sistema_form.html', {
        'form': form,
        'titulo': 'Nuevo Sistema en Inventario',
        'accion': 'Registrar en Inventario',
    })


@login_required
def sistema_edit(request, pk):
    sistema = get_object_or_404(SistemaSoftware, pk=pk)
    if request.method == 'POST':
        form = SistemaSoftwareForm(request.POST, instance=sistema)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sistema "{sistema.nombre}" actualizado correctamente.')
            return redirect('sistema_list')
    else:
        form = SistemaSoftwareForm(instance=sistema)
    return render(request, 'core/sistema_form.html', {
        'form': form,
        'sistema': sistema,
        'titulo': f'Editar Sistema: {sistema.nombre}',
        'accion': 'Actualizar Sistema',
    })


@login_required
def sistema_detail(request, pk):
    sistema = get_object_or_404(SistemaSoftware, pk=pk)
    return render(request, 'core/sistema_detail.html', {'sistema': sistema})


# Alias para retrocompatibilidad
proyecto_list = sistema_list
proyecto_create = sistema_create
proyecto_edit = sistema_edit
proyecto_detail = sistema_detail


# ─────────────────────────────────────────────
#  FACTURAS
# ─────────────────────────────────────────────

@login_required
def factura_list(request):
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    condicion = request.GET.get('condicion', '')
    facturas = Factura.objects.select_related('cliente').all()
    if query:
        facturas = facturas.filter(
            Q(numero__icontains=query) |
            Q(cliente__nombre__icontains=query) |
            Q(nombre_cliente__icontains=query) |
            Q(concepto__icontains=query)
        )
    if estado == 'activa':
        facturas = facturas.filter(is_active=True)
    elif estado == 'anulada':
        facturas = facturas.filter(is_active=False)
    if condicion:
        facturas = facturas.filter(condicion_pago=condicion.upper())
    return render(request, 'core/factura_list.html', {
        'facturas': facturas,
        'query': query,
        'estado': estado,
        'condicion': condicion,
    })


@login_required
def factura_create(request):
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        if form.is_valid():
            factura = form.save(commit=False)
            factura.save()
            messages.success(request, f'Factura {factura.numero} generada exitosamente.')
            return redirect('factura_list')
    else:
        form = FacturaForm()
    
    # Pasamos los sistemas del inventario para que el usuario pueda auto-completar concepto/precio si desea
    sistemas = SistemaSoftware.objects.filter(estado='ACTIVO')
    return render(request, 'core/factura_form.html', {'form': form, 'sistemas': sistemas})


@login_required
def factura_detail(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    abonos = factura.abonos.all().order_by('-fecha')
    pagos = factura.pagos.all().order_by('-fecha')
    cpc = factura.cuentas_por_cobrar.first()
    return render(request, 'core/factura_detail.html', {
        'factura': factura,
        'abonos': abonos,
        'pagos': pagos,
        'cpc': cpc,
    })


@login_required
def factura_pdf(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    html_string = render_to_string('core/factura_pdf.html', {'factura': factura})
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero}.pdf"'
    html.write_pdf(target=response)
    return response


# ─────────────────────────────────────────────
#  CUENTAS POR COBRAR + ABONOS
# ─────────────────────────────────────────────

@login_required
def cuenta_por_cobrar_list(request):
    cuentas = CuentaPorCobrar.objects.select_related('cliente', 'factura').filter(
        saldo_pendiente__gt=0
    ).order_by('-factura__fecha')
    cuentas_pagadas = CuentaPorCobrar.objects.select_related('cliente', 'factura').filter(
        saldo_pendiente=0
    ).order_by('-factura__fecha')
    total_pendiente = cuentas.aggregate(total=Sum('saldo_pendiente'))['total'] or 0
    return render(request, 'core/cuentas_por_cobrar.html', {
        'cuentas': cuentas,
        'cuentas_pagadas': cuentas_pagadas,
        'total_pendiente': total_pendiente,
    })


@login_required
def abono_create(request, factura_pk):
    factura = get_object_or_404(Factura, pk=factura_pk)
    cpc = factura.cuentas_por_cobrar.first()

    liquidar = request.GET.get('liquidar') == '1'

    if request.method == 'POST':
        form = AbonoForm(request.POST)
        if form.is_valid():
            abono = form.save(commit=False)
            if liquidar:
                abono.monto = cpc.saldo_pendiente  # Bloquear el monto al saldo completo
            abono.factura = factura
            abono.cliente = factura.cliente
            abono.usuario = request.user
            abono.save()
            messages.success(request, f'Abono de RD$ {abono.monto} registrado correctamente.')
            return redirect('abono_pdf', pk=abono.pk)
    else:
        initial_monto = cpc.saldo_pendiente if cpc else 0
        if not liquidar and factura.cuota_fija and factura.cuota_fija > 0 and cpc:
            initial_monto = min(factura.cuota_fija, cpc.saldo_pendiente)
        form = AbonoForm(initial={'monto': initial_monto, 'fecha': timezone.now().date()})

    return render(request, 'core/abono_form.html', {
        'form': form,
        'factura': factura,
        'cpc': cpc,
        'is_liquidar': liquidar,
    })


@login_required
def factura_liquidar(request, factura_pk):
    """Redirige a la pantalla de abono para liquidar el saldo pendiente completo con opción a comentario."""
    from django.urls import reverse
    from django.http import HttpResponseRedirect
    url = reverse('abono_create', args=[factura_pk])
    return HttpResponseRedirect(f"{url}?liquidar=1")


@login_required
def abono_list(request):
    query = request.GET.get('q', '')
    abonos = Abono.objects.select_related('factura', 'cliente').all().order_by('-fecha')
    if query:
        abonos = abonos.filter(
            Q(factura__numero__icontains=query) | Q(cliente__nombre__icontains=query) | Q(comentario__icontains=query)
        )
    return render(request, 'core/abono_list.html', {'abonos': abonos, 'query': query})


@login_required
def abono_pdf(request, pk):
    abono = get_object_or_404(Abono, pk=pk)
    cpc = CuentaPorCobrar.objects.filter(factura=abono.factura).first()
    html_string = render_to_string('core/abono_pdf.html', {'abono': abono, 'cpc': cpc})
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_abono_{abono.pk}.pdf"'
    html.write_pdf(target=response)
    return response
