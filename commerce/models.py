from django.db import models
from core.models import Customer, Product, Supplier
from django.utils import timezone
from django.contrib.auth.models import User
from core.constants import InvoicePaymentMethod

class Invoice(models.Model): 
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT,related_name='customer_invoices',verbose_name='Cliente')
    payment_method = models.CharField(verbose_name='Metodo de Pago',max_length=2,choices=InvoicePaymentMethod.choices,default=InvoicePaymentMethod.CASH)
    issue_date = models.DateTimeField(verbose_name='Fecha Emision',default=timezone.now)
    subtotal = models.DecimalField(verbose_name='Subtotal',default=0, max_digits=16, decimal_places=2)
    iva = models.DecimalField(verbose_name='Iva',default=0, max_digits=16, decimal_places=2)
    total = models.DecimalField(verbose_name='Total',default=0, max_digits=16, decimal_places=2)
    payment = models.DecimalField(verbose_name='Pago',default=0, max_digits=16, decimal_places=2)
    change = models.DecimalField(verbose_name='Cambio',default=0, max_digits=16, decimal_places=2)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.BooleanField('Activo', default = True)
 
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ('-issue_date','customer',)
        indexes = [
            models.Index(fields=['issue_date']),
            models.Index(fields=['customer']),  
        ]
        
    def __str__(self):
        return f"{self.id} - {self.customer}"


class InvoiceDetail(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,related_name='detail',verbose_name='Factura')
    product = models.ForeignKey(Product, on_delete=models.PROTECT,related_name='Product',verbose_name='Producto')
    cost = models.DecimalField(default=0, max_digits=16, decimal_places=2, null=True, blank=True)
    quantity = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    price = models.DecimalField(default=0, max_digits=16, decimal_places=2)
    subtotal = models.DecimalField(default=0, max_digits=16, decimal_places=2)
    iva = models.DecimalField(default=0, max_digits=10, decimal_places=2)

  
    class Meta:
        verbose_name = "Factura Detalle"
        verbose_name_plural = "Factura Detalles"
        ordering = ('id',)
        indexes = [models.Index(fields=['id']),]
    
        
    def __str__(self):
        return f"{self.product}"

class Purchase(models.Model):
    num_document = models.CharField(verbose_name='NumDocumento',max_length=50, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT,related_name='purchase_suppliers',verbose_name='Supplier')
    issue_date = models.DateTimeField(verbose_name='Fecha Emision',default=timezone.now,db_index=True)
    subtotal = models.DecimalField(verbose_name='Subtotal',default=0, max_digits=16, decimal_places=2)
    iva = models.DecimalField(verbose_name='Iva',default=0, max_digits=16, decimal_places=2)
    total = models.DecimalField(verbose_name='Total',default=0, max_digits=16, decimal_places=2)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(verbose_name='Activo',default=True)
   
    class Meta:
        verbose_name = 'Compras de Producto '
        verbose_name_plural = 'Compras de Productos'
        ordering = ('-issue_date',)

    def delete(self, *args, **kwargs):
        self.active = False
        self.save()
        
    def __str__(self):
        return "{} - {:%d-%m-%Y}".format(self.num_document,self.issue_date)



class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.PROTECT,related_name='purchase_detail',verbose_name='Compra')
    product = models.ForeignKey(Product, on_delete=models.PROTECT,related_name='purchase_products')
    quantify = models.DecimalField(verbose_name='Cantidad',default=0, max_digits=8, decimal_places=2)
    cost = models.DecimalField(verbose_name='Costo',default=0, max_digits=16, decimal_places=2)
    subtotal = models.DecimalField(verbose_name='subtototal',default=0, max_digits=16, decimal_places=2)
    iva = models.DecimalField(verbose_name='Iva',default=0, max_digits=16, decimal_places=2)
   
    class Meta:
        verbose_name = 'Detalle de Compra'
        verbose_name_plural = 'Detalles de la Compra'
        ordering = ('id',)

    def __str__(self):
        return "{} - {} ".format(self.purchase, self.product.description)
   