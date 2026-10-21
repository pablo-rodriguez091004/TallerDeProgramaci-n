# Evidencias — Guía de Laboratorio 5 (MecaTrack)

Todo lo de esta carpeta sale de ejecuciones reales. Para regenerarlo:
`./scripts/run_all.sh` (sin costo) o `./scripts/run_all.sh --with-llm` (repite las 31 llamadas al LLM).

## Checklist por criterio de evaluación

| % | Criterio | Estado | Dónde está |
|---|---|---|---|
| 25 | API REST: 5 endpoints CRUD, errores HTTP, ≥ 3 pruebas de integración | ✅ | `backend/api/v1/services.py`, `backend/tests/test_api_v1_services.py`, `pytest_output.txt`, capturas 04–07 |
| 15 | OpenAPI 3.0 en inglés + Swagger UI (summary, description, examples) | ✅ | `/docs`, `/openapi.json`, `../docs/openapi.json`, `backend/tests/test_openapi.py`, capturas 01–02 |
| 25 | `/api/v1/ai` funcional, timeout y rate limit, ≥ 10 llamadas reales | ✅ | `backend/api/v1/ai.py`, `backend/services/`, `ai_calls_export.csv` (38 llamadas), captura 08 |
| 15 | Tabla de 3 técnicas de prompting con evaluación | ✅ | `prompt_eval/cases.json`, `prompt_eval/results.json` y `.csv`, informe (Tablas 6 y 7) |
| 10 | Estimación de costos en inglés (precio, tokens, proyección) | ✅ | `cost_estimate_EN.md`, `cost_estimate.json`, informe (sección *LLM Cost Estimate*) |
| 5 | Informe Word APA 7 con las preguntas orientadoras | ⚠️ faltan tus datos | `../informe/Informe_Guia5_MecaTrack.docx` |
| 5 | Video en inglés | ⏳ por grabar | Guion: `video_script_EN.md` |

## Pendiente del estudiante

- [ ] Portada del informe: **nombre completo, código** (y de otros integrantes) y **nombre del docente** (resaltados en amarillo).
- [ ] `git push` de la rama `mecatrack-final` y **captura del CI en verde** (pestaña *Actions*) en el marcador de la sección *Pruebas de integración* del informe. Guárdala también como `screenshots/10_ci_green.png`.
- [ ] Párrafo con tu **experiencia real con GitHub Copilot** (informe, pregunta 4) y la sección 3 del guion del video.
- [ ] Grabar el **video** (2–3 min, en inglés) y pegar el enlace en la sección *Enlaces* del informe.
- [ ] Revisar y ajustar la **Declaración de uso de IA** (borrador al final del informe).
- [ ] Verificar el enlace del repositorio en la sección *Enlaces*.
- [ ] Opcional: decidir si la técnica por defecto del endpoint pasa de `few_shot` a `zero_shot` (el experimento mostró igual precisión con menor costo).

> El informe se genera con `informe/build_informe.js`. Si editas el `.docx` a mano en Word,
> **no vuelvas a correr** `run_all.sh` ni `npm run build`, porque sobrescribe el archivo.
> Alternativa: completa los campos en el `.docx` al final, cuando ya no vayas a regenerarlo.

## Contenido de esta carpeta

| Archivo | Qué es | Lo genera |
|---|---|---|
| `pytest_output.txt` | Salida real de las 31 pruebas (fecha, commit y versión de Python en el encabezado) | `scripts/run_tests.sh` |
| `prompt_eval/cases.json` | 10 síntomas con el servicio esperado (aprobados antes del experimento) | a mano |
| `prompt_eval/results.json` / `.csv` | 30 llamadas reales: prompt, respuesta, aciertos, tokens, latencia | `scripts/run_prompt_eval.py` |
| `cost_estimate_EN.md` / `.json` | Costo por llamada y proyección mensual, con fuente y fecha del precio | `scripts/cost_estimate.py` |
| `ai_calls_export.json` / `.csv` | Exportación de la tabla `ai_calls` (todas las llamadas reales) | `scripts/export_ai_calls.py` |
| `screenshots/01–09_*.png` | Swagger UI, respuestas 200/404/422/409, IA y frontend | `scripts/capture_screenshots.sh` |
| `video_script_EN.md` | Guion del video con los números reales | a mano |

## Datos clave (para la sustentación)

- Modelo: `gemini-3.5-flash-lite` (Google Gemini API), temperatura 0,2. Precio de la capa de pago: US$0.30 / 1M tokens de entrada y US$2.50 / 1M de salida (https://ai.google.dev/gemini-api/docs/pricing, actualizada el 2026-10-19, consultada el 2026-10-20).
- Las tres técnicas: 90 % de precisión top-1. Costo mensual (50 consultas/día): zero-shot $0.44, few-shot $0.66, CoT $0.88.
- Único fallo (caso 9, embrague): lo causó la recuperación por palabras clave, no el prompt. Se documentó y no se ajustó el diccionario a los casos de prueba.
- Un 503 real del proveedor durante el experimento se recuperó con el reintento con backoff.
