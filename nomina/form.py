from django import forms
from .models import Sobretiempo

class SobretiempoForm(forms.ModelForm):
    class Meta:
        model = Sobretiempo
        fields = ['empleado', 'total_horas', 'sueldo_mensual']  # ✔ sin fecha_registro
