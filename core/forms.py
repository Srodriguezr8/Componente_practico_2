from django import forms
from django.forms import Select, SelectMultiple, NumberInput, TextInput, FileInput
from core.models import Supplier, Product, Category


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'ruc', 'address', 'phone', 'state']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'description', 'cost', 'price', 'stock', 'iva', 'expiration_date',
            'brand', 'supplier', 'categories', 'line', 'image', 'state'
        ]
        widgets = {
            'description': TextInput(attrs={'class': 'form-control'}),
            'cost': NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price': NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': NumberInput(attrs={'class': 'form-control'}),
            'brand': Select(attrs={'class': 'form-control'}),
            'supplier': Select(attrs={'class': 'form-control'}),
            'categories': SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
            'line': Select(attrs={'class': 'form-control'}),
            'image': FileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only active categories by default
        self.fields['categories'].queryset = Category.objects.filter(state=True).order_by('description')