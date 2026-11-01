from django import forms
from django.utils import timezone

from .models import Abono, Cliente, Factura, SistemaSoftware


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'cedula', 'direccion', 'telefono_principal', 'telefono_secundario', 'correo', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula o RNC'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'telefono_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono principal'}),
            'telefono_secundario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono secundario'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }


class SistemaSoftwareForm(forms.ModelForm):
    class Meta:
        model = SistemaSoftware
        fields = ['nombre', 'categoria', 'precio', 'descripcion', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: DerejFact Pro'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                 'placeholder': 'Descripción del sistema (opcional)'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre del Sistema',
            'categoria': 'Categoría',
            'precio': 'Precio (RD$)',
            'descripcion': 'Descripción',
            'estado': 'Estado',
        }


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['condicion_pago', 'cliente', 'nombre_cliente', 'numero', 'concepto',
                  'monto', 'impuestos', 'cuota_fija', 'metodo_pago', 'fecha']
        widgets = {
            'condicion_pago': forms.Select(attrs={'class': 'form-control', 'id': 'id_condicion_pago'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control',
                                                      'placeholder': 'Nombre del cliente'}),
            'numero': forms.TextInput(attrs={'class': 'form-control',
                                             'placeholder': 'Ej: INV-2024-001 (opcional)'}),
            'concepto': forms.TextInput(attrs={'class': 'form-control',
                                               'placeholder': 'Descripción del servicio facturado'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'impuestos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'cuota_fija': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'nombre_cliente': 'Nombre del cliente',
            'cliente': 'Cliente registrado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero'].required = False
        self.fields['cliente'].required = False
        self.fields['nombre_cliente'].required = False
        self.fields['cuota_fija'].required = False
        self.fields['cliente'].empty_label = '— Seleccione un cliente —'

    def clean(self):
        cleaned_data = super().clean()
        condicion = cleaned_data.get('condicion_pago')
        cliente = cleaned_data.get('cliente')
        nombre_cliente = cleaned_data.get('nombre_cliente', '').strip()

        if not cleaned_data.get('cuota_fija'):
            cleaned_data['cuota_fija'] = 0

        if condicion == 'CREDITO' and not cliente:
            self.add_error('cliente', 'Para ventas a crédito debe seleccionar un cliente registrado.')
        if condicion == 'CONTADO' and not nombre_cliente:
            self.add_error('nombre_cliente', 'Ingrese el nombre del cliente para ventas al contado.')
        return cleaned_data


class AbonoForm(forms.ModelForm):
    class Meta:
        model = Abono
        fields = ['monto', 'fecha', 'comentario']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'comentario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Pago mes de Junio',
            }),
        }
        labels = {
            'monto': 'Monto del Abono (RD$)',
            'fecha': 'Fecha del pago',
            'comentario': 'Comentario o Referencia',
        }
