# Proyecto VBC - Supermercado

Pequeña aplicación Django para facturación, inventario y compras.

Requisitos rápidos

- Python 3.11+ (se probó con 3.13 en el entorno local)
- Virtualenv recomendado

Instalación (Windows PowerShell)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

PDFs y conversión

La vista de impresión intenta convertir la plantilla a PDF usando `xhtml2pdf` (pisa). En muchos entornos esta conversión funciona, pero en Windows puede dar problemas por dependencias nativas (reportlab). Si la conversión falla, la vista devuelve HTML imprimible que puedes guardar como PDF usando la opción "Imprimir" del navegador.

Recomendaciones si quieres PDF automático estable:

- Instalar `wkhtmltopdf` y usar `pdfkit` (requiere instalar el binario wkhtmltopdf y configurar PATH).
- O usar `WeasyPrint` (requiere dependencias como Cairo/pango; instalación puede ser compleja en Windows).

Mejoras que implementé aquí

- UI de creación de facturas: errores inline, spinner en botón Guardar, prevención de envíos dobles.
- Redirección a la URL de impresión tras guardar (se abre en pestaña nueva y la página va a la lista de facturas).
- Plantilla `invoice/print.html` mejorada con diseño para impresión (logo, cabecera y totales).
- Página de inicio con panel de métricas (proveedores, clientes, productos, ventas, compras).

Siguientes pasos sugeridos

- Habilitar una solución PDF server-side estable (WeasyPrint o wkhtmltopdf) y ajustar la vista `InvoicePrintView`.
- Añadir tests automáticos para facturación y gestión de stock.
- Poner `SECRET_KEY` en variables de entorno para producción.

Si quieres que configure PDF automático con `wkhtmltopdf` (recomendado por estabilidad), puedo guiarte para instalar el binario y adaptar la vista a `pdfkit`.
