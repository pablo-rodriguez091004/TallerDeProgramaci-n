# Uso de IA – Guía 6 (Sesiones 11 y 12)

Trazabilidad del código generado con IA, exigida por la guía ("Documente
siempre qué generó la IA y qué cambios realizó").

- **Herramienta:** Claude Code (modelo Claude Opus 5.5, Anthropic), en la terminal, sobre este repositorio.
- **Estudiante:** Pablo Rodríguez. Revisa, aprueba cada fase y hace los ajustes manuales.
- **Regla de trabajo:** la IA propone un plan por fase, espera la aprobación, ejecuta, corre las pruebas y hace un commit por fase. No hace push sin autorización.

> Las secciones marcadas con **[COMPLETAR]** las debe escribir Pablo con su propia experiencia.

---

## Fase 0 – Diagnóstico

| Qué hizo la IA | Cómo se verificó |
|---|---|
| Leyó la guía (`docs/GUIA_LAB_TALLER_S11_S12.docx`, copiada desde `~/Descargas`), el backend, las migraciones, los tests, el CI y el generador del informe de la Guía 5 | Corrió la suite base: 31 pruebas en verde |
| Consultó el catálogo real de datos.gov.co (API de Socrata) para no proponer datasets inventados | Respuestas HTTP 200 con ids reales (`u3vn-bdcy`, `gdxc-w37w`) |

Decisiones que tomó Pablo: aprobar el plan y migrar los 9 blueprints (no solo agendamiento y pagos).

## Fase 1 – Refactor a arquitectura hexagonal

### Código generado por la IA

| Archivo(s) | Contenido |
|---|---|
| `backend/domain/**` | Entidades (dataclasses), reglas puras (`scheduling/rules.py`, `payments/rules.py`), puertos ABC y errores de dominio. `allocation.py` (motor de agendamiento) se convirtió en servicio de dominio con DI. `retrieval.py`, `prompts.py` y `answer.py` (RAG) quedaron como funciones puras. |
| `backend/application/**` | Casos de uso por contexto con dependencias por constructor: `AuthService`, `BusinessService`, `StaffService`, `BayService`, `PartService`, `ServiceCatalogService`, `VehicleService`, `AppointmentService`, `PaymentService`, `TrackingService`, `AiAssistantService`. |
| `backend/infrastructure/**` | Modelos ORM (movidos sin cambios de esquema), repositorios SQLAlchemy como adaptadores (`SqlAlchemyRepository` mapea filas a entidades), `SqlAlchemyUnitOfWork`, `SystemClock`, `WerkzeugPasswordHasher` y `GeminiGateway` (antes `services/llm_client.py`). |
| `backend/api/**` | Rutas antiguas y v1 reescritas como adaptadores delgados, `SessionUser` (Flask-Login sin acoplar el ORM) y un manejador único de errores de dominio → HTTP. |
| `backend/bootstrap.py` | Composition root único. |
| `backend/tests/test_legacy_routes.py` | 7 pruebas de caracterización de rutas que no tenían cobertura. |
| `backend/tests/test_architecture.py` | Reglas de dependencias verificadas con `ast`. |

### Cómo se verificó que no se rompió nada

1. Las 31 pruebas existentes pasan sin cambiar ninguna aserción; solo se actualizaron los imports a las rutas nuevas.
2. Las 7 pruebas nuevas de caracterización se corrieron primero contra el código **original** (worktree en el commit `45b5a4f`, 7/7 en verde) y después contra el refactor (7/7 en verde).
3. `flask db check`: *No new upgrade operations detected*, es decir, el esquema no cambió.
4. `scripts/export_openapi.py`: `docs/openapi.json` sin diferencias.
5. Prueba de humo de la app real contra la base de desarrollo: login y 7 rutas protegidas con respuesta 200.
6. Prueba de mutación de la regla de arquitectura: se añadió `import flask` a `domain/payments/rules.py`, la prueba falló como se esperaba y luego se revirtió.

### Errores de la IA detectados durante la fase (reales)

| Error | Cómo se detectó | Corrección |
|---|---|---|
| En `ServiceCatalogService.create` quedaron 3 líneas sin sentido (`hasattr(self._business, 'get_owned_or_none')`, un método que no existe) | Revisión del propio código antes de correr las pruebas | Se eliminaron |
| `scripts/run_prompt_eval.py` usaba una variable `assistant` que no estaba definida tras cambiar los imports | Revisión de los usos con `grep` | Se pasa el servicio como parámetro de `run_case` |
| El docstring de `test_legacy_routes.py` afirmaba que las pruebas se escribieron "antes del refactor", y no era cierto | Relectura | Se cambió a lo que realmente ocurrió: se escribieron durante el refactor y se validaron contra el código original |

### Decisiones de diseño que Pablo debe revisar y poder defender

- **Mensajes de error en la capa de aplicación:** los casos de uso conservan los textos en español de las rutas antiguas y en inglés de `/api/v1`, para no cambiar el contrato del frontend. La alternativa (traducir por `code` en la api) se descartó por alcance.
- **`TrackingService.record_step`** valida todos los repuestos *antes* de escribir. El código original creaba el registro y hacía `rollback` si fallaba. El resultado HTTP es el mismo y el stock no cambia en los intentos fallidos (lo prueba `test_tracking_records_steps_and_discounts_stock`).
- **`api` puede importar `domain`** (por ejemplo, las constantes de prompts para el esquema Marshmallow, o `Actor`), pero no `infrastructure`.

**[COMPLETAR]** Qué revisó Pablo personalmente y qué cambiaría.

---

## Fase 2 – Inyección de dependencias y pruebas unitarias con mocks

La guía pide "Mockito"; el stack confirmado es Python, así que se usó `unittest.mock` (librería estándar).

### Código generado por la IA

| Archivo | Qué prueba |
|---|---|
| `tests/unit/test_appointment_service.py` | `AppointmentService` con sus 6 dependencias simuladas: asignación, 2 pagos 30/70, un solo commit, nada escrito si no hay disponibilidad, reglas de cancelación y permisos del mecánico |
| `tests/unit/test_payment_service.py` | `PaymentService` con `Clock` simulado: el depósito confirma la cita, el saldo no; pagos inválidos no escriben |
| `tests/unit/test_resource_allocator.py` | Servicio de dominio con puertos simulados: primera bahía y primer mecánico libres; no consulta mecánicos si no hay bahía |
| `tests/unit/test_tracking_service.py` | El descuento de stock es todo o nada |
| `tests/unit/test_ai_assistant_service.py` | El LLM simulado como puerto: precios del catálogo, ids inventados descartados, fallos registrados, cuota con reloj inyectado |
| `tests/unit/test_domain_rules.py` | Reglas puras, sin mocks |
| `tests/conftest.py`, `tests/integration/conftest.py` | Separación: las fixtures que truncan PostgreSQL solo aplican a `integration/` |

### Verificación

- 43 pruebas unitarias en 0.3 s. También pasan con una `DATABASE_URL` inválida, lo que demuestra que no tocan la base.
- **Prueba de mutación:** con `DEPOSIT_PERCENTAGE = 0.4` fallan 3 pruebas, justo las del 30/70. Luego se revirtió.
- La suite completa da 81 en verde (38 de integración + 43 unitarias).

### Decisión técnica a defender

Se usó `create_autospec(Puerto, instance=True)` en lugar de `Mock()`. Un `Mock()` acepta cualquier método y firma, y no detectaría que el servicio usa algo que el puerto no declara. Lo demuestra `test_autospec_mocks_enforce_the_port_contract`.

**[COMPLETAR]** Experiencia personal de Pablo con las pruebas unitarias.

---

## Fase 3 – APIs colombianas, circuit breaker y retry

### Verificación previa de las APIs (llamadas reales del 2026-10-24, antes de escribir código)

| Fuente | Endpoint | Resultado real |
|---|---|---|
| RUNT, parque automotor (MinTransporte) | `datos.gov.co/resource/u3vn-bdcy.json` | 191 922 filas, 22 655 040 vehículos, publicación de octubre de 2026; 28 007 filas agregadas por departamento, clase y año |
| DIVIPOLA (DANE) | `datos.gov.co/resource/gdxc-w37w.json` | 1 122 municipios, 33 departamentos |
| Población CNPV 2018 (DANE) | `geoportal.dane.gov.co/.../Serv_Mpios_DistribucionPoblacionTotalCen_2018/MapServer/4/query` | 1 122 municipios, 44 164 417 personas censadas |
| Descartadas | precios de combustible `x6id-4v3g` (2018), IPC del geoportal (2012–2013) | Desactualizadas |

**Primer error de la IA en esta fase:** la primera consulta SoQL codificó toda la cadena (incluidos los `&`) en un solo parámetro y Socrata respondió `400 query.compiler.malformed`. Se corrigió pasando cada parámetro por separado. El error se detectó por la respuesta HTTP real.

**Hallazgo de datos:** en el cruce RUNT ↔ DIVIPOLA, "BOGOTA D.C." no coincide con "BOGOTA, D.C." y San Andrés aparece truncado en RUNT. Se resolverá normalizando a solo letras y uniendo por prefijo (Fase 4).

### Código generado por la IA

| Archivo | Contenido |
|---|---|
| `infrastructure/resilience/circuit_breaker.py` | Breaker de 3 estados, umbral de fallos, timeout de recuperación, una sola prueba en HALF_OPEN, historial de transiciones, reloj inyectable y lock entre hilos |
| `infrastructure/resilience/retry.py` | `RetryPolicy` + `retry_call`: backoff exponencial con *equal jitter*, tope `max_delay` y lista de excepciones reintentables |
| `infrastructure/resilience/http_client.py` | httpx con retry por fuera y breaker por dentro; clasifica los errores en transitorios (timeout, conexión, 429, 5xx) y permanentes (otros 4xx) |
| `infrastructure/market_data/clients.py` | Adaptadores Socrata (paginación `$limit/$offset`) y ArcGIS (paginación `resultOffset` y errores dentro de un HTTP 200) |
| `domain/market_data/`, `application/market_data/` | Puertos y caso de uso `MarketDataService` (una fuente caída no detiene a las demás) |
| `scripts/demo_resilience.py` | **Demostración controlada** con red real |
| `tests/fixtures/market/` | Respuestas **reales** recortadas de las 3 fuentes, para pruebas sin red |

### Verificación

- 23 pruebas nuevas (breaker, retry, cliente HTTP con `httpx.MockTransport`, fuentes y caso de uso): 104 en verde en total.
- **Mutación:** con `>` en lugar de `>=` en el umbral del breaker fallan 4 pruebas. Luego se revirtió.
- Adaptadores contra las APIs reales: RUNT 28 007 filas (1,1 s), DIVIPOLA 1 122 (0,27 s), DANE 1 122 (1,1 s).
- `demo_resilience.py` con red real: separación entre intentos de 0,317 / 0,607 / 1,101 / 3,416 s; transiciones CLOSED→OPEN→HALF_OPEN→OPEN→HALF_OPEN→CLOSED; rechazo en ~35 µs con el circuito abierto.

### Decisiones a defender

- **Un breaker por host** (datos.gov.co y geoportal.dane.gov.co): la caída de uno no bloquea al otro.
- **Retry por fuera y breaker por dentro**, y `CircuitOpenError` no se reintenta: no tiene sentido esperar un backoff si ya se sabe que la dependencia está caída.
- **Un 4xx no abre el circuito**: indica un error de la petición, no de la salud de la dependencia.
- **RUNT se agrega en el servidor** (SoQL `group by`): 3 MB en vez de ~27 MB, porque el detalle por municipio no se usa.

**[COMPLETAR]** Opinión de Pablo sobre las decisiones anteriores.

---

## Fase 4 – DuckDB, endpoints y visualización

### Código generado por la IA

| Archivo | Contenido |
|---|---|
| `infrastructure/analytics/queries.py` | 3 consultas SQL: antigüedad del parque por clase (estadísticas **ponderadas**: media, desviación, P25, mediana, P75, P90, mín./máx.), motorización por departamento (RUNT ⋈ DIVIPOLA ⋈ CNPV con resumen entre departamentos) y distribución por rangos |
| `infrastructure/analytics/duckdb_analytics.py` | Adaptador `MarketAnalytics`: `read_json` + `unnest` sobre los snapshots, una conexión en memoria por consulta |
| `api/v1/market.py`, `api/v1/schemas/market_schema.py` | 5 endpoints documentados en OpenAPI (owner/admin) |
| `frontend/pages/mercado.html`, `js/mercado.js`, `js/graficos.js` | Vista vanilla: estado de los breakers, tablas, KPIs y 2 gráficos en Canvas (barras horizontales con referencia nacional y apiladas al 100 %) con tooltip |

**Dependencia nueva:** `duckdb==1.5.6`. Se descartó la 2.0.0 porque era una versión mayor publicada 3 días antes (2026-10-21); la 1.5.6 es del 2026-09-28 y tiene wheels para Python 3.12 (CI) y 3.14 (local).

### Errores de la IA detectados en esta fase

| Error | Cómo se detectó | Corrección |
|---|---|---|
| `CREATE VIEW ... read_json(?)` con parámetro preparado: DuckDB lo rechaza (`Unexpected prepared parameter`) | Ejecución real | Literal SQL escapado; el path sale de la configuración |
| `LEFT JOIN` con `NOT EXISTS` correlacionado: `Cannot perform non-inner join on subquery` | Ejecución real | Se resuelve primero la clave DIVIPOLA (exacta o por prefijo) y luego un join simple |
| Una línea absurda en `api/v1/market.py` (`... if False else decorate`) | Revisión del código | Eliminada |
| Código del tooltip duplicado en `graficos.js` | Revisión del código | Unificado en `canvas._buscar` |
| Capturas de Playwright: tabla de fuentes desbordada, columna cortada, valores tapados por la línea nacional y el "100 %" del eje recortado | Revisión visual de la captura | CSS de tablas compactas, halo en las etiquetas, margen derecho |
| La prueba de interacción falló dos veces, por errores **de la prueba** y no de la app: el canvas estaba fuera del viewport y hubo una carrera al leer la tabla | Depuración con `page.evaluate` | `scroll_into_view_if_needed()` y esperar a la insignia |

### Verificación con datos reales (snapshot del 2026-10-24)

- **Q1:** 22 054 289 vehículos, 9 clases; mediana de 9 años en motos y de 16 en automóviles; 8 864 excluidos por calidad (registro < 1950). 89,5 ms.
- **Q2:** 33 departamentos (Vaupés sin registros en RUNT); 499,4 vehículos por 1 000 hab. a nivel nacional; media 514,8, mediana 446,5, desviación 343,9. ~100 ms.
- **Validación cruzada:** las estadísticas ponderadas coinciden **exactamente** con `quantile_disc`/`stddev_pop` de DuckDB sobre los datos expandidos a una fila por vehículo (22 M filas, 1,1 s), en las 9 clases. El total de la Q2 es igual al de la Q1: el cruce no pierde ni duplica vehículos.
- **Interpretación (advertencia en la UI):** RUNT ubica el vehículo donde se matriculó. Por eso Guaviare (2 021, 99 % motos) y Cundinamarca (1 000) superan a Bogotá (387).
- **Pruebas:** 11 nuevas (adaptador DuckDB con fixtures reales, regla del cruce por prefijo y endpoints con red simulada, incluido un corte de datos.gov.co que abre su breaker mientras el del DANE sigue CLOSED). Total: 115 en verde.
- **Gráficos:** colores verificados con el validador de paletas (rampa ordinal de un solo tono, luminosidad monótona, paso más claro ≥ 2:1). Se comprobaron en Playwright el tooltip, el botón de actualizar (descarga real: 1 632 / 274 / 880 ms) y la vista móvil de 390 px sin scroll horizontal.

**[COMPLETAR]** Qué conclusiones saca Pablo para el negocio del taller.

---

## Fases siguientes

*(Se completan al terminar cada fase.)*
