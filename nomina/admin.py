from django.contrib import admin
from .models import TipoSobretiempo, Empleado, Sobretiempo, SobretiempoDetalle

@admin.register(TipoSobretiempo)
class TipoSobretiempoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'factor')
    search_fields = ('codigo', 'descripcion')

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'sueldo')
    search_fields = ('nombres',)

class SobretiempoDetalleInline(admin.TabularInline):
    model = SobretiempoDetalle
    extra = 1

@admin.register(Sobretiempo)
class SobretiempoAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'fecha_registro', 'total_calculado')
    inlines = [SobretiempoDetalleInline]
