from django import forms

from commerce.models import Invoice
class InvoiceForm(forms.ModelForm):
    class Meta:
        model=Invoice
        fields = ['customer', 'payment_method', 'issue_date', 'subtotal', 'iva', 'total']
        widgets = {
            'customer': forms.Select(),
            'payment_method': forms.Select(),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'subtotal': forms.NumberInput(),
            'iva': forms.NumberInput(),
            'total': forms.NumberInput(),
           
        }