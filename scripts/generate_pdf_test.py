#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proy_vbc.settings')
sys.path.insert(0, BASE_DIR)

django.setup()

from django.contrib.auth.models import User
from commerce.models import Invoice
from core.models import Customer
from django.utils import timezone
from decimal import Decimal
from django.template.loader import render_to_string
import io

try:
    from xhtml2pdf import pisa
except Exception:
    pisa = None

# Crear/obtener usuario de prueba
u, created = User.objects.get_or_create(username='test_pdf', defaults={'email': 'test@example.com'})
if created:
    u.set_password('test')
    u.save()

# Crear/obtener cliente de prueba
cust, created_c = Customer.objects.get_or_create(
    dni='9999999999',
    defaults={
        'first_name': 'Test',
        'last_name': 'User',
        'phone': '0999999999',
        'user': u
    }
)

# Crear factura de prueba
inv = Invoice.objects.create(
    customer=cust,
    payment_method='EF',
    issue_date=timezone.now(),
    subtotal=Decimal('0.00'),
    iva=Decimal('0.00'),
    total=Decimal('0.00'),
    user=u
)

# Renderizar HTML de la plantilla
html = render_to_string('invoice/print.html', {'invoice': inv, 'details': []})

# Guardar HTML para verificación
out_html = os.path.join(BASE_DIR, 'out_invoice.html')
with open(out_html, 'w', encoding='utf-8') as f:
    f.write(html)
print('Wrote HTML to', out_html)

# Intentar generar PDF si pisa disponible
if pisa:
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode('utf-8')), dest=result)
    if pdf.err:
        print('xhtml2pdf reported errors while generating PDF')
    else:
        out_pdf = os.path.join(BASE_DIR, 'out_invoice.pdf')
        with open(out_pdf, 'wb') as f:
            f.write(result.getvalue())
        print('Generated PDF at', out_pdf)
else:
    print('xhtml2pdf not available; install it with: pip install xhtml2pdf')
