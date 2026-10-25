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

## Fases siguientes

*(Se completan al terminar cada fase.)*
