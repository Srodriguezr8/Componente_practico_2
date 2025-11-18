from django.urls import path
from commerce import views

app_name = 'commerce'

urlpatterns = [
    path('invoice_list/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoice_create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoice_update/<int:pk>/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoice_detail/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoice_annul/<int:pk>/', views.InvoiceAnnulView.as_view(), name='invoice_annul'),
    path('invoice_delete/<int:pk>/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoice_print/<int:pk>/', views.InvoicePrintView.as_view(), name='invoice_print'),
    path('category/', views.CategoryListView.as_view(), name='category_list'),
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/update/<int:pk>/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('category/delete/<int:pk>/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('brand/', views.BrandListView.as_view(), name='brand_list'),
    path('brand/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brand/update/<int:pk>/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('brand/delete/<int:pk>/', views.BrandDeleteView.as_view(), name='brand_delete'),
    path('product/', views.ProductListView.as_view(), name='product_list'),
    path('product/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('product/update/<int:pk>/', views.ProductUpdateView.as_view(), name='product_update'),
    path('product/delete/<int:pk>/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('customer/', views.CustomerListView.as_view(), name='customer_list'),
    path('customer/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customer/update/<int:pk>/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('customer/delete/<int:pk>/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('purchase/', views.PurchaseListView.as_view(), name='purchase_list'),
    path('purchase/create/', views.PurchaseCreateView.as_view(), name='purchase_create'),
    path('purchase/update/<int:pk>/', views.PurchaseUpdateView.as_view(), name='purchase_update'),
    path('purchase/detail/<int:pk>/', views.PurchaseDetailView.as_view(), name='purchase_detail'),
    path('purchase/delete/<int:pk>/', views.PurchaseDeleteView.as_view(), name='purchase_delete'),
]
