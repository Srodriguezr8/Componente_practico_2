from django.urls import path, include
from core import views
from django.contrib.auth import views as auth_views
from core.views import RegisterView, logout_view
 
app_name='core' # define un espacio de nombre para la aplicacion
urlpatterns = [
   #path('', views.home,name='home'),
   path('', views.HomeTemplateView.as_view(),name='home'),
   path('login/', auth_views.LoginView.as_view(template_name="login.html"), name='login'),
   path('logout/', logout_view, name='logout'),
   path('register/', RegisterView.as_view(), name='register'),
   path('supplier_list/', views.SupplierListView.as_view(),name='supplier_list'),
   path('supplier_create/', views.SupplierCreateView.as_view(),name='supplier_create'),
   path('supplier_update/<int:pk>/', views.SupplierUpdateView.as_view(),name='supplier_update'),
   path('supplier_detail/<int:pk>/', views.SupplierDetailView.as_view(),name='supplier_detail'),
   path('supplier_delete/<int:pk>/', views.SupplierDeleteView.as_view(),name='supplier_delete'),
   path('nomina/', include('nomina.urls')),
]