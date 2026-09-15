// frontend/js/catalogo.js
// Carga el catálogo público de servicios y arma las tarjetas.

const contenedorServicios = document.getElementById('lista-servicios');
const errorEl = document.getElementById('catalogo-error');
const cargandoEl = document.getElementById('catalogo-cargando');

async function cargarServicios() {
try {
    const servicios = await apiGet('/services');
    cargandoEl.classList.add('oculto');
    renderizarServicios(servicios);
} catch (error) {
    cargandoEl.classList.add('oculto');
    errorEl.textContent = 'No se pudieron cargar los servicios: ' + error.message;
}
}

function renderizarServicios(servicios) {
if (servicios.length === 0) {
    contenedorServicios.textContent = 'No hay servicios disponibles por el momento.';
    return;
}

servicios.forEach(servicio => {
    const tarjeta = document.createElement('div');
    tarjeta.className = 'tarjeta-servicio';

    tarjeta.innerHTML = `
    <h2>${servicio.service_name}</h2>
    <p>${servicio.description || ''}</p>
    <p class="detalle-servicio">Duración estimada: ${servicio.estimated_duration_minutes} min</p>
    <p class="precio-servicio">$${servicio.base_price}</p>
    <button class="btn-agendar" data-id="${servicio.service_id}">Agendar</button>
    `;

    contenedorServicios.appendChild(tarjeta);
});

  // Un solo listener para todos los botones (event delegation),
  // en vez de agregar un listener por cada tarjeta.
contenedorServicios.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-agendar')) {      const serviceId = e.target.dataset.id;  window.location.href = `calendario.html?service_id=${serviceId}`;
    }  });
}

cargarServicios();