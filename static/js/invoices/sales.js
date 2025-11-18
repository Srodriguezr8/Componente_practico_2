// static/js/SaleManager.js
document.addEventListener('DOMContentLoaded', () => new SaleManager());

class SaleManager {
  constructor() {
    // --- Referencias DOM ---
    this.d = document;
    this.detailSale = [];

    this.$customer = this.d.getElementById("id_customer");
    this.$payment = this.d.getElementById("id_payment_method");
    this.$product = this.d.getElementById("product");
    this.$btnAdd = this.d.getElementById("btnAdd");
    this.$form = this.d.getElementById("frmSale");
    this.$detailBody = this.d.getElementById("detalle");

    this.$btnSubmit = this.d.getElementById('btnSubmit');
    this.$btnSpinner = this.d.getElementById('btnSpinner');
    this.$formErrors = this.d.getElementById('formErrors');

    this.subtotalInput = this.d.getElementById("id_subtotal");
    this.ivaInput = this.d.getElementById("id_iva");
    this.totalInput = this.d.getElementById("id_total");

    // --- Config inicial ---
    try { this.$customer.selectedIndex = 1; } catch(e){}
    try { this.$payment.selectedIndex = 0; } catch(e){}

    // --- Eventos ---
    this.initEvents();

    // --- Si hay detalles previos cargados ---
    if (typeof detail_sales !== 'undefined' && detail_sales.length > 0) {
      this.detailSale = detail_sales.map(item => ({
        id: item.product,
        description: item.product__description,
        price: parseFloat(item.price),
        quantify: parseFloat(item.quantity),
        iva: parseFloat(item.iva),
        sub: parseFloat(item.subtotal)
      }));
      this.renderDetail();
      this.updateTotals();
    }
  }

  // ---------------- Eventos ----------------
  initEvents() {
    if (this.$product) this.$product.addEventListener('change', e => this.onProductChange(e));
    if (this.$btnAdd) this.$btnAdd.addEventListener('click', () => this.addProduct());
    if (this.$detailBody) this.$detailBody.addEventListener('click', e => this.removeProduct(e));
    if (this.$form) this.$form.addEventListener('submit', e => this.submitForm(e));

    // Llamar una vez para inicializar
    if (this.$product) this.onProductChange({ target: this.$product });
  }

  // ---------------- Métodos principales ----------------
  onProductChange(e) {
    const option = e.target.selectedOptions ? e.target.selectedOptions[0] : null;
    if (!option) return;
    const priceEl = this.d.getElementById('price');
    const ivaEl = this.d.getElementById('iva');
    if (priceEl) priceEl.value = option.dataset.price || 0;
    if (ivaEl) ivaEl.value = option.dataset.iva || 0;
  }

  addProduct() {
    const selected = this.$product ? this.$product.options[this.$product.selectedIndex] : null;
    if (!selected || !selected.value) return this.showFormError("Seleccione un producto");

    const stock = parseInt(selected.dataset.stock || 0);
    const quantify = parseInt(this.d.getElementById('quantify').value || 0);
    if (quantify <= 0 || quantify > stock) {
      return this.showFormError(`Cantidad inválida o mayor al stock disponible (${stock}).`);
    }

    const id = parseInt(selected.value);
    const description = selected.text;
    const price = parseFloat(selected.dataset.price);
    const iva = parseFloat(selected.dataset.iva);
    this.calculateProduct(id, description, iva, price, quantify);
  }

  calculateProduct(id, description, iva, price, quantify) {
    const existing = this.detailSale.find(p => p.id === id);
    if (existing && !confirm(`"${description}" ya está agregado. ¿Desea actualizar la cantidad?`)) return;

    if (existing) {
      quantify += existing.quantify;
      this.detailSale = this.detailSale.filter(p => p.id !== id);
    }

    const ivaValue = iva > 0 ? (price * quantify * (iva / 100)) : 0;
    let sub = price * quantify + ivaValue;
    this.detailSale.push({ id, description, price, quantify, iva: ivaValue, sub });
    this.renderDetail();
    this.updateTotals();
  }

  renderDetail() {
    if (!this.$detailBody) return;
    this.$detailBody.innerHTML = this.detailSale.map(prod => `
      <tr>
        <td>${prod.id}</td>
        <td>${prod.description}</td>
        <td>${prod.price.toFixed(2)}</td>
        <td>${prod.quantify}</td>
        <td>${prod.iva.toFixed(2)}</td>
        <td>${prod.sub.toFixed(2)}</td>
        <td class="text-center">
          <button class="text-danger" data-id="${prod.id}" rel="rel-delete">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>`).join('');
  }

  removeProduct(e) {
    const btn = e.target.closest && e.target.closest('button[rel=rel-delete]');
    if (!btn) return;
    const id = parseInt(btn.dataset.id);
    this.detailSale = this.detailSale.filter(p => p.id !== id);
    this.renderDetail();
    this.updateTotals();
  }

  updateTotals() {
    const totals = this.detailSale.reduce((acc, p) => {
      acc.iva += p.iva;
      acc.sub += p.sub;
      return acc;
    }, { iva: 0, sub: 0 });

    if (this.subtotalInput) this.subtotalInput.value = (totals.sub - totals.iva).toFixed(2);
    if (this.ivaInput) this.ivaInput.value = totals.iva.toFixed(2);
    if (this.totalInput) this.totalInput.value = totals.sub.toFixed(2);
  }

  async submitForm(e) {
    e.preventDefault();
    if (!this.totalInput || parseFloat(this.totalInput.value) <= 0) {
      this.showFormError('Debe agregar productos antes de guardar la venta.');
      return;
    }
    await this.saveSale(save_url, invoice_list_url);
  }

  async saveSale(urlPost, urlSuccess) {
    const formData = new FormData(this.$form);
    formData.append("detail", JSON.stringify(this.detailSale));

    const csrfEl = this.d.querySelector('[name=csrfmiddlewaretoken]');
    const csrf = csrfEl ? csrfEl.value : '';

    // Disable submit and show spinner
    if (this.$btnSubmit) this.$btnSubmit.disabled = true;
    if (this.$btnSpinner) this.$btnSpinner.classList.remove('d-none');
    if (this.$formErrors) this.$formErrors.innerHTML = '';

    try {
      const res = await fetch(urlPost, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf,
        },
        body: formData
      });

      const result = await res.json().catch(() => ({}));
      if (!res.ok) {
        // Show errors inline if provided
        const msg = result.msg || `Error HTTP ${res.status}`;
        if (typeof msg === 'object') {
          // render field errors
          this.renderErrors(msg);
        } else {
          this.showFormError(msg);
        }
        return;
      }

      // Success: show a short confirmation and go to the list. Do NOT open the print view.
      const successMsg = result.msg || 'Factura guardada correctamente.';
      this.showFormSuccess(successMsg);
      // Redirect to list after a short delay so user sees the message
      setTimeout(() => { window.location.href = urlSuccess; }, 1200);
    } catch (err) {
      console.error("Error en guardado:", err);
      this.showFormError('Error al grabar la venta. Revise la consola o contacte al administrador.');
    } finally {
      if (this.$btnSubmit) this.$btnSubmit.disabled = false;
      if (this.$btnSpinner) this.$btnSpinner.classList.add('d-none');
    }
  }

  renderErrors(errors) {
    if (!this.$formErrors) return;
    let html = '<div class="alert alert-danger"><ul class="mb-0">';
    for (const [k, v] of Object.entries(errors)) {
      html += `<li><strong>${k}:</strong> ${v}</li>`;
    }
    html += '</ul></div>';
    this.$formErrors.innerHTML = html;
  }

  showFormError(msg) {
    if (!this.$formErrors) return alert(msg);
    this.$formErrors.innerHTML = `<div class="alert alert-danger">${msg}</div>`;
  }

  showFormSuccess(msg) {
    if (!this.$formErrors) return alert(msg);
    this.$formErrors.innerHTML = `<div class="alert alert-success">${msg}</div>`;
  }

}
