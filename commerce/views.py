from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from commerce.mixins import SearchQuerysetMixin
from core.mixins import TitleContextMixin
from core.models import Brand, Category, Customer, Product
from core.utils import custom_serializer
from .forms import InvoiceForm
from .models import Invoice, InvoiceDetail, Purchase, PurchaseDetail 
from django.db.models import Q, F
from collections import defaultdict
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DetailView ,View, DeleteView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
from django.db import transaction
from django.template.loader import render_to_string 
import json

class InvoiceListView(LoginRequiredMixin,TitleContextMixin,ListView): 
    model = Invoice 
    template_name = 'invoice/list.html'  # Nombre del template a usar 
    context_object_name = 'invoices'     # Nombre del contexto a pasar al template 
    paginate_by = 10   
                
    title1 = "Autor | TeacherCode"
    title2 = "Listado de Ventas"

    def get_queryset(self):
        # Se Puede personalizar el queryset aquí si es necesario
        queryset = super().get_queryset()  # self.model.objects.all()
        query = self.request.GET.get('q','')
        if query:
            queryset = queryset.filter(Q(customer__last_name__icontains=query) | Q(customer__first_name__icontains=query))
        return queryset
    
   
class InvoiceCreateView(LoginRequiredMixin,TitleContextMixin,CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")  # Redirigir a la lista de proveedores después de crear uno nuevo
    title1 = '"Ventas"'
    title2 = 'Crear Nueva Venta'
          
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['products'] = Product.active_products.only('id','description','price','stock','iva')
        context['detail_sales'] =[]
        context['save_url'] = reverse_lazy('commerce:invoice_create') 
        context['invoice_list_url'] = self.success_url 
        print(context['products'])
        return context
    
    def post(self, request, *args, **kwargs):
        print("POST request received")
        form = self.get_form()
        print("request.POST:", request.POST)
        if not form.is_valid():
            # Return form errors as simple dict
            errors = {k: v for k, v in form.errors.items()}
            messages.error(self.request, f"Error al grabar la venta: {errors}")
            return JsonResponse({"msg": errors}, status=400)

        # Use cleaned_data to avoid KeyError / raw access problems
        data = form.cleaned_data
        try:
            with transaction.atomic():
                sale = Invoice.objects.create(
                    customer=data['customer'],
                    user=request.user,
                    payment_method=data['payment_method'],
                    issue_date=timezone.now(),
                    subtotal=data.get('subtotal') or Decimal('0.00'),
                    iva=data.get('iva') or Decimal('0.00'),
                    total=data.get('total') or Decimal('0.00')
                )

                # Parse detail JSON and create detail rows
                try:
                    details = json.loads(request.POST.get('detail', '[]'))
                except Exception as ex_det:
                    raise ValueError(f"Formato de detalle inválido: {ex_det}")

                for detail in details:
                    product_id = int(detail.get('id'))
                    quantify = Decimal(str(detail.get('quantify', '0')))
                    price = Decimal(str(detail.get('price', '0')))
                    iva_val = Decimal(str(detail.get('iva', '0')))
                    subtotal = Decimal(str(detail.get('sub', '0')))

                    inv_det = InvoiceDetail.objects.create(
                        invoice=sale,
                        product_id=product_id,
                        quantity=quantify,
                        price=price,
                        iva=iva_val,
                        subtotal=subtotal
                    )

                    # Update stock: convert quantity to int for IntegerField
                    try:
                        inv_det.product.reduce_stock(int(quantify))
                    except Exception as ex_stock:
                        # If stock update fails, raise to rollback transaction
                        raise

                messages.success(self.request, f"Éxito al registrar la venta F#{sale.id}")
                print_url = reverse('commerce:invoice_print', kwargs={'pk': sale.id})
                return JsonResponse({"msg": "Éxito al registrar la venta Factura", "print_url": print_url}, status=200)
        except Exception as ex:
            # Ensure exception is stringified for JSON
            return JsonResponse({"msg": str(ex)}, status=400)
    
class InvoiceUpdateView(LoginRequiredMixin,TitleContextMixin,UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoice/form.html"
    success_url = reverse_lazy("commerce:invoice_list")  # Redirigir a la lista de proveedores después de crear uno nuevo
    title1 = '"Venta"'
    title2 = 'Editar Venta'
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['products'] = Product.active_products.only('id','description','price','stock','iva')
        context['invoice_list_url'] = self.success_url 
        detail_sale =list(InvoiceDetail.objects.filter(invoice_id=self.object.id).values(
             "product","product__description","quantity","price","subtotal","iva"))
        print("detalle")
        detail_sale=json.dumps(detail_sale,default=custom_serializer)
        context['detail_sales']=detail_sale  #[{'id':1,'precio':2},{},{}]
        context['save_url'] = reverse_lazy('commerce:invoice_update',kwargs={"pk":self.object.id})
        print(detail_sale)
        return context
    
    def post(self, request, *args, **kwargs):
        print("POST request update")
        form = self.get_form()
        print(request.POST)
        if not form.is_valid():
            messages.success(self.request, f"Error al actualizar la venta!!!: {form.errors}.")
            return JsonResponse({"msg":form.errors},status=400)
        data = request.POST
        try:
            print("facturaId: ")
            print(self.kwargs.get('pk'))
            sale= Invoice.objects.get(id=self.kwargs.get('pk'))
           
            with transaction.atomic():
                sale.customer_id=int(data['customer'])
                sale.user=request.user
                sale.payment_method=data['payment_method']
                sale.issue_date = timezone.now() 
                sale.subtotal=Decimal(data['subtotal'])
                sale.iva= Decimal(data['iva'])
                sale.total=Decimal(data['total'])
                sale.save()

                # Parse incoming detail list
                try:
                    details = json.loads(request.POST.get('detail', '[]'))
                except Exception as ex_det:
                    raise ValueError(f"Formato de detalle inválido: {ex_det}")

                # Restore stock from existing details then delete them
                detdelete = InvoiceDetail.objects.filter(invoice_id=sale.id)
                for det in detdelete:
                    try:
                        det.product.stock += int(det.quantity)
                        det.product.save()
                    except Exception:
                        # ignore individual restore errors here; raising would rollback
                        pass
                detdelete.delete()

                for detail in details:
                    product_id = int(detail.get('id'))
                    quantify = Decimal(str(detail.get('quantify', '0')))
                    price = Decimal(str(detail.get('price', '0')))
                    iva_val = Decimal(str(detail.get('iva', '0')))
                    subtotal = Decimal(str(detail.get('sub', '0')))

                    inv_det = InvoiceDetail.objects.create(
                        invoice=sale,
                        product_id=product_id,
                        quantity=quantify,
                        price=price,
                        iva=iva_val,
                        subtotal=subtotal
                    )

                    inv_det.product.reduce_stock(int(quantify))

                messages.success(self.request, f"Éxito al Modificar la venta F#{sale.id}")
                print_url = reverse('commerce:invoice_print', kwargs={'pk': sale.id})
                return JsonResponse({"msg": "Éxito al Modificar la venta Factura", "print_url": print_url}, status=200)
        except Exception as ex:
            return JsonResponse({"msg": str(ex)}, status=400)


class InvoiceDetailView(LoginRequiredMixin, TitleContextMixin, DetailView):
    model = Invoice
    template_name = 'invoice/detail_modal.html'
    context_object_name = 'invoice'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['details'] = InvoiceDetail.objects.filter(invoice=self.object)
        html = render_to_string(self.template_name, context, request=request)
        return JsonResponse({'html': html})

class InvoiceDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice = Invoice.objects.get(pk=pk)

                # Devolver stock de productos
                details = InvoiceDetail.objects.filter(invoice=invoice)
                for d in details:
                    d.product.stock += d.quantity
                    d.product.save()
                details.delete()

                invoice.delete()
                return JsonResponse({'msg': f'✅ Factura N°{pk} eliminada correctamente.'}, status=200)
        except Invoice.DoesNotExist:
            return JsonResponse({'msg': '⚠️ Factura no encontrada.'}, status=404)
        except Exception as ex:
            return JsonResponse({'msg': f'❌ Error al eliminar: {ex}'}, status=400)


class InvoiceAnnulView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice = Invoice.objects.get(pk=pk)
                if not invoice.state:
                    return JsonResponse({'msg': '⚠️ La factura ya está anulada.'}, status=400)

                # Revertir stock
                details = InvoiceDetail.objects.filter(invoice=invoice)
                for d in details:
                    d.product.stock += d.quantity
                    d.product.save()

                invoice.state = False
                invoice.save(update_fields=['state'])

                return JsonResponse({'msg': f'🚫 Factura N°{pk} anulada correctamente.'}, status=200)
        except Invoice.DoesNotExist:
            return JsonResponse({'msg': '⚠️ Factura no encontrada.'}, status=404)
        except Exception as ex:
            return JsonResponse({'msg': f'❌ Error al anular: {ex}'}, status=400)
        
class CategoryListView(LoginRequiredMixin, TitleContextMixin, SearchQuerysetMixin, ListView):
    model = Category
    template_name = 'category/list.html'
    context_object_name = 'categories'
    paginate_by = 10
    search_fields = ['name']
    title1 = "Categorías"
    title2 = "Listado de Categorías"


class CategoryCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Category
    template_name = 'category/form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('commerce:category_list')
    title1 = "Categorías"
    title2 = "Registrar Nueva Categoría"


class CategoryUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Category
    template_name = 'category/form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('commerce:category_list')
    title1 = "Categorías"
    title2 = "Actualizar Categoría"


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('commerce:category_list')


class BrandListView(LoginRequiredMixin, TitleContextMixin, SearchQuerysetMixin, ListView):
    model = Brand
    template_name = 'brand/list.html'
    context_object_name = 'brands'
    paginate_by = 10
    search_fields = ['description'] 
    title1 = "Marcas"
    title2 = "Listado de Marcas"


class BrandCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Brand
    template_name = 'brand/form.html'
    fields = ['description']
    success_url = reverse_lazy('commerce:brand_list')
    title1 = "Marcas"
    title2 = "Registrar Nueva Marca"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class BrandUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Brand
    template_name = 'brand/form.html'
    fields = ['description']
    success_url = reverse_lazy('commerce:brand_list')
    title1 = "Marcas"
    title2 = "Actualizar Marca"


class BrandDeleteView(LoginRequiredMixin, DeleteView):
    model = Brand
    template_name = 'brand/delete.html'
    success_url = reverse_lazy('commerce:brand_list')
    title1 = "Marcas"
    title2 = "Eliminar Marca"



class ProductListView(LoginRequiredMixin, TitleContextMixin, SearchQuerysetMixin, ListView):
    model = Product
    template_name = 'product/list.html'
    context_object_name = 'products'
    paginate_by = 10
    search_fields = ['description']
    title1 = "Productos"
    title2 = "Listado de Productos"


class ProductCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Product
    template_name = 'product/form.html'
    # Use a custom ModelForm to control widgets and queryset for categories
    from core.forms import ProductForm
    form_class = ProductForm
    success_url = reverse_lazy('commerce:product_list')
    title1 = "Productos"
    title2 = "Registrar Nuevo Producto"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Product
    template_name = 'product/form.html'
    from core.forms import ProductForm
    form_class = ProductForm
    success_url = reverse_lazy('commerce:product_list')
    title1 = "Productos"
    title2 = "Actualizar Producto"


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('commerce:product_list')


class CustomerListView(LoginRequiredMixin, TitleContextMixin, SearchQuerysetMixin, ListView):
    model = Customer
    template_name = 'customer/list.html'
    context_object_name = 'customers'
    paginate_by = 10
    search_fields = ['first_name', 'last_name', 'dni']
    title1 = "Clientes"
    title2 = "Listado de Clientes"


class CustomerCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Customer
    template_name = 'customer/form.html'
    fields = ['first_name', 'last_name', 'dni', 'email', 'address', 'phone']
    success_url = reverse_lazy('commerce:customer_list')
    title1 = "Clientes"
    title2 = "Registrar Nuevo Cliente"


class CustomerUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    model = Customer
    template_name = 'customer/form.html'
    fields = ['first_name', 'last_name', 'dni', 'email', 'address', 'phone']
    success_url = reverse_lazy('commerce:customer_list')
    title1 = "Clientes"
    title2 = "Actualizar Cliente"


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('commerce:customer_list')


class PurchaseListView(LoginRequiredMixin, TitleContextMixin, SearchQuerysetMixin, ListView):
    model = Purchase
    template_name = 'purchase/list.html'
    context_object_name = 'purchases'
    paginate_by = 10
    search_fields = ['num_document', 'supplier__name']
    title1 = "Compras"
    title2 = "Listado de Compras"

    def get_queryset(self):
        """Filtrar sólo compras activas por defecto. Permitir búsqueda a través del mixin."""
        queryset = super().get_queryset()
        queryset = queryset.filter(active=True)
        return queryset

class PurchaseCreateView(LoginRequiredMixin, TitleContextMixin, CreateView):
    model = Purchase
    template_name = 'purchase/form.html'
    fields = ['supplier', 'num_document', 'subtotal', 'iva', 'total']  
    success_url = reverse_lazy('commerce:purchase_list')
    title1 = "Compras"
    title2 = "Registrar Nueva Compra"

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.issue_date = timezone.now()   
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.active_products.only('id', 'description', 'price', 'stock', 'iva')
        context['detail_sales'] = []
        context['save_url'] = reverse_lazy('commerce:purchase_create')
        context['purchase_list_url'] = self.success_url
        return context

    def post(self, request, *args, **kwargs):
        """Acepta POST normal (sin detalle) o POST con campo 'detail' (JSON) para crear detalles.
        Actualiza el stock incrementándolo por la cantidad comprada.
        """
        form = self.get_form()
        if not form.is_valid():
            errors = {k: v for k, v in form.errors.items()}
            return JsonResponse({"msg": errors}, status=400)

        data = form.cleaned_data
        try:
            # Parse details and validate before creating purchase
            try:
                details = json.loads(request.POST.get('detail', '[]'))
            except Exception as ex_det:
                return JsonResponse({"msg": f"Formato de detalle inválido: {ex_det}"}, status=400)

            if not details:
                return JsonResponse({"msg": "Debe agregar al menos un detalle de compra."}, status=400)

            # Validate structure and collect product ids
            product_ids = set()
            for d in details:
                try:
                    pid = int(d.get('id'))
                    qty = Decimal(str(d.get('quantify', '0')))
                    cost = Decimal(str(d.get('cost', '0')))
                except Exception:
                    return JsonResponse({"msg": "Detalle con formato inválido (id, quantify, cost)."}, status=400)
                if qty <= 0:
                    return JsonResponse({"msg": f"Cantidad inválida para el producto {pid}. Debe ser mayor a 0."}, status=400)
                if cost < 0:
                    return JsonResponse({"msg": f"Costo inválido para el producto {pid}."}, status=400)
                product_ids.add(pid)

            # Lock product rows to avoid race conditions
            with transaction.atomic():
                products_qs = Product.objects.select_for_update().filter(pk__in=product_ids)
                products = {p.id: p for p in products_qs}

                missing = [str(pid) for pid in product_ids if pid not in products]
                if missing:
                    return JsonResponse({"msg": f"Productos no encontrados: {', '.join(missing)}"}, status=404)

                purchase = Purchase.objects.create(
                    supplier=data['supplier'],
                    num_document=data.get('num_document'),
                    user=request.user,
                    issue_date=timezone.now(),
                    subtotal=data.get('subtotal') or Decimal('0.00'),
                    iva=data.get('iva') or Decimal('0.00'),
                    total=data.get('total') or Decimal('0.00')
                )

                # Create PurchaseDetail and update stock
                for detail in details:
                    product_id = int(detail.get('id'))
                    quantify = Decimal(str(detail.get('quantify', '0')))
                    cost = Decimal(str(detail.get('cost', '0')))
                    subtotal = Decimal(str(detail.get('sub', '0')))
                    iva_val = Decimal(str(detail.get('iva', '0')))

                    PurchaseDetail.objects.create(
                        purchase=purchase,
                        product_id=product_id,
                        quantify=quantify,
                        cost=cost,
                        subtotal=subtotal,
                        iva=iva_val
                    )

                    Product.objects.filter(pk=product_id).update(stock=F('stock') + int(quantify))

                return JsonResponse({"msg": "Compra registrada correctamente.", "id": purchase.id}, status=200)
        except Exception as ex:
            return JsonResponse({"msg": str(ex)}, status=400)


class PurchaseUpdateView(LoginRequiredMixin, TitleContextMixin, UpdateView):
    """Editar una compra simple (sin detalle en esta implementación).
    Si más adelante se quiere soporte de detalle via AJAX, se puede extender aquí.
    """
    model = Purchase
    template_name = 'purchase/form.html'
    fields = ['supplier', 'num_document', 'subtotal', 'iva', 'total']
    success_url = reverse_lazy('commerce:purchase_list')
    title1 = "Compras"
    title2 = "Actualizar Compra"

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Mantener issue_date del registro original o actualizar según política
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.active_products.only('id', 'description', 'price', 'stock', 'iva')
        detail_sale = list(PurchaseDetail.objects.filter(purchase_id=self.object.id).values(
            "product", "product__description", "quantify", "cost", "subtotal", "iva"
        ))
        context['detail_sales'] = json.dumps(detail_sale, default=custom_serializer)
        context['save_url'] = reverse_lazy('commerce:purchase_update', kwargs={"pk": self.object.id})
        context['purchase_list_url'] = self.success_url
        return context

    def post(self, request, *args, **kwargs):
        # If the request is not AJAX, delegate to the normal UpdateView implementation
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
            return super().post(request, *args, **kwargs)

        form = self.get_form()
        if not form.is_valid():
            return JsonResponse({"msg": form.errors}, status=400)

        try:
            purchase = self.get_object()

            # Parse and validate incoming details
            try:
                details = json.loads(request.POST.get('detail', '[]'))
            except Exception as ex_det:
                return JsonResponse({"msg": f"Formato de detalle inválido: {ex_det}"}, status=400)

            if not details:
                return JsonResponse({"msg": "Debe agregar al menos un detalle de compra."}, status=400)

            # Compute old quantities per product and new quantities per product
            old_q = defaultdict(int)
            old_details = PurchaseDetail.objects.filter(purchase_id=purchase.id)
            for od in old_details:
                old_q[od.product_id] += int(od.quantify)

            new_q = defaultdict(int)
            product_ids = set()
            for d in details:
                try:
                    pid = int(d.get('id'))
                    qty = int(Decimal(str(d.get('quantify', '0'))))
                except Exception:
                    return JsonResponse({"msg": "Detalle con formato inválido (id, quantify)."}, status=400)
                if qty <= 0:
                    return JsonResponse({"msg": f"Cantidad inválida para el producto {pid}."}, status=400)
                new_q[pid] += qty
                product_ids.add(pid)

            # Also include products that were in old details
            for pid in list(old_q.keys()):
                product_ids.add(pid)

            # Lock involved product rows
            with transaction.atomic():
                products_qs = Product.objects.select_for_update().filter(pk__in=product_ids)
                products = {p.id: p for p in products_qs}
                missing = [str(pid) for pid in product_ids if pid not in products]
                if missing:
                    return JsonResponse({"msg": f"Productos no encontrados: {', '.join(missing)}"}, status=404)

                # Check resulting stock won't be negative: new_stock = current_stock - old_q + new_q
                for pid in product_ids:
                    current = products[pid].stock
                    net = new_q.get(pid, 0) - old_q.get(pid, 0)
                    if current + net < 0:
                        return JsonResponse({"msg": f"No hay stock suficiente para el producto {pid} al aplicar los cambios."}, status=400)

                # Update purchase header
                purchase.supplier_id = int(request.POST.get('supplier'))
                purchase.num_document = request.POST.get('num_document')
                purchase.subtotal = Decimal(request.POST.get('subtotal') or '0')
                purchase.iva = Decimal(request.POST.get('iva') or '0')
                purchase.total = Decimal(request.POST.get('total') or '0')
                purchase.user = request.user
                purchase.issue_date = timezone.now()
                purchase.save()

                # Revert old stock effects (subtract old quantities)
                for pid, qty in old_q.items():
                    if qty:
                        Product.objects.filter(pk=pid).update(stock=F('stock') - qty)
                old_details.delete()

                # Create new details and apply stock increases
                for d in details:
                    pid = int(d.get('id'))
                    quantify = Decimal(str(d.get('quantify', '0')))
                    cost = Decimal(str(d.get('cost', '0')))
                    subtotal = Decimal(str(d.get('sub', '0')))
                    iva_val = Decimal(str(d.get('iva', '0')))

                    PurchaseDetail.objects.create(
                        purchase=purchase,
                        product_id=pid,
                        quantify=quantify,
                        cost=cost,
                        subtotal=subtotal,
                        iva=iva_val
                    )
                    Product.objects.filter(pk=pid).update(stock=F('stock') + int(quantify))

                return JsonResponse({"msg": "Compra actualizada correctamente.", "id": purchase.id}, status=200)
        except Exception as ex:
            return JsonResponse({"msg": str(ex)}, status=400)


class PurchaseDetailView(LoginRequiredMixin, TitleContextMixin, DetailView):
    model = Purchase
    template_name = 'purchase/detail_modal.html'
    context_object_name = 'purchase'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        # Intentar obtener detalles relacionados (si existen)
        context['details'] = PurchaseDetail.objects.filter(purchase=self.object)
        html = render_to_string(self.template_name, context, request=request)
        return JsonResponse({'html': html})


class PurchaseDeleteView(LoginRequiredMixin, View):
    """Eliminación lógica de la compra: marca como inactive (modelo usa `active`) y
    opcionalmente revierte stock si se desea. Aquí realizamos la desactivación y
    devolvemos JSON para compatibilidad con llamadas AJAX desde la lista.
    """
    def post(self, request, pk, *args, **kwargs):
        try:
            with transaction.atomic():
                purchase = Purchase.objects.get(pk=pk)

                # Si se desea revertir el stock (ej: la compra aumentó stock),
                # se puede restar la cantidad. Por ahora dejamos solo marca inactive.
                purchase.active = False
                purchase.save(update_fields=['active'])

                # If request is AJAX return JSON; otherwise redirect to list page
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'msg': f'✅ Compra N°{pk} desactivada correctamente.'}, status=200)
                else:
                    from django.shortcuts import redirect
                    return redirect('commerce:purchase_list')
        except Purchase.DoesNotExist:
            return JsonResponse({'msg': '⚠️ Compra no encontrada.'}, status=404)
        except Exception as ex:
            return JsonResponse({'msg': f'❌ Error al eliminar: {ex}'}, status=400)

    def get(self, request, pk, *args, **kwargs):
        """Renderiza una página de confirmación para eliminación cuando se accede por GET.
        Esto permite que enlaces tradicionales funcionen (no solo AJAX).
        """
        try:
            purchase = Purchase.objects.get(pk=pk)
            return render_to_string('purchase/delete.html', {'object': purchase}, request=request) if request.headers.get('x-requested-with') == 'XMLHttpRequest' else self.render_delete_page(request, purchase)
        except Purchase.DoesNotExist:
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound('Compra no encontrada')

    def render_delete_page(self, request, purchase):
        from django.shortcuts import render
        return render(request, 'purchase/delete.html', {'object': purchase})


class InvoicePrintView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoice/print.html'

    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        details = InvoiceDetail.objects.filter(invoice=invoice)
        # Render the invoice HTML
        html = render_to_string(self.template_name, {'invoice': invoice, 'details': details}, request=request)

        # Try to convert HTML to PDF using xhtml2pdf (if installed). If not available,
        # fallback to returning the printable HTML so the user can still print from browser.
        try:
            from xhtml2pdf import pisa
            import io

            result = io.BytesIO()
            # xhtml2pdf expects bytes (UTF-8)
            pdf = pisa.pisaDocument(io.BytesIO(html.encode('utf-8')), dest=result)
            if pdf.err:
                # On conversion error, return HTML so the user can still print
                return HttpResponse(html)

            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"factura_{invoice.id}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except ImportError:
            # xhtml2pdf not installed: return HTML (printable)
            return HttpResponse(html)
        except Exception:
            # Any other error during PDF generation: return HTML
            return HttpResponse(html)