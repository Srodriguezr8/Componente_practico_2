from django.urls import path
from . import views

app_name = 'nomina'

urlpatterns = [
    path('sobretiempos/', views.SobretiempoListView.as_view(), name='sobretiempo_list'),
    path('sobretiempos/crear/', views.SobretiempoCreateView.as_view(), name='sobretiempo_create'),
    path('sobretiempos/detalle/<int:pk>/', views.SobretiempoDetailView.as_view(), name='sobretiempo_detail'),
    path('sobretiempos/eliminar/<int:pk>/', views.SobretiempoDeleteView.as_view(), name='sobretiempo_delete'),
]
