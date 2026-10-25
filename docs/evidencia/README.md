# Evidencia – Guía 6 (Sesiones 11 y 12)

Todas las imágenes salen de ejecuciones **reales** y se regeneran con `./scripts/generar_evidencia.sh`.
La salida de texto de cada comando queda en `salidas/` (misma ejecución que la imagen).

| Archivo | Requisito de la guía | Qué muestra | Origen |
|---|---|---|---|
| `01_estructura_hexagonal.png` | a) 4 capas | `tree` de domain / application / api / infrastructure y archivos por capa | `tree`, `find` |
| `02_pytest_verde.png` | d) pytest en verde | Suite completa con el conteo de pruebas | `pytest -q` |
| `03_puerto_y_adaptador.png` | b) puerto y adaptador | `AppointmentRepository` (ABC) y `SqlAlchemyAppointmentRepository` | código real con números de línea |
| `04_servicio_di_constructor.png` | c) DI por constructor | `AppointmentService.__init__` + `book()` y el composition root | código real |
| `05_test_con_mock.png` | c) test con mocks | Fixture con `create_autospec` y ejecución de 19 pruebas | código + `pytest` |
| `06_api_datos_gov_co.png` | e) API 1 | RUNT y DIVIPOLA respondiendo (JSON recortado a 3 registros) | `consultar_apis.py` |
| `07_api_dane.png` | e) API 2 | Geoportal del DANE, CNPV 2018 (JSON recortado) | `consultar_apis.py` |
| `08_circuit_breaker_estados.png` | f) 3 estados | CLOSED → OPEN → HALF_OPEN → OPEN → HALF_OPEN → CLOSED con marcas de tiempo | `demo_resilience.py` (**demostración controlada**) |
| `09_circuit_breaker_pruebas.png` | f) pruebas de transiciones | Pruebas del breaker, del retry y del cliente HTTP | `pytest` |
| `10_retry_backoff.png` | g) backoff exponencial | Tiempos reales entre intentos (misma ejecución que la 08) | `demo_resilience.py` |
| `11_duckdb_q1_antiguedad.png` | h) query DuckDB 1 | SQL + resultado (estadísticas ponderadas) | `consultas_duckdb.py q1` |
| `12_duckdb_q2_motorizacion.png` | h) query DuckDB 2 | SQL + resultado + resumen entre departamentos | `consultas_duckdb.py q2` |
| `13a_ui_mercado_fuentes_motorizacion.png` | i) UI | Breakers, fuentes, KPIs y gráfico de barras (Canvas) | Playwright sobre la app real |
| `13b_ui_mercado_antiguedad.png` | i) UI | Tabla de estadísticas y gráfico apilado (Canvas) | Playwright |
| `14_ui_circuit_breaker_abierto.png` | f) breaker en la UI | datos.gov.co **OPEN** y el DANE **CLOSED** | Playwright; **demostración controlada** (`MARKET_SOCRATA_BASE_URL` → host `.invalid`) |
| `15_ci_verde.png` | j) CI | Run de GitHub Actions en verde (ver `salidas/15_ci_run.json`) | GitHub (repo público) |
| `16_adr.png` | k) ADR en inglés | ADR 0001 renderizado en GitHub (secciones 1 a 2.1) | GitHub |
| `17_swagger_market.png` | extra | Endpoints `/api/v1/market` en Swagger UI | Playwright |

**Seguridad:** antes de guardar cada imagen, `scripts/evidencia/render.py` y `capturar.py` comprueban que el contenido no incluya valores de `backend/.env` (contraseña de la BD, `SECRET_KEY`, claves de API). Si alguno aparece, se aborta.
