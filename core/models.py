from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from core.utils import phone_validator
from core.constants import CustomerGender, ProductIva, ProductLine

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    ruc = models.CharField(max_length=13)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=10,validators=[phone_validator])
    user = models.ForeignKey(User,on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.BooleanField('Activo', default = True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
      
    def __str__(self):
        return f"{self.name} - {self.ruc}"
    
class Customer(models.Model): 
    dni = models.CharField(verbose_name='Dni',max_length=13, unique=True, blank=True, null=True)
    first_name = models.CharField(verbose_name='Nombres',max_length=50)
    last_name = models.CharField(verbose_name='Apellidos',max_length=50)
    address = models.TextField(verbose_name='Dirección',blank=True, null=True)
    gender = models.CharField(verbose_name='Sexo',max_length=1, choices=CustomerGender, default=CustomerGender.MALE)
    date_of_birth = models.DateField(verbose_name='Fecha Nacimiento',blank=True, null=True)
    phone = models.CharField(max_length=10,validators=[phone_validator])
    email = models.EmailField(verbose_name='Correo',max_length=100, blank=True, null=True)
    image = models.ImageField(verbose_name='Foto',upload_to='customers/',blank=True,null=True,default='customers/default.png')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.BooleanField(verbose_name='Activo', default = True)
 
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['last_name']
        indexes = [models.Index(fields=['last_name']),]

    def save(self, *args, **kwargs):
        if self.first_name:
            self.first_name = self.first_name.upper()
        if self.last_name:
            self.last_name = self.last_name.upper()
        super(Customer, self).save(*args, **kwargs)
    
    @property
    def get_full_name(self):
        return f"{self.last_name} {self.first_name}"
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
class ActiveBrandManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(state=True)
    
class Brand(models.Model):
    description = models.CharField('Articulo',max_length=100)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.BooleanField('Activo', default = True)

    objects = models.Manager()  # Manager predeterminado
    active_brands = ActiveBrandManager()  # Manager filtrado por state=True

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['description']
        indexes = [
            models.Index(fields=['description']),]
        
    def __str__(self):
        return self.description


class ActiveProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(state=True)
    
class Product(models.Model):
    description = models.CharField('Articulo',max_length=100)
    cost=models.DecimalField('Costo Producto',max_digits=10,decimal_places=2,default=Decimal('0.0'))
    price=models.DecimalField('Precio',max_digits=10,decimal_places=2,default=Decimal('0.0'))
    stock=models.IntegerField(default=100,help_text="Stock debe estar en 0 y 10000 unidades",verbose_name='Stock')
    iva = models.IntegerField(verbose_name='IVA', choices=ProductIva.choices, default=ProductIva.FIFTEEN)
    expiration_date = models.DateTimeField('Fecha Caducidad',default=timezone.now)
    brand = models.ForeignKey(Brand,on_delete=models.CASCADE,related_name='product',verbose_name='Marca')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='Proveedor')
    categories = models.ManyToManyField('Category',verbose_name='Categoria')
    line = models.CharField('Linea',max_length=2,choices=ProductLine.choices,default=ProductLine.COMISARIATO)
    image = models.ImageField(upload_to='products/',blank=True,null=True,default='products/default.png')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.BooleanField("Activo",default=True)

    objects = models.Manager()  # Manager predeterminado
    active_products = ActiveProductManager()  #
     
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['description']
        indexes = [models.Index(fields=['description']),]
           
    def __str__(self):
        return self.description
     
    @property
    def get_categories(self):
        return " - ".join([c.description for c in self.categories.all().order_by('description')])
    
    def reduce_stock(self,quantity):
        if quantity > self.stock:
            raise ValueError("No hay suficiente stock disponible.")
        self.stock -= quantity
        self.save()
        
    @staticmethod
    def update_stock(id, quantity):
        """Reduce the stock of product with given id by quantity using an F-expression.

        This avoids race conditions at the Python level and performs the decrement
        atomically at the DB side.
        """
        from django.db.models import F
        Product.objects.filter(pk=id).update(stock=F('stock') - quantity)
            
class Category(models.Model):
    description = models.CharField(verbose_name='Categoria',max_length=100)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.BooleanField('Activo', default = True)
 
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['description']
        indexes = [models.Index(fields=['description']),]
        
    def __str__(self):
        return self.description



    
