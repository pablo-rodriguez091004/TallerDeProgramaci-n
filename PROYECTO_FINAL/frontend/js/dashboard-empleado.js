// frontend/js/dashboard-empleado.js
// Panel del mecánico: cambiar estado de la cita y registrar seguimientos con repuestos.

const listaCitas = document.getElementById('lista-citas');
const citasErrorEl = document.getElementById('citas-error');

let mapaVehiculos = new Map();
let mapaServicios = new Map();
let listaPartes = []; // array de {part_id, part_name, unit_price, stock_quantity}

const ESTADOS_CITA = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled'];
const NOMBRES_ESTADO_CITA = {
  pending: 'Pendiente', confirmed: 'Confirmada', in_progress: 'En proceso',
  completed: 'Completada', cancelled: 'Cancelada',
};

const ESTADOS_TRACKING = ['received', 'diagnosing', 'in_repair', 'quality_check', 'ready_for_pickup', 'delivered'];
const NOMBRES_ESTADO_TRACKING = {
  received: 'Recibido', diagnosing: 'Diagnosticando', in_repair: 'En reparación',
  quality_check: 'Control de calidad', ready_for_pickup: 'Listo para entrega', delivered: 'Entregado',
};

async function cargarTodo() {
  citasErrorEl.textContent = '';
  try {
    const [servicios, partes, citas] = await Promise.all([
      apiGet('/services'),
      apiGet('/parts'),
      apiGet('/appointments'),
    ]);

    mapaServicios = new Map(servicios.map(s => [s.service_id, s]));
    listaPartes = partes;

    // Pedimos cada vehículo individualmente por id (GET /vehicles no sirve para mecánico)
    const idsVehiculosUnicos = [...new Set(citas.map(c => c.vehicle_id))];
    const vehiculos = await Promise.all(
      idsVehiculosUnicos.map(id => apiGet(`/vehicles/${id}`).catch(() => null))
    );
    mapaVehiculos = new Map(
      vehiculos.filter(v => v !== null).map(v => [v.vehicle_id, v])
    );

    renderizarCitas(citas);
  } catch (error) {
    citasErrorEl.textContent = 'No se pudieron cargar tus citas: ' + error.message;
  }
}

function renderizarCitas(citas) {
  listaCitas.innerHTML = '';

  if (citas.length === 0) {
    listaCitas.textContent = 'No tenés citas asignadas por el momento.';
    return;
  }

  citas.forEach(cita => {
    const vehiculo = mapaVehiculos.get(cita.vehicle_id);
    const servicio = mapaServicios.get(cita.service_id);

    const tarjeta = document.createElement('div');
    tarjeta.className = 'tarjeta-servicio';
    tarjeta.dataset.appointmentId = cita.appointment_id;

    tarjeta.innerHTML = `
      <h2>${servicio ? servicio.service_name : 'Servicio #' + cita.service_id}</h2>
      <p>Vehículo: ${vehiculo ? vehiculo.license_plate + ' - ' + vehiculo.brand + ' ' + vehiculo.model : cita.vehicle_id}</p>
      <p>Fecha: ${new Date(cita.scheduled_start).toLocaleString()}</p>

      <label>Estado de la cita</label>
      <select class="select-estado-cita">
        ${ESTADOS_CITA.map(s => `<option value="${s}" ${s === cita.status ? 'selected' : ''}>${NOMBRES_ESTADO_CITA[s]}</option>`).join('')}
      </select>
      <button class="btn-guardar-estado">Guardar estado</button>

      <hr>
      <button class="btn-toggle-seguimiento">Agregar seguimiento</button>

      <form class="form-seguimiento oculto">
        <label>Estado del proceso</label>
        <select class="tracking-estado" required>
          ${ESTADOS_TRACKING.map(s => `<option value="${s}">${NOMBRES_ESTADO_TRACKING[s]}</option>`).join('')}
        </select>

        <label>Notas</label>
        <textarea class="tracking-notas" rows="2"></textarea>

        <label>Kilometraje actual</label>
        <input type="number" class="tracking-kilometraje">

        <label>Repuestos usados</label>
        <div class="lista-partes-checkbox">
          ${listaPartes.map(p => `
            <div class="fila-parte">
              <input type="checkbox" class="check-parte" value="${p.part_id}" id="parte-${cita.appointment_id}-${p.part_id}">
              <label for="parte-${cita.appointment_id}-${p.part_id}">${p.part_name} (stock: ${p.stock_quantity})</label>
              <input type="number" class="cantidad-parte" min="1" value="1" disabled>
            </div>
          `).join('')}
        </div>

        <button type="submit">Guardar seguimiento</button>
      </form>

      <p class="mensaje-error"></p>
      <p class="mensaje-exito"></p>
    `;

    listaCitas.appendChild(tarjeta);
  });
}

// --- Delegación de eventos: todo dentro de #lista-citas ---

listaCitas.addEventListener('click', async (e) => {
  const tarjeta = e.target.closest('.tarjeta-servicio');
  if (!tarjeta) return;
  const appointmentId = tarjeta.dataset.appointmentId;

  // Guardar cambio de estado de la cita
  if (e.target.classList.contains('btn-guardar-estado')) {
    const nuevoEstado = tarjeta.querySelector('.select-estado-cita').value;
    const errorEl = tarjeta.querySelector('.mensaje-error');
    const exitoEl = tarjeta.querySelector('.mensaje-exito');
    errorEl.textContent = '';
    exitoEl.textContent = '';

    try {
      await apiPut(`/appointments/${appointmentId}/status`, { status: nuevoEstado });
      exitoEl.textContent = 'Estado actualizado.';
    } catch (error) {
      errorEl.textContent = error.message;
    }
  }

  // Mostrar/ocultar formulario de seguimiento
  if (e.target.classList.contains('btn-toggle-seguimiento')) {
    tarjeta.querySelector('.form-seguimiento').classList.toggle('oculto');
  }

  // Habilitar/deshabilitar el input de cantidad según el checkbox
  if (e.target.classList.contains('check-parte')) {
    const inputCantidad = e.target.closest('.fila-parte').querySelector('.cantidad-parte');
    inputCantidad.disabled = !e.target.checked;
  }
});

listaCitas.addEventListener('submit', async (e) => {
  if (!e.target.classList.contains('form-seguimiento')) return;
  e.preventDefault();

  const tarjeta = e.target.closest('.tarjeta-servicio');
  const appointmentId = tarjeta.dataset.appointmentId;
  const errorEl = tarjeta.querySelector('.mensaje-error');
  const exitoEl = tarjeta.querySelector('.mensaje-exito');
  errorEl.textContent = '';
  exitoEl.textContent = '';

  // Armamos parts_used solo con los checkboxes marcados
  const partsUsed = [];
  tarjeta.querySelectorAll('.check-parte:checked').forEach(chk => {
    const cantidad = chk.closest('.fila-parte').querySelector('.cantidad-parte').value;
    partsUsed.push({ part_id: parseInt(chk.value), quantity: parseInt(cantidad) });
  });

  const body = {
    status: e.target.querySelector('.tracking-estado').value,
    notes: e.target.querySelector('.tracking-notas').value || null,
    current_mileage: e.target.querySelector('.tracking-kilometraje').value
      ? parseInt(e.target.querySelector('.tracking-kilometraje').value)
      : null,
  };
  if (partsUsed.length > 0) {
    body.parts_used = partsUsed;
  }

  try {
    await apiPost(`/tracking/appointment/${appointmentId}`, body);
    exitoEl.textContent = 'Seguimiento registrado.';
    e.target.reset();
    e.target.classList.add('oculto');
  } catch (error) {
    errorEl.textContent = error.message;
  }
});

cargarTodo();