// frontend/js/reservas.js
// Lógica de la página de agendamiento: carga vehículos, maneja el form
// de vehículo nuevo si hace falta, y envía la reserva.

// --- Leer el service_id de la URL ---
const params = new URLSearchParams(window.location.search);
const serviceId = params.get('service_id');

const infoEl = document.getElementById('calendario-info');
const bloqueSelector = document.getElementById('bloque-selector-vehiculo');
const bloqueNuevoVehiculo = document.getElementById('bloque-nuevo-vehiculo');
const selectVehiculo = document.getElementById('select-vehiculo');
const errorEl = document.getElementById('agendar-error');
const exitoEl = document.getElementById('agendar-exito');

if (!serviceId) {
  infoEl.textContent = 'No se especificó un servicio. Volvé al catálogo y elegí uno.';
} else {
  infoEl.textContent = `Agendando servicio #${serviceId}`;
}

// Todos los inputs required dentro del bloque de vehículo nuevo
const camposNuevoVehiculo = bloqueNuevoVehiculo.querySelectorAll('input, select');

function toggleRequiredNuevoVehiculo(activar) {
  camposNuevoVehiculo.forEach(campo => {
    campo.required = activar;
  });
}

async function cargarVehiculos() {
  try {
    const vehiculos = await apiGet('/vehicles');

    if (vehiculos.length === 0) {
      // No tiene vehículos: ocultamos el selector, mostramos el formulario nuevo
      bloqueSelector.classList.add('oculto');
      bloqueNuevoVehiculo.classList.remove('oculto');
      toggleRequiredNuevoVehiculo(true); // ahora sí son obligatorios
    } else {
      vehiculos.forEach(v => {
        const option = document.createElement('option');
        option.value = v.vehicle_id;
        option.textContent = `${v.brand} ${v.model} - ${v.license_plate}`;
        selectVehiculo.appendChild(option);
      });
      toggleRequiredNuevoVehiculo(false); // están ocultos, no deben bloquear el envío
    }
  } catch (error) {
    errorEl.textContent = 'No se pudieron cargar tus vehículos: ' + error.message;
  }
}

cargarVehiculos();

// --- Envío del formulario ---
document.getElementById('form-agendar').addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.textContent = '';
  exitoEl.textContent = '';

  if (!serviceId) {
    errorEl.textContent = 'Falta el servicio. Volvé al catálogo.';
    return;
  }

  try {
    let vehicleId;

    // Si el bloque de vehículo nuevo está visible, primero creamos el vehículo
    if (!bloqueNuevoVehiculo.classList.contains('oculto')) {
      const nuevoVehiculo = await apiPost('/vehicles', {
        license_plate: document.getElementById('veh-placa').value,
        brand: document.getElementById('veh-marca').value,
        model: document.getElementById('veh-modelo').value,
        year: parseInt(document.getElementById('veh-anio').value),
        vehicle_type: document.getElementById('veh-tipo').value,
        fuel_type: document.getElementById('veh-combustible').value,
        transmission_type: document.getElementById('veh-transmision').value,
      });
      vehicleId = nuevoVehiculo.vehicle_id;
    } else {
      vehicleId = selectVehiculo.value;
    }

    // El input datetime-local da algo como "2026-09-25T09:00" (sin segundos).
    // Le agregamos ":00" para dejarlo en formato ISO 8601 completo, tal como
    // lo espera el backend.
    const fechaHora = document.getElementById('input-fecha-hora').value + ':00';

    const cita = await apiPost('/appointments', {
      vehicle_id: vehicleId,
      service_id: parseInt(serviceId),
      scheduled_start: fechaHora,
    });

    exitoEl.textContent = `Cita confirmada. Depósito a pagar: $${cita.deposit_amount}`;
    document.getElementById('form-agendar').reset();

  } catch (error) {
    if (error.status === 409) {
      errorEl.textContent = 'No hay disponibilidad en ese horario. Probá con otra fecha u hora.';
    } else {
      errorEl.textContent = error.message;
    }
  }
});