document.addEventListener('DOMContentLoaded', () => new PurchaseManager());

class PurchaseManager {
  constructor() {
    this.d = document;
    this.detailPurchase = [];

    this.$supplier = this.d.getElementById('id_supplier');
    this.$product = this.d.getElementById('product');
    this.$btnAdd = this.d.getElementById('btnAdd');
    this.$form = this.d.getElementById('frmPurchase');
    this.$detailBody = this.d.getElementById('detalle');

    this.$btnSubmit = this.d.getElementById('btnSubmit');
    this.$btnSpinner = this.d.getElementById('btnSpinner');
    this.$formErrors = this.d.getElementById('formErrors');

    this.subtotalInput = this.d.getElementById('id_subtotal');
    this.ivaInput = this.d.getElementById('id_iva');
    this.totalInput = this.d.getElementById('id_total');

    this.initEvents();

    if (typeof detail_sales !== 'undefined' && detail_sales.length > 0) {
      this.detailPurchase = detail_sales.map(item => ({
        id: item.product,
        description: item.product__description,
        cost: parseFloat(item.cost || item.price || 0),
        quantify: parseFloat(item.quantify),
        iva: parseFloat(item.iva || 0),
        sub: parseFloat(item.subtotal)
      }));
      this.renderDetail();
      this.updateTotals();
    }
  }

  initEvents() {
    if (this.$product) this.$product.addEventListener('change', e => this.onProductChange(e));
    if (this.$btnAdd) this.$btnAdd.addEventListener('click', () => this.addProduct());
    if (this.$detailBody) this.$detailBody.addEventListener('click', e => this.removeProduct(e));
    if (this.$form) this.$form.addEventListener('submit', e => this.submitForm(e));
    if (this.$product) this.onProductChange({ target: this.$product });
  }

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
    if (!selected || !selected.value) return this.showFormError('Seleccione un producto');

    const stock = parseInt(selected.dataset.stock || 0);
    const quantify = parseInt(this.d.getElementById('quantify').value || 0);
    if (quantify <= 0) return this.showFormError('Cantidad inválida');

    const id = parseInt(selected.value);
    const description = selected.text;
    const cost = parseFloat(selected.dataset.cost || selected.dataset.price || 0);
    const iva = parseFloat(selected.dataset.iva || 0);
    this.calculateProduct(id, description, iva, cost, quantify);
  }

  calculateProduct(id, description, iva, cost, quantify) {
    const existing = this.detailPurchase.find(p => p.id === id);
    if (existing && !confirm(`"${description}" ya está agregado. ¿Desea actualizar la cantidad?`)) return;
    if (existing) {
      quantify += existing.quantify;
      this.detailPurchase = this.detailPurchase.filter(p => p.id !== id);
    }
    const ivaValue = iva > 0 ? (cost * quantify * (iva / 100)) : 0;
    const sub = cost * quantify + ivaValue;
    this.detailPurchase.push({ id, description, cost, quantify, iva: ivaValue, sub });
    this.renderDetail();
    this.updateTotals();
  }

  renderDetail() {
    if (!this.$detailBody) return;
    this.$detailBody.innerHTML = this.detailPurchase.map(prod => `
      <tr>
        <td>${prod.id}</td>
        <td>${prod.description}</td>
        <td>${prod.cost.toFixed(2)}</td>
        <td>${prod.quantify}</td>
        <td>${prod.iva.toFixed(2)}</td>
        <td>${prod.sub.toFixed(2)}</td>
        <td class="text-center"><button class="text-danger" data-id="${prod.id}" rel="rel-delete"><i class="fa-solid fa-trash"></i></button></td>
      </tr>`).join('');
  }

  removeProduct(e) {
    const btn = e.target.closest && e.target.closest('button[rel=rel-delete]');
    if (!btn) return;
    const id = parseInt(btn.dataset.id);
    this.detailPurchase = this.detailPurchase.filter(p => p.id !== id);
    this.renderDetail();
    this.updateTotals();
  }

  updateTotals() {
    const totals = this.detailPurchase.reduce((acc, p) => {
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
      this.showFormError('Debe agregar productos antes de guardar la compra.');
      return;
    }
    await this.savePurchase(save_url, purchase_list_url);
  }

  async savePurchase(urlPost, urlSuccess) {
    const formData = new FormData(this.$form);
    formData.append('detail', JSON.stringify(this.detailPurchase));
    const csrfEl = this.d.querySelector('[name=csrfmiddlewaretoken]');
    const csrf = csrfEl ? csrfEl.value : '';

    if (this.$btnSubmit) this.$btnSubmit.disabled = true;
    if (this.$btnSpinner) this.$btnSpinner.classList.remove('d-none');
    if (this.$formErrors) this.$formErrors.innerHTML = '';

    try {
      const res = await fetch(urlPost, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf },
        body: formData
      });
      const result = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = result.msg || `Error HTTP ${res.status}`;
        if (typeof msg === 'object') this.renderErrors(msg); else this.showFormError(msg);
        return;
      }
      const successMsg = result.msg || 'Compra guardada correctamente.';
      this.showFormSuccess(successMsg);
      setTimeout(() => { window.location.href = urlSuccess; }, 1200);
    } catch (err) {
      console.error('Error en guardado:', err);
      this.showFormError('Error al grabar la compra. Revise la consola o contacte al administrador.');
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

