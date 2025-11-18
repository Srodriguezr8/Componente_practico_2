import json
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, View
from datetime import date

from .form import SobretiempoForm
from .models import (
    Empleado,
    TipoSobretiempo,
    Sobretiempo,
    SobretiempoDetalle,
)

# ==========================
#     LISTA
# ==========================
class SobretiempoListView(ListView):
    model = Sobretiempo
    template_name = "nomina/sobretiempo_list.html"
    context_object_name = "sobretiempos"
    paginate_by = 10

    def get_queryset(self):
        # Query optimizado y seguro
        return (
            Sobretiempo.objects
            .select_related('empleado')
            .prefetch_related('detalles', 'detalles__tipo_sobretiempo')
            .order_by('-fecha_registro')
        )


# ==========================
#     CREAR
# ==========================
class SobretiempoCreateView(CreateView):
    model = Sobretiempo
    form_class = SobretiempoForm
    template_name = 'nomina/sobretiempo_form.html'
    success_url = reverse_lazy('nomina:sobretiempo_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipos'] = TipoSobretiempo.objects.all()
        ctx['today'] = date.today()
        ctx['save_url'] = reverse_lazy('nomina:sobretiempo_create')
        ctx['list_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        form.instance.fecha_registro = date.today()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if not form.is_valid():
            return JsonResponse({'msg': form.errors}, status=400)

        try:
            detalles = json.loads(request.POST.get("detalle", "[]"))
            if not detalles:
                return JsonResponse({"msg": "Debe agregar al menos un detalle."}, status=400)

            with transaction.atomic():

                st = form.save()

                total_general = Decimal('0.00')

                for d in detalles:
                    tipo = TipoSobretiempo.objects.get(pk=int(d['tipo']))
                    horas = Decimal(str(d['horas']))

                    valor_hora = st.sueldo_mensual / st.total_horas
                    valor_calc = valor_hora * horas * tipo.factor
                    total_general += valor_calc

                    SobretiempoDetalle.objects.create(
                        sobretiempo=st,
                        tipo_sobretiempo=tipo,
                        numero_horas=horas,
                        valor_calculado=valor_calc,
                    )

                st.total_calculado = total_general
                st.save()

                return JsonResponse({"msg": "Sobretiempo registrado correctamente", "id": st.id}, status=200)

        except Exception as e:
            return JsonResponse({'msg': str(e)}, status=400)


# ==========================
#     DETALLE (MODAL)
# ==========================
class SobretiempoDetailView(DetailView):
    model = Sobretiempo
    template_name = 'nomina/sobretiempo_detail_modal.html'
    context_object_name = 'sobretiempo'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        detalles = self.object.detalles.all()
        context['detalles'] = detalles

        # Total de horas + horas extras
        total_horas_con_extra = self.object.total_horas + sum(d.numero_horas for d in detalles)
        context['total_horas_con_extra'] = total_horas_con_extra

        from django.template.loader import render_to_string
        html = render_to_string(self.template_name, context, request=request)

        return JsonResponse({'html': html})


# ==========================
#     ELIMINAR
# ==========================
class SobretiempoDeleteView(View):
    def post(self, request, pk):
        try:
            st = Sobretiempo.objects.get(pk=pk)
            st.delete()
            return JsonResponse({'msg': 'Registro eliminado correctamente.'})
        except Sobretiempo.DoesNotExist:
            return JsonResponse({'msg': 'No encontrado'}, status=404)
