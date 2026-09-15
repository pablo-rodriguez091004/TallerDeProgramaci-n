// frontend/js/historial.js
// Muestra vehículos (con editar/borrar) y citas (con estado de pago) del cliente logueado.

const listaVehiculos = document.getElementById('lista-vehiculos');
const vehiculosErrorEl = document.getElementById('vehiculos-error');
const listaCitas = document.getElementById('lista-citas');
const citasErrorEl = document.getElementById('citas-error');

const bloqueEditar = document.getElementById('bloque-editar-vehiculo');

// Diccionarios id -> nombre, para no repetir fetch por cada cita
let mapaVehiculos = new Map();
let mapaServicios = new Map();

// Traducciones legibles del status de la cita
const NOMBRES_ESTADO_CITA = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  in_progress: 'En proceso',
  completed: 'Completada',
  cancelled: 'Cancelada',
};

// --- VEHÍCULOS ---

async function cargarVehiculos() {
  try {
    const vehiculos = await apiGet('/vehicles');
    mapaVehiculos = new Map(vehiculos.map(v => [v.vehicle_id, v]));
    renderizarVehiculos(vehiculos);
  } catch (error) {
    vehiculosErrorEl.textContent = 'No se pudieron cargar tus vehículos: ' + error.message;
  }
}

function renderizarVehiculos(vehiculos) {
  listaVehiculos.innerHTML = '';

  if (vehiculos.length === 0) {
    listaVehiculos.textContent = 'No tenés vehículos registrados todavía.';
    return;
  }

  vehiculos.forEach(v => {
    const tarjeta = document.createElement('div');
    tarjeta.className = 'tarjeta-servicio';
    tarjeta.innerHTML = `
      <h2>${v.brand} ${v.model} (${v.year})</h2>
      <p>Placa: ${v.license_plate}</p>
      <button class="btn-editar-vehiculo" data-id="${v.vehicle_id}">Editar</button>
      <button class="btn-borrar-vehiculo" data-id="${v.vehicle_id}">Eliminar</button>
    `;
    listaVehiculos.appendChild(tarjeta);
  });
}

// Delegación de eventos: un solo listener para editar y borrar
listaVehiculos.addEventListener('click', async (e) => {
  const id = e.target.dataset.id;
  if (!id) return;

  if (e.target.classList.contains('btn-editar-vehiculo')) {
    abrirFormularioEdicion(id);
  }

  if (e.target.classList.contains('btn-borrar-vehiculo')) {
    if (!confirm('¿Seguro que querés eliminar este vehículo?')) return;
    try {
      await apiDelete(`/vehicles/${id}`);
      cargarVehiculos(); // recargamos la lista
    } catch (error) {
      vehiculosErrorEl.textContent = error.message;
    }
  }
});

function abrirFormularioEdicion(id) {
  const v = mapaVehiculos.get(Number(id));
  document.getElementById('edit-veh-id').value = v.vehicle_id;
  document.getElementById('edit-veh-placa').value = v.license_plate;
  document.getElementById('edit-veh-marca').value = v.brand;
  document.getElementById('edit-veh-modelo').value = v.model;
  document.getElementById('edit-veh-anio').value = v.year;
  bloqueEditar.classList.remove('oculto');
}

document.getElementById('btn-cancelar-edicion').addEventListener('click', () => {
  bloqueEditar.classList.add('oculto');
});

document.getElementById('form-editar-vehiculo').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('edit-veh-id').value;

  try {
    await apiPut(`/vehicles/${id}`, {
      license_plate: document.getElementById('edit-veh-placa').value,
      brand: document.getElementById('edit-veh-marca').value,
      model: document.getElementById('edit-veh-modelo').value,
      year: parseInt(document.getElementById('edit-veh-anio').value),
    });
    bloqueEditar.classList.add('oculto');
    cargarVehiculos();
  } catch (error) {
    vehiculosErrorEl.textContent = error.message;
  }
});

// --- CITAS ---

async function cargarServiciosParaMapa() {
  const servicios = await apiGet('/services');
  mapaServicios = new Map(servicios.map(s => [s.service_id, s]));
}

async function cargarCitas() {
      citasErrorEl.textContent = ''; // limpiamos cualquier error viejo antes de recargar
  try {
    await cargarServiciosParaMapa();
    const citas = await apiGet('/appointments');
    await renderizarCitas(citas);
  } catch (error) {
    citasErrorEl.textContent = 'No se pudieron cargar tus citas: ' + error.message;
  }
}

async function renderizarCitas(citas) {
  listaCitas.innerHTML = '';

  if (citas.length === 0) {
    listaCitas.textContent = 'No tenés citas agendadas todavía.';
    return;
  }

  for (const cita of citas) {
    const vehiculo = mapaVehiculos.get(cita.vehicle_id);
    const servicio = mapaServicios.get(cita.service_id);
    const pagos = await apiGet(`/payments/appointment/${cita.appointment_id}`);

    const tarjeta = document.createElement('div');
    tarjeta.className = 'tarjeta-servicio';

let htmlPagos = pagos.map(pago => {
  const nombreTipo = pago.payment_type === 'deposit' ? 'Depósito' : 'Saldo';
  if (pago.status === 'completed') {   // <-- antes decía 'paid'
    return `<p>${nombreTipo}: pagado ✅</p>`;
  }
  return `
    <p>${nombreTipo}: pendiente ($${pago.amount})
      <button class="btn-pagar" data-payment-id="${pago.payment_id}">Pagar</button>
    </p>`;
}).join('');

    const puedeCancel = cita.status !== 'completed' && cita.status !== 'cancelled';

    tarjeta.innerHTML = `
      <h2>${servicio ? servicio.service_name : 'Servicio #' + cita.service_id}</h2>
      <p>Vehículo: ${vehiculo ? vehiculo.license_plate : cita.vehicle_id}</p>
      <p>Fecha: ${new Date(cita.scheduled_start).toLocaleString()}</p>
      <p>Estado: ${NOMBRES_ESTADO_CITA[cita.status] || cita.status}</p>
      ${htmlPagos}
      ${puedeCancel ? `<button class="btn-cancelar-cita" data-id="${cita.appointment_id}">Cancelar cita</button>` : ''}
    `;

    listaCitas.appendChild(tarjeta);
  }
}

// Delegación de eventos para pagar y cancelar
listaCitas.addEventListener('click', async (e) => {
  if (e.target.classList.contains('btn-pagar')) {
    const paymentId = e.target.dataset.paymentId;
    try {
      await apiPost(`/payments/${paymentId}/pay`, {});
      cargarCitas(); // recargamos para reflejar el nuevo estado
    } catch (error) {
      citasErrorEl.textContent = error.message;
    }
  }

  if (e.target.classList.contains('btn-cancelar-cita')) {
    if (!confirm('¿Seguro que querés cancelar esta cita?')) return;
    const id = e.target.dataset.id;
    try {
      await apiDelete(`/appointments/${id}`);
      cargarCitas();
    } catch (error) {
      citasErrorEl.textContent = error.message;
    }
  }
});

// --- Inicio ---
cargarVehiculos();
cargarCitas();