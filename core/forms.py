from django import forms
from .models import Abono, Cliente, Factura, Proyecto


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


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['cliente', 'software', 'nombre', 'descripcion', 'precio_total',
                  'fecha_contratacion', 'fecha_entrega_estimada', 'estado',
                  'porcentaje_anticipo', 'monto_anticipo']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'software': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proyecto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del proyecto'}),
            'precio_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'fecha_contratacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_entrega_estimada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'porcentaje_anticipo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'monto_anticipo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
        }


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'proyecto', 'numero', 'concepto', 'monto', 'impuestos',
                  'condicion_pago', 'metodo_pago', 'fecha']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: INV-2024-001 (opcional)'}),
            'concepto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del servicio facturado'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'impuestos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'condicion_pago': forms.Select(attrs={'class': 'form-control'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # numero es opcional en el formulario – el modelo lo genera automáticamente
        self.fields['numero'].required = False
        self.fields['proyecto'].queryset = Proyecto.objects.select_related('cliente').all()
        self.fields['proyecto'].empty_label = '— Sin proyecto asociado —'


class AbonoForm(forms.ModelForm):
    class Meta:
        model = Abono
        fields = ['monto']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
            }),
        }
        labels = {
            'monto': 'Monto del Abono (RD$)',
        }
