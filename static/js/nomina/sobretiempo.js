// static/js/nomina/sobretiempo.js
document.addEventListener('DOMContentLoaded', () => new SobretiempoManager());

class SobretiempoManager {
    constructor() {
        this.d = document;

        // --- Estado ---
        this.detalles = [];

        // --- Elementos DOM ---
        this.$form = this.d.getElementById("frmSobretiempo");

        this.$tipo = this.d.getElementById("tipo");
        this.$horas = this.d.getElementById("horas");
        this.$btnAdd = this.d.getElementById("btnAdd");
        this.$tbody = this.d.getElementById("detalle");

        this.$btnSubmit = this.d.getElementById("btnSubmit");
        this.$btnSpinner = this.d.getElementById("btnSpinner");
        this.$formErrors = this.d.getElementById("formErrors");

        // Eventos
        this.initEvents();
    }

    initEvents() {
        if (this.$btnAdd) this.$btnAdd.addEventListener("click", () => this.addDetalle());
        if (this.$tbody) this.$tbody.addEventListener("click", (e) => this.deleteDetalle(e));
        if (this.$form) this.$form.addEventListener("submit", (e) => this.submitForm(e));
    }

    // ==========================================
    //          AÑADIR DETALLE
    // ==========================================
    addDetalle() {
        const tipoOption = this.$tipo.options[this.$tipo.selectedIndex];

        if (!tipoOption.value) {
            return this.showError("Seleccione un tipo de sobretiempo.");
        }

        const horas = parseFloat(this.$horas.value);
        if (isNaN(horas) || horas <= 0) {
            return this.showError("Ingrese un número de horas válido.");
        }

        const tipoId = parseInt(tipoOption.value);
        const tipoNombre = tipoOption.text;
        const factor = parseFloat(tipoOption.dataset.factor);

        // Si existe → preguntar si quiere actualizar
        const existing = this.detalles.find(d => d.tipo == tipoId);

        if (existing && !confirm("Este tipo ya está agregado. ¿Desea reemplazarlo?")) {
            return;
        }

        // Eliminar si existía
        this.detalles = this.detalles.filter(d => d.tipo !== tipoId);

        // Agregar nuevo
        this.detalles.push({
            tipo: tipoId,
            nombre: tipoNombre,
            factor: factor,
            horas: horas
        });

        this.renderDetalle();
    }

    // ==========================================
    //          MOSTRAR DETALLE EN TABLA
    // ==========================================
    renderDetalle() {
        this.$tbody.innerHTML = this.detalles
            .map(d => `
                <tr>
                    <td>${d.nombre}</td>
                    <td>${d.factor}</td>
                    <td>${d.horas}</td>
                    <td class="text-center">
                        <button class="btn btn-danger btn-sm" data-id="${d.tipo}" rel="del">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `)
            .join("");
    }

    // ==========================================
    //          ELIMINAR DETALLE
    // ==========================================
    deleteDetalle(e) {
        const btn = e.target.closest("button[rel=del]");
        if (!btn) return;

        const id = parseInt(btn.dataset.id);
        this.detalles = this.detalles.filter(d => d.tipo !== id);

        this.renderDetalle();
    }

    // ==========================================
    //          GUARDAR SOBRETIEMPO
    // ==========================================
    async submitForm(e) {
        e.preventDefault();

        if (this.detalles.length === 0) {
            return this.showError("Debe agregar al menos un detalle."); 
        }

        const data = new FormData(this.$form);
        data.append("detalle", JSON.stringify(this.detalles));

        const csrf = this.d.querySelector("[name=csrfmiddlewaretoken]").value;

        this.$btnSubmit.disabled = true;
        if (this.$btnSpinner) this.$btnSpinner.classList.remove("d-none");

        try {
            const res = await fetch(save_url, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": csrf
                },
                body: data
            });

            const result = await res.json();

            if (!res.ok) {
                return this.showError(result.msg || "Error al guardar.");
            }

            this.showSuccess(result.msg || "Guardado con éxito");

            setTimeout(() => {
                window.location.href = list_url;
            }, 1200);

        } catch (err) {
            console.error(err);
            this.showError("Error inesperado al guardar.");
        } finally {
            this.$btnSubmit.disabled = false;
            if (this.$btnSpinner) this.$btnSpinner.classList.add("d-none");
        }
    }

    // ==========================================
    //          MENSAJES
    // ==========================================
    showError(msg) {
        this.$formErrors.innerHTML = `
            <div class="alert alert-danger">${msg}</div>
        `;
    }

    showSuccess(msg) {
        this.$formErrors.innerHTML = `
            <div class="alert alert-success">${msg}</div>
        `;
    }
}
