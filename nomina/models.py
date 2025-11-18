from django.db import models

class TipoSobretiempo(models.Model):
    codigo = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=100)
    factor = models.DecimalField(max_digits=4, decimal_places=2)  # Ej: 1.50, 2.00

    def __str__(self):
        return self.descripcion

class Empleado(models.Model):
    nombres = models.CharField(max_length=100)
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombres

class Sobretiempo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_registro = models.DateField(auto_now_add=True)
    
    total_horas = models.PositiveIntegerField(default=240)  # Horas normales
    sueldo_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    
    total_calculado = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    def __str__(self):
        return f"Sobretiempo #{self.id} - {self.empleado}"

    @property
    def total_horas_con_extra(self):
        """Suma las horas normales más las horas extras de los detalles."""
        return self.total_horas + sum(d.numero_horas for d in self.detalles.all())


class SobretiempoDetalle(models.Model):
    sobretiempo = models.ForeignKey(Sobretiempo, related_name='detalles', on_delete=models.CASCADE)
    tipo_sobretiempo = models.ForeignKey(TipoSobretiempo, on_delete=models.CASCADE)

    numero_horas = models.DecimalField(max_digits=6, decimal_places=2)

    valor_calculado = models.DecimalField(max_digits=10, decimal_places=2, editable=False)


    def __str__(self):
        return f"Detalle ST {self.id} - {self.tipo_sobretiempo}"
