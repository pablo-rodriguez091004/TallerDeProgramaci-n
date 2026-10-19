# MecaTrack — Guía de sustentación y demo

Duración sugerida: **12–15 min** (2 de contexto + 7 de demo + 3 de código/pruebas + preguntas).

---

## 1. Antes de presentar (checklist)

- [ ] PostgreSQL arriba: `pg_isready -h 127.0.0.1`
- [ ] Pruebas en verde: `cd backend && venv/bin/python -m pytest`
- [ ] Pipeline de GitHub Actions en verde (abre la pestaña **Actions** del repo en otra pestaña)
- [ ] Los 3 usuarios inician sesión con `test1234` (ver la nota al final)
- [ ] Existe al menos una cita futura en estado *pendiente* o *confirmada* para mostrarla
- [ ] Terminal 1: `./scripts/start-backend.sh`
- [ ] Terminal 2: `cd frontend && python3 -m http.server 5500 --bind 127.0.0.1`
- [ ] Navegador en `http://127.0.0.1:5500/index.html` (usa `127.0.0.1`, **no** `localhost`)
- [ ] VSCode abierto en `appointment_model.py`, `appointment_repository.py`, `scheduling_engine.py` y `tests/test_integration.py`

> **Demo sin riesgo para tus datos:** puedes presentar sobre una base aparte creada con las migraciones y el seed:
> `DATABASE_URL=postgresql://postgres:CLAVE@127.0.0.1:5432/mecatrack_demo ./scripts/start-backend.sh`
> (la variable de entorno tiene prioridad sobre `backend/.env`).

---

## 2. Guion

### 2.1 Contexto (≈ 2 min)

- **Problema:** un taller agenda citas "a mano", choca bahías y mecánicos y el cliente no sabe en qué va su carro.
- **Solución:** MecaTrack, con 3 roles (cliente, mecánico y dueño) y un motor que asigna solo una bahía y un mecánico libres.
- **Arquitectura multicapa**, dibujada o en una diapositiva:
  `UI (HTML/JS vanilla) → API Flask (blueprints + role_required) → negocio (scheduling_engine) → repositorios → SQLAlchemy ORM → PostgreSQL`

### 2.2 Demo en vivo (≈ 7 min)

| # | Rol | Acción | Qué decir |
|---|---|---|---|
| 1 | Cliente (`laura.cliente@gmail.com`) | Iniciar sesión → catálogo | "La sesión viaja en una cookie HttpOnly de Flask-Login; CORS permite credenciales solo desde 127.0.0.1:5500." |
| 2 | Cliente | **Agendar** un servicio para mañana a las 9:00 | "El backend calcula la hora de fin con la duración del servicio y asigna bahía y mecánico. Se crean el depósito (30 %) y el saldo en **una sola transacción**." |
| 3 | Cliente | Intentar **otra cita a la misma hora** | Si no queda bahía o mecánico libre → *"No hay disponibilidad"* (HTTP 409). "El solapamiento se calcula en SQL con intervalos `[inicio, fin)`." |
| 4 | Cliente | Historial → **Pagar** depósito | "Pagar el depósito pasa la cita de *pendiente* a *confirmada*." |
| 5 | Mecánico (`andres.mecanico@…`) | Ver la cita → **Agregar seguimiento** "Diagnosticando" con 1 repuesto | "Se descuenta el stock; si no alcanza, la transacción hace rollback." |
| 6 | Dueño (`carlos.owner@…`) | Panel → pestaña **Citas** | "Vista global: cliente, mecánico, vehículo, servicio y bahía en **una sola consulta** gracias a `joinedload`." |
| 7 | Dueño | **Repuestos**: mostrar que el stock bajó; crear uno con stock 2 → aparece *Stock bajo* | |
| 8 | Dueño | **Bahías**: poner una en *mantenimiento* | "El motor ya no la asigna." (opcional: repetir el paso 3) |
| 9 | Dueño | **Mecánicos**: crear uno y desactivarlo | "Un mecánico inactivo no puede iniciar sesión ni recibe citas." |
| 10 | — | Abrir `dashboard-admin.html` sin sesión | Redirige al login: la protección es en el backend (401/403), no solo en la UI. |

### 2.3 Código y calidad (≈ 3 min)

1. **ORM y relaciones**, en `models/appointment_model.py`: la doble FK hacia `users` con alias `client` y `mechanic` (`foreign_keys=[...]`).
2. **Repositorio + N+1**, en `repositories/appointment_repository.py`: `_LIST_OPTIONS` con `joinedload`. Las rutas no consultan modelos directamente.
3. **Migraciones**: `venv/bin/flask --app app db history` → 2 revisiones (esquema inicial + índices del motor).
4. **Pruebas**: ejecutar `venv/bin/python -m pytest` en vivo (≈ 2 s, 3 pasan) y mostrar el `assert len(selects) <= 2`.
5. **CI**: pestaña Actions en verde y `.github/workflows/mecatrack-tests.yml` (PostgreSQL como servicio).

---

## 3. Preguntas probables y respuestas cortas

**¿Qué es el problema N+1 y cómo lo resolviste?**
Listar N citas y acceder a 5 relaciones perezosas genera 1 + 5N consultas. Con `joinedload` se traen en un solo `SELECT … LEFT OUTER JOIN`. Una prueba cuenta las consultas y falla si alguien quita el `joinedload` (lo comprobé quitándolo).

**¿Por qué `foreign_keys` en `Appointment`?**
Porque hay dos FK hacia `users` (`client_user_id` y `mechanic_user_id`) y SQLAlchemy no puede saber cuál usa cada relación.

**¿Cómo evitas que dos citas usen la misma bahía a la misma hora?**
El motor busca una bahía disponible y un mecánico activo que no tengan una cita bloqueante (pending, confirmed o in_progress) que se solape: `existente.inicio < nuevo.fin AND nuevo.inicio < existente.fin`. Las canceladas y las completadas liberan la franja.
*Límite conocido:* dos peticiones exactamente simultáneas podrían pasar la verificación a la vez. Se resolvería con un bloqueo (`SELECT … FOR UPDATE`) o con una restricción `EXCLUDE` de PostgreSQL.

**¿Por qué no usaste una BD en memoria (SQLite) para las pruebas?**
Las pruebas corren contra un PostgreSQL efímero (contenedor en CI y una base `_test` en local), así validan el motor real: restricciones CHECK, `TRUNCATE … RESTART IDENTITY` y las migraciones. SQLite no reproduce eso fielmente.

**¿Cómo protegen las pruebas tu base de datos real?**
`conftest.py` aborta si el nombre de la base no termina en `_test`.

**¿Qué hacen las migraciones?**
`26b91cd3e584` crea las 10 tablas (equivale a `schema.sql`; lo verifiqué con `compare_metadata` contra la base real: 0 diferencias). `6a4f4ff49bfe` añade índices para las consultas de solapamiento y las FK, que PostgreSQL no indexa solo.

**¿Por qué la transacción la confirma la ruta y no el repositorio?**
Para que operaciones compuestas, como cita + 2 pagos o seguimiento + descuento de stock, sean atómicas: si algo falla, se hace rollback de todo.

**Complejidad del motor de agendamiento (Big-O)**
O(B + M) consultas `EXISTS` en el peor caso (B bahías, M mecánicos). Cada una usa los índices compuestos `(bay_id, scheduled_start, scheduled_end)` y `(mechanic_user_id, …)`.

**SOLID**
*S:* rutas (HTTP), repositorios (datos) y motor (reglas) separados. *D:* las rutas dependen de funciones de repositorio, no de consultas concretas, y los modelos se pueden cambiar sin tocar los controladores.

---

## 4. Plan B

| Falla | Qué hacer |
|---|---|
| "No se pudo conectar con el servidor" | ¿Corre el backend en :5000? Revisa la terminal 1. |
| El login funciona pero luego da 401 | Estás en `localhost` en vez de `127.0.0.1`, o el frontend no está en el puerto 5500. |
| El agendamiento da 409 siempre | Bahías en mantenimiento o franja ocupada: prueba otra fecha u hora. |
| La BD falla en vivo | Muestra las pruebas (`pytest`) y las capturas del informe (`docs/Informe_Guia4_MecaTrack.docx`). |

---

> **Nota sobre las contraseñas:** en la base `taller_mecanico`, `carlos` y `andres` ya tienen `test1234`, pero **`laura` no**. Antes de la demo, inicia sesión con otra cuenta de cliente, registra una nueva desde la pantalla de registro o actualiza el hash de laura.
