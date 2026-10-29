document.addEventListener('DOMContentLoaded', function() {

    const form = document.getElementById('reportForm');
    const btnGenerate = document.getElementById('btnGenerate');

    const fechaInicio = document.getElementById('fecha_inicio');
    const fechaFin = document.getElementById('fecha_fin');

    const metricCruzadaBlock = document.getElementById('metric_cruzada_block');
    const metricCruzadaCheckbox = document.getElementById('metric_cruzada');

    const modoAmbos = document.getElementById('modo_ambos');
    const modoTramites = document.getElementById('modo_tramites');
    const modoUsuarios = document.getElementById('modo_usuarios');

    const formatoExcel = document.getElementById('formato_excel');
    const formatoPDF = document.getElementById('formato_pdf');

    function updateCruzadaBlock() {

        const modoAmbosSelected = modoAmbos.checked;
        const formatoExcelSelected = formatoExcel.checked;

        const shouldShow = modoAmbosSelected && formatoExcelSelected;

        if (shouldShow) {

            metricCruzadaBlock.style.display = 'block';

            metricCruzadaCheckbox.checked = true;

            metricCruzadaBlock.classList.add('selected');

        } else {

            metricCruzadaBlock.style.display = 'none';

            metricCruzadaCheckbox.checked = false;

            metricCruzadaBlock.classList.remove('selected');

        }
    }

    const radioOptions = document.querySelectorAll('.radio-option');

    radioOptions.forEach(option => {

        option.addEventListener('click', function() {

            const group = this.closest('.radio-group');

            group.querySelectorAll('.radio-option').forEach(opt => {
                opt.classList.remove('selected');
            });

            this.classList.add('selected');

            const radio = this.querySelector('input[type="radio"]');

            if (radio) radio.checked = true;

            updateCruzadaBlock();

        });

    });

    const formatCards = document.querySelectorAll('.format-card');

    formatCards.forEach(card => {

        card.addEventListener('click', function() {

            formatCards.forEach(c => c.classList.remove('selected'));

            this.classList.add('selected');

            const radio = this.querySelector('input[type="radio"]');

            if (radio) radio.checked = true;

            updateCruzadaBlock();

        });

    });


    formatoExcel.addEventListener('change', updateCruzadaBlock);
    formatoPDF.addEventListener('change', updateCruzadaBlock);

    const metricOptions = document.querySelectorAll('.metric-option');

    metricOptions.forEach(option => {

        const checkbox = option.querySelector('input[type="checkbox"]');

        option.addEventListener('click', function(e) {

            if (e.target.tagName === 'INPUT') return;

            if (this.id === 'metric_cruzada_block' && this.style.display === 'none') return;

            checkbox.checked = !checkbox.checked;

            if (checkbox.checked)
                this.classList.add('selected');
            else
                this.classList.remove('selected');

        });

        if (checkbox.checked)
            option.classList.add('selected');

    });

    document.getElementById('btnSelectAll').addEventListener('click', function() {

        metricOptions.forEach(option => {

            if (option.style.display === 'none') return;

            const checkbox = option.querySelector('input[type="checkbox"]');

            checkbox.checked = true;

            option.classList.add('selected');

        });

    });


    document.getElementById('btnDeselectAll').addEventListener('click', function() {

        metricOptions.forEach(option => {

            if (option.style.display === 'none') return;

            const checkbox = option.querySelector('input[type="checkbox"]');

            checkbox.checked = false;

            option.classList.remove('selected');

        });

    });

    function validateDates() {

        const inicio = new Date(fechaInicio.value);

        const fin = new Date(fechaFin.value);

        const hoy = new Date();

        hoy.setHours(0, 0, 0, 0);

        if (!fechaInicio.value || !fechaFin.value) {

            alert('Por favor selecciona ambas fechas');

            return false;

        }

        if (inicio > fin) {

            alert('La fecha de inicio no puede ser mayor a la fecha fin');

            fechaFin.value = '';

            return false;

        }

        if (inicio > hoy || fin > hoy) {

            alert('No se pueden seleccionar fechas futuras');

            return false;

        }

        const diffDays = Math.ceil((fin - inicio) / (1000 * 60 * 60 * 24));

        if (diffDays > 365) {

            return confirm('Has seleccionado un rango mayor a 1 año. Esto puede tomar varios minutos. ¿Deseas continuar?');

        }

        return true;

    }

    function validateMetrics() {

        const checkedMetrics = document.querySelectorAll('input[name="metricas"]:checked');

        if (checkedMetrics.length === 0) {

            alert('Debes seleccionar al menos una opción para incluir en el reporte');

            return false;

        }

        return true;

    }

    const today = new Date().toISOString().split('T')[0];

    fechaInicio.max = today;

    fechaFin.max = today;

    fechaInicio.addEventListener('change', validateDates);

    fechaFin.addEventListener('change', validateDates);

    form.addEventListener('submit', function(e) {

        if (!validateDates() || !validateMetrics()) {

            e.preventDefault();

            return false;

        }

        btnGenerate.disabled = true;

        btnGenerate.textContent = 'Generando reporte...';

        setTimeout(() => {

            btnGenerate.disabled = false;

            btnGenerate.textContent = 'Generar y Descargar Reporte';

        }, 5000);

    });
    updateCruzadaBlock();

});