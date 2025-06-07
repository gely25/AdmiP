from django import forms
from .models import Empleado, Rol, Cargo,  Departamento, TipoContrato, Prestamo
from django.forms import ModelForm, TextInput, EmailInput, NumberInput, Select,Textarea


#Crud Prestámo (Examén Práctico)

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = '__all__'
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'tipo_prestamo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_prestamo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'interes': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'monto_pagar': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'numero_cuotas': forms.NumberInput(attrs={'class': 'form-control'}),
            'cuota_mensual': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'saldo': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
        }
        
        
