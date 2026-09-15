// frontend/js/api.js
// Wrapper centralizado de fetch. Ninguna otra página debe llamar fetch() directamente.

const API_BASE_URL = 'http://127.0.0.1:5000';

/**
 * Función base. Arma la petición, maneja JSON y centraliza errores.
 * @param {string} endpoint - ej: '/services', '/auth/login'
 * @param {object} options - method, body (objeto JS, no string), etc.
 */
async function apiRequest(endpoint, options = {}) {
  const config = {
    method: options.method || 'GET',
    credentials: 'include', // manda la cookie de sesión
    headers: {},
  };

  // Si hay body, lo convertimos a JSON y avisamos el Content-Type
  if (options.body) {
    config.headers['Content-Type'] = 'application/json';
    config.body = JSON.stringify(options.body);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  } catch (networkError) {
    // Esto salta solo si el servidor está caído o no hay red
    throw new Error('No se pudo conectar con el servidor. ¿Está corriendo el backend?');
  }

  // El backend puede responder sin body en algunos casos (poco común, pero por seguridad)
  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    data = null;
  }

  if (!response.ok) {
    // data.error viene del formato { error: '...' } que confirmaste
    const mensaje = data?.error || `Error ${response.status}`;
    const error = new Error(mensaje);
    error.status = response.status; // guardamos el código por si cada página quiere reaccionar distinto
    throw error;
  }

  return data;
}

// Funciones de conveniencia — esto es lo que vas a usar en cada página
function apiGet(endpoint) {
  return apiRequest(endpoint, { method: 'GET' });
}

function apiPost(endpoint, body) {
  return apiRequest(endpoint, { method: 'POST', body });
}

function apiPut(endpoint, body) {
  return apiRequest(endpoint, { method: 'PUT', body });
}

function apiDelete(endpoint) {
  return apiRequest(endpoint, { method: 'DELETE' });
}