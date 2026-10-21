// Genera informe/Informe_Guia5_MecaTrack.docx (normas APA 7) con la libreria docx.
// Todos los numeros, tablas y salidas se LEEN de ../evidence y del codigo: si se
// repite un experimento, basta con volver a correr `npm run build`.
//
// Los campos que debe completar el estudiante van resaltados en amarillo.

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel, ImageRun, LevelFormat,
  PageBreak, PageNumber, Packer, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun,
  WidthType,
} = require('docx');

const ROOT = path.resolve(__dirname, '..');
const EVIDENCE = path.join(ROOT, 'evidence');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const readJson = (p) => JSON.parse(read(p));

const results = readJson('evidence/prompt_eval/results.json');
const cases = readJson('evidence/prompt_eval/cases.json');
const cost = readJson('evidence/cost_estimate.json');
const aiCalls = readJson('evidence/ai_calls_export.json');
const pytestOutput = read('evidence/pytest_output.txt').trimEnd();
const promptsPy = read('backend/services/prompts.py');
const SYSTEM_PROMPT = promptsPy.match(/SYSTEM_PROMPT = """([\s\S]*?)"""/)[1];
const COMMITS = execSync('git log --format="%h %s" master..HEAD', { cwd: ROOT }).toString().trim().split('\n');

const TECHNIQUES = ['zero_shot', 'few_shot', 'cot'];
const TECH_LABEL = { zero_shot: 'Zero-shot', few_shot: 'Few-shot', cot: 'Chain-of-thought' };
const S = results.summary;
const MODEL = results.metadata.model;

// ---------------------------------------------------------------- formato APA
const FONT = 'Times New Roman';
const MONO = 'Consolas';
const PAGE_W = 12240; // Carta
const MARGIN = 1440; // 1 pulgada
const CONTENT_W = PAGE_W - 2 * MARGIN; // 9360 DXA = 6.5 in
const CONTENT_PX = 624; // 6.5 in a 96 px/in
const DOUBLE = 480;
const SINGLE = 240;

// Texto con marcas simples: **negrita**, *cursiva*, `codigo`, [[PENDIENTE]] (resaltado).
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[\[[^\]]+\]\])/g;
  let last = 0;
  let m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith('**')) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    // Sombreado amarillo en vez de `highlight`: docx 9.7 emite <w:highlightCs>, que no valida contra el esquema.
    else if (t.startsWith('[[')) out.push(new TextRun({ text: t.slice(2, -2), shading: { type: ShadingType.CLEAR, fill: 'FFFF00', color: 'auto' }, bold: true, ...base }));
    else if (t.startsWith('*')) out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: MONO, size: (base.size || 24) - 2, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const p = (text, opts = {}) => new Paragraph({
  children: runs(text), spacing: { line: DOUBLE, before: 0, after: 0 }, indent: { firstLine: 720 }, ...opts,
});
const plain = (text, opts = {}) => p(text, { indent: {}, ...opts });
const center = (text, opts = {}) => p(text, { indent: {}, alignment: AlignmentType.CENTER, ...opts });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const h3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
const bullet = (text) => new Paragraph({
  children: runs(text), numbering: { reference: 'bullets', level: 0 }, spacing: { line: DOUBLE },
});
const numbered = (text, ref = 'numbers') => new Paragraph({
  children: runs(text), numbering: { reference: ref, level: 0 }, spacing: { line: DOUBLE },
});
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

function code(text, size = 16) {
  return text.split('\n').map((line, i, all) => new Paragraph({
    children: [new TextRun({ text: line || ' ', font: MONO, size })],
    spacing: { line: SINGLE, before: i === 0 ? 120 : 0, after: i === all.length - 1 ? 240 : 0 },
    shading: { type: ShadingType.CLEAR, fill: 'F2F2F2', color: 'auto' },
    indent: { left: 144, right: 144 },
  }));
}

let tableNo = 0;
let figureNo = 0;
// Numeracion automatica: el contenido se arma dos veces; la primera pasada
// registra el numero de cada tabla (por titulo) y figura (por archivo).
const labels = {};
const tab = (title) => labels[`T:${title}`] ?? '?';
const fig = (file) => labels[`F:${file}`] ?? '?';
// APA: "Tabla N" en negrita y el titulo en cursiva, encima; la nota debajo.
function apaLabel(kind, n, title) {
  return [
    new Paragraph({ children: [new TextRun({ text: `${kind} ${n}`, bold: true })], spacing: { before: 240, line: DOUBLE }, keepNext: true }),
    new Paragraph({ children: [new TextRun({ text: title, italics: true })], spacing: { line: DOUBLE }, keepNext: true }),
  ];
}
const note = (text) => new Paragraph({
  children: [new TextRun({ text: 'Nota. ', italics: true, size: 20 }), ...runs(text, { size: 20 })],
  spacing: { line: SINGLE, before: 80, after: 240 },
});

function table(title, headers, rows, widths, { size = 18, notes } = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  if (total !== CONTENT_W) throw new Error(`Las columnas de "${title}" suman ${total}, no ${CONTENT_W}`);
  const border = { style: BorderStyle.SINGLE, size: 4, color: '999999' };
  const cell = (text, w, header) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    shading: header ? { type: ShadingType.CLEAR, fill: 'D9E2F3', color: 'auto' } : undefined,
    borders: { top: border, bottom: border, left: border, right: border },
    children: String(text).split('\n').map((line) => new Paragraph({
      children: runs(line, { size, bold: header || undefined }), spacing: { line: SINGLE },
    })),
  });
  tableNo += 1;
  labels[`T:${title}`] = tableNo;
  return [
    ...apaLabel('Tabla', tableNo, title),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: widths,
      rows: [
        new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true)) }),
        ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], false)) })),
      ],
    }),
    ...(notes ? [note(notes)] : [new Paragraph({ spacing: { after: 240 }, children: [] })]),
  ];
}

function pngSize(file) {
  const buf = fs.readFileSync(file);
  return { buf, w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

// 650 px (~6,8 in) deja espacio en la pagina de 9 in para el rotulo APA de dos
// lineas y la nota, de modo que no queden separados de la imagen.
function figure(file, title, notes, maxHeightPx = 650) {
  const { buf, w, h } = pngSize(file);
  const scale = Math.min(CONTENT_PX / w, maxHeightPx / h);
  figureNo += 1;
  labels[`F:${path.basename(file)}`] = figureNo;
  return [
    ...apaLabel('Figura', figureNo, title),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      keepNext: !!notes,
      children: [new ImageRun({
        type: 'png', data: buf,
        transformation: { width: Math.round(w * scale), height: Math.round(h * scale) },
        altText: { title, description: title, name: path.basename(file) },
      })],
    }),
    ...(notes ? [note(notes)] : []),
  ];
}
const shot = (name) => path.join(EVIDENCE, 'screenshots', name);

// ------------------------------------------------------------ datos derivados
const fmt = (n, d = 0) => Number(n).toLocaleString('es-CO', { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (x) => `${Math.round(x * 100)} %`;
const usd = (x, d = 6) => `$${Number(x).toFixed(d)}`;
const byTech = Object.fromEntries(TECHNIQUES.map((t) => [t, results.results.filter((r) => r.technique === t)]));
const confidence = Object.fromEntries(TECHNIQUES.map((t) => {
  const all = byTech[t].flatMap((r) => (r.suggestions || []).map((s) => s.confidence));
  return [t, { high: all.filter((c) => c === 'high').length, medium: all.filter((c) => c === 'medium').length,
    low: all.filter((c) => c === 'low').length, total: all.length }];
}));
const notesCount = Object.fromEntries(TECHNIQUES.map((t) => [t, byTech[t].filter((r) => r.notes).length]));
const retried = results.results.filter((r) => (r.attempts || 1) > 1);
const avgNoRetry = (t) => {
  const xs = byTech[t].filter((r) => r.status === 'success' && (r.attempts || 1) === 1).map((r) => r.latency_ms);
  return Math.round(xs.reduce((a, b) => a + b, 0) / xs.length);
};
const failedCases = cases.filter((c) => TECHNIQUES.every((t) => !byTech[t].find((r) => r.case_id === c.id).hit_top1));
const caseRow = (id, t) => byTech[t].find((r) => r.case_id === id);
const callsByStatus = aiCalls.reduce((acc, c) => ({ ...acc, [c.status]: (acc[c.status] || 0) + 1 }), {});
const evalCalls = aiCalls.filter((c) => c.source === 'eval').length;
const apiCalls = aiCalls.filter((c) => c.source === 'api').length;
const passedTests = (pytestOutput.match(/ PASSED/g) || []).length;
const testsSummary = pytestOutput.split('\n').filter((l) => /passed|failed/.test(l) && l.startsWith('=')).pop();
const ccost = cost.by_technique;

// ------------------------------------------------------------------ contenido
function buildContent() {
tableNo = 0;
figureNo = 0;
const children = [];
const add = (...items) => items.flat().forEach((i) => children.push(i));

// 1. Portada (APA 7, trabajo de estudiante)
add(
  ...Array.from({ length: 3 }, () => new Paragraph({ spacing: { line: DOUBLE }, children: [] })),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { line: DOUBLE, after: 480 },
    children: [new TextRun({ text: 'Guía de Laboratorio 5: API REST con OpenAPI 3.0 e Integración de un Modelo de Lenguaje en MecaTrack', bold: true })],
  }),
  center('[[NOMBRE COMPLETO DEL ESTUDIANTE]] — Código [[CÓDIGO]]'),
  center('[[NOMBRE COMPLETO DE OTRO INTEGRANTE, SI APLICA]] — Código [[CÓDIGO]]'),
  center('Facultad de Ingeniería, Universidad Manuela Beltrán (UMB)'),
  center('Taller de Programación — Sesiones 9 y 10'),
  center('Docente: [[NOMBRE DEL DOCENTE]]'),
  center('20 de octubre de 2026'),
  pageBreak(),
);

// 2. Introduccion y objetivos
add(
  center('Guía de Laboratorio 5: API REST con OpenAPI 3.0 e Integración de un Modelo de Lenguaje en MecaTrack', { children: [new TextRun({ text: 'Guía de Laboratorio 5: API REST con OpenAPI 3.0 e Integración de un Modelo de Lenguaje en MecaTrack', bold: true })] }),
  h1('Introducción'),
  p('MecaTrack es un sistema de citas y seguimiento de vehículos para un taller mecánico, construido con Flask, SQLAlchemy y PostgreSQL, con un frontend en HTML, CSS y JavaScript sin frameworks. En esta guía se le agregó una API REST versionada bajo `/api/v1`, documentada con la especificación OpenAPI 3.0 y publicada con Swagger UI, y un asistente basado en un modelo de lenguaje (LLM) que, a partir del síntoma que describe un cliente, sugiere servicios del catálogo del taller con su precio y duración.'),
  p(`El trabajo se hizo por fases, cada una con pruebas automáticas y un commit propio en la rama \`mecatrack-final\`. Todas las cifras de este informe (pruebas, llamadas al modelo, tokens, latencias y costos) provienen de ejecuciones reales guardadas en la carpeta \`evidence/\` del repositorio; el informe se genera a partir de esos archivos con el script \`informe/build_informe.js\`.`),
  h2('Objetivos'),
  bullet('Exponer un CRUD de 5 endpoints sobre el catálogo de servicios con códigos HTTP correctos y un formato de error único.'),
  bullet('Documentar la API con OpenAPI 3.0 en inglés (summary, description y ejemplos en cada endpoint) y publicarla con Swagger UI.'),
  bullet('Integrar un LLM en `/api/v1/ai` con recuperación aumentada (RAG), manejo de timeout y límites de uso, y registro de cada llamada.'),
  bullet('Comparar tres técnicas de prompting (zero-shot, few-shot y chain-of-thought) con datos reales y estimar el costo mensual del modelo.'),
  bullet('Verificar todo con pruebas de integración que se ejecutan en GitHub Actions sin depender del proveedor del LLM.'),
);

// 3. Arquitectura
add(
  h1('Arquitectura'),
  p('La API nueva convive con las rutas existentes (`/services`, `/auth`, `/appointments`, etc.), que el frontend sigue usando sin cambios. Se mantuvo Flask y la especificación OpenAPI se genera con flask-smorest, que valida las entradas y salidas con esquemas Marshmallow y produce el documento OpenAPI a partir del mismo código; así la documentación no puede quedar desactualizada respecto a la implementación sin que las pruebas lo detecten.'),
  p('La Figura ' + fig('arquitectura.png') + ' muestra el flujo de una consulta al asistente. El cliente envía la descripción del problema; el endpoint valida la sesión, el cuerpo y el límite por usuario; la etapa de recuperación consulta los servicios activos en PostgreSQL y elige los más relevantes; el módulo de prompts arma la instrucción con ese contexto; el modelo responde un JSON; el backend valida la respuesta, completa precio y duración desde la base de datos y registra la llamada en la tabla `ai_calls`.'),
  figure(path.join(__dirname, 'arquitectura.png'), 'Flujo de POST /api/v1/ai/suggest-service', 'Diagrama elaborado con Graphviz (`informe/arquitectura.dot`). La línea discontinua indica las lecturas y escrituras en la base de datos después de la respuesta del modelo.', 560),
  h2('Componentes principales'),
  ...table('Archivos que implementan la guía', ['Componente', 'Archivo(s)', 'Responsabilidad'], [
    ['API v1 y errores', '`backend/api/__init__.py`, `backend/api/errors.py`', 'Registro de blueprints, especificación OpenAPI, formato único de error solo bajo `/api/`.'],
    ['CRUD de servicios', '`backend/api/v1/services.py`, `backend/schemas/service_schema.py`', 'Cinco endpoints, validación Marshmallow, reglas 404/409/422.'],
    ['Asistente IA', '`backend/api/v1/ai.py`, `backend/services/ai_service.py`', 'Orquestación RAG, límite por usuario, mapeo de errores a HTTP.'],
    ['Recuperación', '`backend/services/retrieval.py`', 'Puntaje por palabras clave y sinónimos de síntomas.'],
    ['Prompts', '`backend/services/prompts.py`', 'Prompt de sistema y variantes zero-shot, few-shot y CoT.'],
    ['Cliente LLM', '`backend/services/llm_client.py`', 'SDK google-genai, timeout, reintentos con backoff, conteo de tokens.'],
    ['Bitácora', '`backend/models/ai_call_model.py` + migración `0243525bf206`', 'Tabla `ai_calls`.'],
    ['Pruebas y CI', '`backend/tests/`, `.github/workflows/mecatrack-tests.yml`', `${passedTests} pruebas de integración con PostgreSQL.`],
  ], [1900, 3600, 3860]),
);

// 4. API REST
add(
  h1('API REST'),
  p('La Tabla ' + tab('Endpoints del catálogo de servicios') + ' resume los cinco endpoints del CRUD. La lectura es pública porque el catálogo se muestra antes de iniciar sesión; la escritura exige los roles `owner` o `admin` mediante el mismo decorador `role_required` que usan las rutas antiguas, que dentro de `/api/v1` responde con el formato nuevo. El chequeo de rol se ejecuta antes que la validación, de modo que un usuario anónimo con un cuerpo inválido recibe 401 y no 422.'),
  ...table('Endpoints del catálogo de servicios', ['Método', 'Ruta', 'Descripción', 'Auth', 'Códigos HTTP'], [
    ['GET', '`/api/v1/services`', 'Lista servicios; filtro `status` = active (defecto), inactive o all.', 'Pública', '200, 422'],
    ['GET', '`/api/v1/services/{id}`', 'Obtiene un servicio activo o inactivo.', 'Pública', '200, 404'],
    ['POST', '`/api/v1/services`', 'Crea un servicio en el taller del usuario.', 'owner, admin', '201, 401, 403, 409, 422'],
    ['PUT', '`/api/v1/services/{id}`', 'Reemplaza todos los campos editables (no es un PATCH).', 'owner, admin', '200, 401, 403, 404, 409, 422'],
    ['DELETE', '`/api/v1/services/{id}`', 'Borra un servicio sin citas; si tiene citas responde 409.', 'owner, admin', '204, 401, 403, 404, 409'],
  ], [900, 2200, 3360, 1200, 1700], { notes: 'El 409 de POST/PUT se produce si el nombre ya existe en el taller sin distinguir mayúsculas; la migración `ec27632baa28` agrega además la restricción `UNIQUE(business_id, service_name)` para el caso de dos peticiones simultáneas. La ruta antigua `DELETE /services/{id}` conserva su borrado lógico.' }),
  h2('Formato único de error'),
  p('Todas las respuestas de error bajo `/api/` tienen la misma forma, incluidas las de rutas inexistentes (404) y métodos no permitidos (405). El campo `code` es estable y sirve para que un cliente tome decisiones; `message` es legible para una persona; `details` lleva contexto, como los errores por campo de una validación:'),
  ...code('{\n  "code": "validation_error",\n  "message": "The request body is invalid",\n  "details": {\n    "service_name": ["Shorter than minimum length 2."],\n    "base_price": ["Must be greater than or equal to 0 and less than or equal to 100000000."]\n  }\n}'),
  p('Las rutas antiguas no se modificaron y siguen respondiendo `{"error": "..."}`, que es lo que lee el frontend; una prueba de integración verifica ambos comportamientos.'),
  h2('Documentación OpenAPI y Swagger UI'),
  p('La especificación (OpenAPI 3.0.3, en inglés) se sirve en `/openapi.json` y Swagger UI en `/docs`. Cada operación tiene summary, description, ejemplos de petición y de respuesta, y todas sus respuestas de error documentadas; cada campo de los esquemas tiene description y example. El script `scripts/export_openapi.py` exporta el documento a `docs/openapi.json` y lo valida con openapi-spec-validator; la prueba `tests/test_openapi.py` falla si algún endpoint o campo queda sin documentar, y el CI comprueba que el archivo exportado coincida con el código. Las rutas `/auth/login` y `/auth/logout` se documentaron a mano para poder iniciar sesión desde Swagger UI y probar las operaciones protegidas.'),
  figure(shot('01_swagger_overview.png'), 'Swagger UI de la API de MecaTrack', 'Captura tomada con Playwright (Chromium headless) sobre el servidor local, `scripts/capture_screenshots.sh`.'),
  figure(shot('02_swagger_post_docs_examples.png'), 'Documentación de POST /api/v1/services con ejemplos y respuestas de error', null),
  figure(shot('05_get_service_404.png'), 'Respuesta real 404 con el formato único de error'),
  figure(shot('06_post_service_422.png'), 'Respuesta real 422 con el detalle de cada campo inválido', 'La petición se hizo con la sesión del dueño iniciada desde Swagger UI.'),
  figure(shot('07_delete_service_409.png'), 'Respuesta real 409 al intentar borrar un servicio con citas asociadas'),
  figure(shot('04_get_services_200.png'), 'Respuesta real 200 del listado de servicios', null),
  figure(shot('09_frontend_catalogo.png'), 'El frontend existente sigue mostrando el catálogo', 'La página `catalogo.html` usa la ruta antigua `/services`; muestra los 12 servicios del catálogo ampliado para esta guía (`database/catalog.sql`).'),
);

// 5. Pruebas
const required = [
  ['1', '`test_post_creates_service_and_get_reads_it`', 'Con la sesión del dueño, POST crea un servicio (201) y GET lo lee (200) con exactamente el mismo cuerpo.'],
  ['2', '`test_get_unknown_id_returns_404_with_error_format`', 'GET de un id inexistente responde 404 con `code = not_found` y `details = {"service_id": 9999}`.'],
  ['3', '`test_post_invalid_body_returns_422_with_field_details`', 'POST con nombre vacío, duración de texto, precio negativo y un campo desconocido responde 422 y lista los cuatro campos.'],
  ['+', '`test_delete_returns_204_404_and_409_when_booked`', 'DELETE responde 204, luego 404, y 409 cuando el servicio tiene una cita creada por el flujo real de agendamiento.'],
];
add(
  h1('Pruebas de integración'),
  p('Las pruebas usan pytest y recorren la aplicación real (Flask, SQLAlchemy y PostgreSQL) contra una base aparte `taller_mecanico_test`, creada con las mismas migraciones de Alembic que el proyecto; `conftest.py` aborta si el nombre de la base no termina en `_test`. Antes de cada prueba se vacían las tablas y se cargan usuarios, negocio, bahía y un servicio. La Tabla ' + tab('Pruebas mínimas de la guía') + ' describe las tres pruebas mínimas que pide la guía y una adicional del 409.'),
  ...table('Pruebas mínimas de la guía', ['#', 'Prueba', 'Qué verifica'], required, [500, 4000, 4860]),
  p(`En total hay ${passedTests} pruebas: 9 del CRUD v1, 15 del asistente de IA, 4 de la especificación OpenAPI y 3 de las rutas anteriores del proyecto. Las pruebas del asistente reemplazan solo la función que habla con la red (\`llm_client._call_model\`), por lo que la recuperación, los prompts, los reintentos, el mapeo de errores y la bitácora se ejecutan de verdad; además, un fixture automático hace fallar cualquier prueba que intente llamar al proveedor real. La salida real de la última ejecución es:`),
  ...code(pytestOutput, 14),
  h2('Integración continua'),
  p('El workflow `.github/workflows/mecatrack-tests.yml` levanta un servicio `postgres:16`, instala las dependencias con Python 3.12, ejecuta pytest, publica el reporte JUnit como artefacto y vuelve a exportar la especificación OpenAPI para comprobar que `docs/openapi.json` coincida con el código. La variable `GEMINI_API_KEY` se define vacía a propósito. Antes de subir los cambios, el workflow se verificó con actionlint 1.7.12 y se replicó localmente en contenedores `python:3.12` y `postgres:16` (Podman), sin archivo `.env`, con las 31 pruebas en verde.'),
  plain('[[PENDIENTE: insertar aquí la captura del workflow en verde en GitHub Actions (pestaña Actions del repositorio, después de hacer push de la rama).]]', { alignment: AlignmentType.CENTER }),
);

// 6. Integracion LLM
const shownCalls = aiCalls.filter((c) => c.source === 'api' || c.ai_call_id <= 18);
add(
  h1('Integración del modelo de lenguaje'),
  p(`El endpoint \`POST /api/v1/ai/suggest-service\` recibe \`{"description": "...", "technique": "zero_shot | few_shot | cot"}\` (técnica opcional, por defecto few_shot) y requiere sesión. El proveedor es Google Gemini a través de su SDK oficial \`google-genai\`; el modelo se configura con la variable \`GEMINI_MODEL\` y en las pruebas reales se usó \`${MODEL}\`, recomendado por Google para proyectos nuevos y con capa gratuita. La key vive solo en \`backend/.env\`, que está en \`.gitignore\`; el repositorio incluye \`.env.example\` sin valores.`),
  h2('Diseño del RAG'),
  numbered('**Recuperación.** Se normaliza la descripción (minúsculas, sin tildes, sin palabras vacías), se reduce cada palabra a sus primeras 4 letras y se expande con un diccionario de sinónimos de síntomas escrito con conocimiento general de mecánica (por ejemplo, “chillido” → freno, pastilla). Cada servicio activo recibe un puntaje: 2 por raíz compartida con el nombre y 1 por raíz compartida con la descripción. Se envían los 5 mejores; si ninguno coincide, se envía el catálogo activo completo.', 'rag'),
  numbered('**Aumento.** El contexto se inyecta como líneas `[id] nombre - descripción`, sin precios, para que el modelo no tenga cifras que repetir.', 'rag'),
  numbered('**Generación restringida.** El prompt de sistema exige recomendar solo servicios del contexto por su `service_id`, sin inventar servicios, precios ni duraciones, máximo 3, y responder solo JSON. El backend descarta cualquier id que no estuviera en el contexto (queda en `discarded_service_ids`) y completa nombre, precio y duración desde la base de datos.', 'rag'),
  p('Se eligió recuperación por palabras clave en lugar de embeddings porque es determinista, explicable, no agrega dependencias ni otra llamada paga, y es suficiente para un catálogo de 12 servicios. Su limitación quedó medida en el experimento (sección siguiente): cuando el cliente describe el síntoma con palabras que no están en el diccionario, el servicio correcto no llega al contexto.'),
  h2('Manejo de errores y límites'),
  ...table('Mapeo de fallos del proveedor a respuestas HTTP', ['Situación', 'Comportamiento', 'HTTP', '`code`'], [
    ['Sin `GEMINI_API_KEY` o `GEMINI_MODEL`', 'No se llama al proveedor; se registra en `ai_calls`.', '503', '`ai_not_configured`'],
    ['El proveedor no responde a tiempo', 'Timeout explícito de `AI_TIMEOUT_SECONDS` (20 s); no se reintenta.', '504', '`llm_timeout`'],
    ['429 o 503 del proveedor', 'Hasta `AI_MAX_RETRIES` (2) reintentos con backoff exponencial y jitter.', '200 si se recupera', '—'],
    ['429 tras todos los reintentos', 'Se informa al cliente.', '429', '`llm_rate_limited`'],
    ['Otro error del proveedor o de red', 'Se informa al cliente.', '502', '`llm_provider_error`'],
    ['Respuesta que no es el JSON esperado', 'Se guarda la respuesta cruda.', '502', '`invalid_llm_response`'],
    ['Usuario supera `AI_MAX_CALLS_PER_HOUR` (20)', 'Rechazo local antes de llamar al proveedor, con encabezado `Retry-After`.', '429', '`user_quota_exceeded`'],
  ], [2700, 3660, 1300, 1700], { notes: 'Los errores incluyen en `details` el `ai_call_id` de la fila registrada y el número de intentos. Las 15 pruebas del asistente cubren cada fila de esta tabla con el proveedor simulado.' }),
  p(`El reintento no es teórico: durante el experimento, la llamada ${retried.map((r) => r.ai_call_id).join(', ')} recibió un 503 real del proveedor (“modelo sobrecargado”), el cliente esperó 1,3 s y el segundo intento respondió correctamente.`),
  h2('Llamadas reales registradas'),
  p(`La tabla \`ai_calls\` guarda, para cada llamada exitosa o fallida, el usuario, la técnica, el prompt completo, la respuesta cruda, los tokens de entrada, salida y razonamiento, la latencia, los intentos y el estado. Al cierre de este informe había ${aiCalls.length} llamadas reales (${apiCalls} desde el endpoint y ${evalCalls} del experimento), con estados: ${Object.entries(callsByStatus).map(([k, v]) => `${k} = ${v}`).join(', ')}. La Tabla ${tab('Llamadas reales al LLM tomadas de ai_calls')} muestra ${shownCalls.length} de ellas; la exportación completa está en \`evidence/ai_calls_export.csv\`.`),
  ...table('Llamadas reales al LLM tomadas de ai_calls', ['ID', 'Fecha (UTC)', 'Origen', 'Técnica', 'Estado', 'Tok. ent.', 'Tok. sal.', 'Lat. (ms)', 'Int.', 'Síntoma'],
    shownCalls.map((c) => [c.ai_call_id, c.created_at, c.source, c.technique, c.status, c.input_tokens ?? '—', c.output_tokens ?? '—', c.latency_ms ?? '—', c.attempts, c.description.length > 42 ? `${c.description.slice(0, 40)}…` : c.description]),
    [500, 1500, 700, 900, 1200, 700, 700, 760, 500, 1900], { size: 15, notes: 'Las llamadas 1 a 3 respondieron 503 porque `GEMINI_MODEL` quedó mal escrito en `.env` (ver la sección de dificultades); el sistema lo registró correctamente. Origen `api` = endpoint HTTP; `eval` = script del experimento. Hora UTC (Colombia = UTC − 5).' }),
  figure(shot('08_ai_suggest_service_200.png'), 'Respuesta real del asistente con la técnica chain-of-thought', 'El modelo eligió el servicio de refrigeración; el precio (170.000 COP) y la duración (90 min) los completó el backend desde la base de datos.'),
);

// 7. Comparacion de tecnicas
const promptDiff = {
  zero_shot: 'Prompt de sistema + contexto + descripción + formato JSON. Sin ejemplos.',
  few_shot: 'Lo mismo + 3 ejemplos resueltos con un catálogo ficticio (ids 101-106): frenos, check engine y un caso sin servicio aplicable.',
  cot: 'Lo mismo que zero-shot + instrucción de razonar en 3 pasos en el campo `reasoning` antes de elegir.',
};
add(
  h1('Comparación de técnicas de prompting'),
  p(`Se ejecutaron 10 casos realistas (síntomas descritos como los diría un cliente, aprobados por el equipo antes de correr el experimento) con las tres técnicas: ${results.results.length} llamadas reales a \`${MODEL}\` con temperatura 0,2, alternando técnicas en cada caso para que una degradación temporal del proveedor no afectara a una sola. Un acierto es que el servicio esperado sea la primera sugerencia. Todas las técnicas comparten el mismo prompt de sistema y el mismo contexto recuperado; solo cambia la forma de pedir la respuesta. Script: \`scripts/run_prompt_eval.py\`; resultados: \`evidence/prompt_eval/results.json\` y \`.csv\`.`),
  ...table('Resultados por técnica (valores medidos)', ['Técnica', 'Qué cambia en el prompt', 'Top-1', 'Top-3', 'Tokens ent.', 'Tokens sal.', 'Latencia prom.', 'USD / llamada'],
    TECHNIQUES.map((t) => [TECH_LABEL[t], promptDiff[t], pct(S[t].precision_top1), pct(S[t].hit_rate_top3), fmt(S[t].avg_input_tokens, 1), fmt(S[t].avg_output_tokens, 1), `${fmt(S[t].avg_latency_ms)} ms`, usd(ccost[t].cost_per_call_usd)]),
    [1300, 2560, 700, 700, 950, 950, 1100, 1100], { notes: `Top-1 = aciertos / 10. El modelo no generó tokens de razonamiento interno (thinking = 0) en ninguna llamada. La latencia promedio de few-shot incluye la llamada reintentada; sin ella es ${fmt(avgNoRetry('few_shot'))} ms. Costo con el precio de la capa de pago (sección siguiente).` }),
  ...table('Resultado por caso (✓ = acierto top-1)', ['Caso', 'Servicio esperado', 'Zero-shot', 'Few-shot', 'CoT', '¿Llegó al contexto?'],
    cases.map((c) => [c.id, `${c.expected_service_id} – ${c.expected_service_name}`, ...TECHNIQUES.map((t) => {
      const r = caseRow(c.id, t);
      return r.hit_top1 ? '✓' : `✗ (${r.suggested_service_ids.length ? r.suggested_service_ids.join(', ') : 'ninguno'})`;
    }), caseRow(c.id, 'zero_shot').retrieval_hit ? 'Sí' : 'No']),
    [600, 3560, 1200, 1200, 1200, 1600], { notes: 'La recuperación es determinista, por lo que el contexto fue idéntico para las tres técnicas en cada caso.' }),
  h2('Prompt de sistema común'),
  ...code(SYSTEM_PROMPT.trim(), 15),
  p('El Anexo A reproduce un prompt few-shot completo tal como se envió al modelo.'),
  h2('Respuesta de ejemplo de cada técnica (caso 3)'),
  plain(`*Descripción del cliente:* “${cases[2].description}”`),
  ...TECHNIQUES.flatMap((t) => [h3(TECH_LABEL[t]), ...code(JSON.stringify(JSON.parse(caseRow(3, t).response), null, 2), 14)]),
  h2('Análisis'),
  p(`**Las tres técnicas empataron en precisión (${pct(S.zero_shot.precision_top1)}).** Con este catálogo y estos casos la tarea es casi de clasificación con un contexto ya filtrado, y el modelo la resuelve sin necesidad de ejemplos ni de razonamiento explícito. Con 10 casos y una sola corrida, el experimento no permite afirmar que una técnica sea más precisa que otra; sí permite comparar costo, latencia y forma de la respuesta.`),
  p(`**El costo sí cambia.** Few-shot multiplica por ${(S.few_shot.avg_input_tokens / S.zero_shot.avg_input_tokens).toFixed(1)} los tokens de entrada, porque los tres ejemplos viajan en cada prompt. Chain-of-thought multiplica por ${(S.cot.avg_output_tokens / S.zero_shot.avg_output_tokens).toFixed(1)} los tokens de salida, que en este modelo cuestan 8,3 veces más que los de entrada; por eso es la técnica más cara (${(ccost.cot.cost_per_call_usd / ccost.zero_shot.cost_per_call_usd).toFixed(1)} veces zero-shot por llamada) y la de mayor latencia sin reintentos.`),
  p(`**La calidad de la respuesta no es idéntica.** Zero-shot marcó todas sus sugerencias con confianza “high” (${confidence.zero_shot.high} de ${confidence.zero_shot.total}), mientras que few-shot y CoT usaron “medium” para segundas opciones (${confidence.few_shot.medium} y ${confidence.cot.medium} veces) y propusieron más alternativas (${confidence.few_shot.total} y ${confidence.cot.total} sugerencias frente a ${confidence.zero_shot.total}). CoT además entrega un razonamiento legible, útil para que el asesor del taller explique la recomendación, y fue la que más advertencias agregó en \`notes\` (${notesCount.cot} de 10). Ninguna técnica propuso ids fuera del contexto: la regla del prompt y la validación del backend funcionaron.`),
  p(`**El único fallo fue de la recuperación, no del prompt.** En el caso ${failedCases.map((c) => c.id).join(', ')} (“${failedCases.map((c) => c.description).join('; ')}”) las tres técnicas devolvieron cero sugerencias. El diccionario de sinónimos no contiene “revoluciones”, “avanza” ni “quemado”, así que el contexto solo traía sincronización y batería. El modelo diagnosticó correctamente un embrague (lo dice en \`notes\` y, en CoT, en el razonamiento), pero obedeció la regla de usar solo el contexto y le dijo al cliente que el taller no ofrecía ese servicio, aunque sí está en el catálogo. Separar la métrica “¿llegó al contexto?” fue lo que permitió atribuir el fallo a la etapa correcta.`),
  p('**Decisión y trabajo futuro.** No se agregaron esas palabras al diccionario, porque eso sería ajustar el sistema a los casos de prueba y volvería optimista la medición. Las mejoras propuestas, que deben evaluarse con casos nuevos, son: (a) si el modelo devuelve cero sugerencias y el contexto no era el catálogo completo, repetir una vez con todo el catálogo; (b) reemplazar o complementar la recuperación por palabras clave con embeddings; (c) ampliar el conjunto de evaluación y repetir cada caso varias veces para medir la variabilidad.'),
  p('**Recomendación.** Con estos datos, zero-shot ofrece la misma precisión al menor costo y latencia y es la opción razonable para producción; chain-of-thought se justifica cuando se necesita mostrar el razonamiento al cliente o al asesor. El endpoint conserva few-shot como valor por defecto, que fue la elección inicial antes del experimento; cambiarlo es una decisión pendiente del equipo.'),
  p('**Limitaciones.** Los casos y el diccionario de sinónimos los escribió el mismo equipo (el diccionario antes que los casos), lo que puede sesgar la recuperación a favor; los ejemplos de few-shot tocan frenos y check engine con frases distintas a las de los casos; y la muestra es pequeña.'),
);

// 8. Costos (en ingles, requisito de la guia)
add(
  h1('LLM Cost Estimate'),
  plain('*This section is written in English, as required by the lab guide.*'),
  p(`**Model and price.** The assistant uses \`${cost.model}\` through the Google Gemini Developer API. On the paid tier (Standard), the price is **US$${cost.pricing.input_usd_per_1m.toFixed(2)} per 1M input tokens** and **US$${cost.pricing.output_usd_per_1m.toFixed(2)} per 1M output tokens**, and thinking tokens are billed as output (Google, 2026b). The pricing page was last updated on ${cost.pricing.page_last_updated} and was accessed on ${cost.pricing.accessed}.`),
  p(`**Average tokens.** The averages are measured, not estimated: they come from the ${results.results.length} real calls of the prompting experiment (10 cases × 3 techniques). The model produced no thinking tokens in any call.`),
  h2('Formula'),
  ...code('cost_per_call = avg_input_tokens x input_price / 1,000,000\n              + (avg_output_tokens + avg_thinking_tokens) x output_price / 1,000,000\nmonthly_cost  = cost_per_call x queries_per_day x days_per_month'),
  h2('Assumptions'),
  bullet(`${cost.assumptions.queries_per_day} queries per day × ${cost.assumptions.days_per_month} days = **${fmt(cost.assumptions.monthly_calls)} calls per month**; one LLM call per customer query.`),
  bullet(`Retries are rare: ${retried.length} of ${results.results.length} experiment calls needed one, and the failed attempt reported no token usage, so nothing is added for it.`),
  bullet('Keyword retrieval runs on our own server and has no API cost. Infrastructure (server, database) is out of scope.'),
  bullet('All values are parameters of `scripts/cost_estimate.py` (`--input-price`, `--output-price`, `--queries-per-day`, `--days`), so the projection can be recomputed if the price or the volume changes.'),
  ...table('Monthly cost projection per prompting technique (paid tier)', ['Technique', 'Avg input tokens', 'Avg output tokens', 'Cost per call (USD)', 'Cost per 1,000 calls (USD)', 'Monthly cost (USD)'],
    TECHNIQUES.map((t) => [TECH_LABEL[t], ccost[t].avg_input_tokens, ccost[t].avg_output_tokens, usd(ccost[t].cost_per_call_usd), usd(ccost[t].cost_per_1000_calls_usd, 4), usd(ccost[t].monthly_cost_usd, 4)]),
    [1660, 1400, 1400, 1600, 1700, 1600], { notes: `Example for zero-shot: ${ccost.zero_shot.avg_input_tokens} × 0.30 / 10^6 + ${ccost.zero_shot.avg_output_tokens} × 2.50 / 10^6 = US$${ccost.zero_shot.cost_per_call_usd.toFixed(6)} per call; × ${fmt(cost.assumptions.monthly_calls)} calls = US$${ccost.zero_shot.monthly_cost_usd.toFixed(2)} per month.` }),
  p(`**Interpretation.** At this volume every technique costs less than one US dollar per month, so cost is not a blocker; the relative difference still matters if traffic grows, since chain-of-thought costs about ${(ccost.cot.cost_per_call_usd / ccost.zero_shot.cost_per_call_usd).toFixed(1)} times as much as zero-shot per call. The free tier of this model costs nothing, but it has stricter rate limits and, according to the same pricing page, free-tier content is used to improve Google products, while paid-tier content is not; for real customer data the paid tier is the safer choice.`),
);

// 9. Preguntas orientadoras
add(
  h1('Respuestas a las preguntas orientadoras'),
  h2('1. Aprendizajes relacionados con el quehacer del ingeniero de software'),
  p('**La documentación de una API es un contrato que se puede verificar.** Generar la especificación OpenAPI desde el mismo código y validarla en las pruebas cambió la documentación de “texto que se desactualiza” a un artefacto que falla si está incompleto. El validador detectó un error real durante el trabajo: un decorador aplicado a nivel de clase borraba la documentación de un método y la especificación dejaba de ser válida.'),
  p('**Los códigos HTTP y el formato de error son parte del diseño, no un detalle.** Decidir que el 401 se evalúe antes que el 422, que el DELETE responda 409 en lugar de dejar citas huérfanas o que el 409 por nombre duplicado tenga además una restricción en la base de datos son decisiones que afectan a quien consume la API. Mantener el formato antiguo en las rutas del frontend mostró que mejorar un sistema existente exige no romper a sus clientes actuales.'),
  p('**Integrar un LLM es integrar un servicio externo poco confiable.** El modelo es solo una parte; el trabajo de ingeniería está en el timeout, los reintentos, el registro de cada llamada, los límites por usuario, las pruebas sin red y la medición del costo. El 503 real que ocurrió durante el experimento y se recuperó con el reintento confirmó que estas defensas no son teóricas.'),
  p('**Medir antes de concluir.** La intuición era que few-shot o chain-of-thought serían más precisos; los datos mostraron un empate y que el punto débil del sistema estaba en la recuperación. Separar métricas por etapa (¿llegó el servicio al contexto?, ¿lo eligió el modelo?) es lo que permite mejorar el componente correcto.'),
  h2('2. Mayor dificultad y cómo se resolvió'),
  p(`La mayor dificultad fue el caso del embrague (caso ${failedCases.map((c) => c.id).join(', ')}): las tres técnicas fallaron y, a primera vista, parecía un problema del modelo o del prompt. Al revisar el contexto enviado se vio que la recuperación por palabras clave nunca incluyó el servicio de embrague, porque el cliente lo describió con palabras que el diccionario no contemplaba. El modelo sí entendió el problema, pero la regla anti-alucinación le impidió sugerir algo fuera del contexto. Se resolvió en dos partes: se agregó al experimento la métrica de *recall* de la recuperación para atribuir cada fallo a su etapa, y se decidió no “arreglar” el diccionario con las palabras de ese caso para no sesgar la medición; en su lugar se documentaron mejoras generales para evaluar con casos nuevos.`),
  p('Hubo otros problemas reales durante el desarrollo:'),
  bullet('**Especificación inválida.** Un `@blp.doc` aplicado a la clase de la vista sobrescribía la documentación de cada método; openapi-spec-validator lo detectó y se pasó la descripción del parámetro a `blp.route(..., parameters=...)`.'),
  bullet('**Configuración rota.** Al agregar `GEMINI_MODEL` al `.env`, el archivo no terminaba en salto de línea y la variable quedó pegada a la línea de la key; el endpoint respondió 503 `ai_not_configured` (llamadas 1 a 3 de `ai_calls`). El propio manejo de errores permitió diagnosticarlo; se separó la línea sin exponer la key.'),
  bullet('**Diferencia de versiones.** El equipo local usa Python 3.14 y el CI Python 3.12; para no depender de “en mi máquina funciona”, se replicó el job en contenedores `python:3.12` y `postgres:16` antes de subir los cambios.'),
  bullet('**Credenciales de prueba.** El `seed.sql` trae hashes de ejemplo con los que no se puede iniciar sesión; los ejemplos de Swagger UI se ajustaron a los usuarios de prueba documentados en el README y se verificó el login contra el servidor.'),
  h2('3. Evidencia técnica de los entregables'),
  ...table('Entregables y evidencia', ['Entregable', 'Evidencia en el repositorio'], [
    ['CRUD de 5 endpoints + errores HTTP', `\`backend/api/v1/services.py\`; Figuras ${fig('05_get_service_404.png')} a ${fig('04_get_services_200.png')}`],
    [`${passedTests} pruebas de integración + CI`, '`backend/tests/`, `evidence/pytest_output.txt`, `.github/workflows/mecatrack-tests.yml`'],
    ['OpenAPI 3.0.3 en inglés + Swagger UI', `\`docs/openapi.json\`, \`/docs\`, \`tests/test_openapi.py\`; Figuras ${fig('01_swagger_overview.png')} y ${fig('02_swagger_post_docs_examples.png')}`],
    ['Endpoint de IA con manejo de errores', `\`backend/api/v1/ai.py\`, \`backend/services/\`; Tabla ${tab('Mapeo de fallos del proveedor a respuestas HTTP')}; Figura ${fig('08_ai_suggest_service_200.png')}`],
    [`≥ 10 llamadas reales documentadas`, `\`evidence/ai_calls_export.csv\` (${aiCalls.length} llamadas); Tabla ${tab('Llamadas reales al LLM tomadas de ai_calls')}`],
    ['Comparación de 3 técnicas', `\`evidence/prompt_eval/results.json\` y \`.csv\`; Tablas ${tab('Resultados por técnica (valores medidos)')} y ${tab('Resultado por caso (✓ = acierto top-1)')}`],
    ['Estimación de costos (inglés)', `\`evidence/cost_estimate_EN.md\`, \`scripts/cost_estimate.py\`; Tabla ${tab('Monthly cost projection per prompting technique (paid tier)')}`],
    ['Guion del video (inglés)', '`evidence/video_script_EN.md`'],
  ], [3200, 6160], { notes: 'Commits de la rama `mecatrack-final` para esta guía: ' + COMMITS.filter((c) => c.includes('Guia 5')).map((c) => c.split(' ')[0]).join(', ') + '.' }),
  h2('4. Ventajas y errores de la IA como asistente de programación'),
  p('En este laboratorio la asistencia de IA utilizada fue Claude Code (Anthropic, 2026), un agente que trabaja en la terminal: lee el repositorio, ejecuta comandos y pruebas, y propone y aplica cambios que el estudiante revisa y aprueba por fases.'),
  p('**Ventajas observadas.** Exploró el repositorio antes de proponer cambios y respetó convenciones existentes (repositorios sin commit, `role_required`, migraciones con Alembic); escribió pruebas junto con cada fase; consultó la documentación oficial de Gemini el día de la ejecución para elegir el modelo y el precio en lugar de usar datos de memoria; y automatizó tareas repetitivas como exportar la especificación, capturar Swagger UI o generar este informe a partir de los datos.'),
  p('**Errores reales que cometió la IA y cómo se detectaron.** En la documentación de Swagger escribió primero unas credenciales de ejemplo inventadas, que no existían en la base; al agregar `GEMINI_MODEL` al `.env` rompió la línea de la key; aplicó un decorador de documentación a nivel de clase que dejó inválida la especificación; escribió prefijos del diccionario de sinónimos que nunca coincidían (“trac” en vez de “traq” para “traqueteo”); un comando suyo creó por accidente un archivo suelto llamado `0` en el repositorio; y en el análisis de costos redactó una afirmación no verificada sobre la facturación de los intentos fallidos. Todos se detectaron con pruebas, con el validador de OpenAPI, revisando las capturas y releyendo las afirmaciones contra las fuentes, y se corrigieron antes de cada commit. La lección es que la IA acelera mucho el trabajo, pero cada salida necesita una verificación independiente.'),
  p('[[PENDIENTE (experiencia propia con GitHub Copilot): describir una sugerencia real de Copilot que hayas evaluado —qué pediste, qué sugirió, qué tenía de correcto o incorrecto y qué decidiste—. Si no usaste Copilot en esta guía, indícalo y elimina este párrafo.]]', { indent: {} }),
);

// 10. Enlaces
add(
  h1('Enlaces'),
  plain('**Repositorio:** https://github.com/pablo-rodriguez091004/TallerDeProgramaci-n (rama `mecatrack-final`). [[VERIFICAR que la rama esté publicada en GitHub.]]'),
  plain('**Video en inglés:** [[PEGAR ENLACE DEL VIDEO]]'),
);

// 11. Referencias (APA 7, orden alfabetico, sangria francesa)
const refs = [
  'Anthropic. (2026). *Claude Code* [Software]. https://claude.com/claude-code',
  'Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D. M., Wu, J., Winter, C., … Amodei, D. (2020). Language models are few-shot learners. *Advances in Neural Information Processing Systems, 33*, 1877–1901.',
  'flask-smorest contributors. (s. f.). *flask-smorest documentation*. Recuperado el 20 de octubre de 2026, de https://flask-smorest.readthedocs.io/',
  'GitHub. (s. f.). *Workflow syntax for GitHub Actions*. GitHub Docs. Recuperado el 20 de octubre de 2026, de https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax',
  'Google. (2026a). *Gemini models*. Google AI for Developers. Recuperado el 20 de octubre de 2026, de https://ai.google.dev/gemini-api/docs/models',
  'Google. (2026b). *Gemini Developer API pricing*. Google AI for Developers. Recuperado el 20 de octubre de 2026, de https://ai.google.dev/gemini-api/docs/pricing',
  'Google. (s. f.). *Google Gen AI Python SDK (google-genai)* [Software]. Recuperado el 20 de octubre de 2026, de https://googleapis.github.io/python-genai/',
  'Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459–9474.',
  'Microsoft. (s. f.). *Playwright for Python*. Recuperado el 20 de octubre de 2026, de https://playwright.dev/python/',
  'OpenAPI Initiative. (2020). *OpenAPI Specification v3.0.3*. https://spec.openapis.org/oas/v3.0.3',
  'Pallets Projects. (s. f.). *Flask documentation (3.1.x)*. Recuperado el 20 de octubre de 2026, de https://flask.palletsprojects.com/en/stable/',
  'python-openapi. (s. f.). *openapi-spec-validator* [Software]. GitHub. Recuperado el 20 de octubre de 2026, de https://github.com/python-openapi/openapi-spec-validator',
  'SmartBear Software. (s. f.). *Swagger UI*. Recuperado el 20 de octubre de 2026, de https://swagger.io/tools/swagger-ui/',
  'Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q. V., & Zhou, D. (2022). Chain-of-thought prompting elicits reasoning in large language models. *Advances in Neural Information Processing Systems, 35*, 24824–24837.',
];
add(
  pageBreak(),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Referencias')] }),
  ...refs.map((r) => new Paragraph({ children: runs(r), spacing: { line: DOUBLE }, indent: { left: 720, hanging: 720 } })),
);

// 12. Declaracion de uso de IA (borrador)
add(
  h1('Declaración de uso de inteligencia artificial'),
  plain('[[BORRADOR — revisar y ajustar antes de entregar.]]'),
  p('En este trabajo se utilizó Claude Code (Anthropic, 2026) como asistente de programación. La IA generó, a partir de instrucciones del estudiante y por fases aprobadas una a una: el código de la API v1 y del asistente de IA, los esquemas y la configuración de OpenAPI, las migraciones, las pruebas de integración, el workflow de CI, los scripts de evaluación, costos y capturas, el guion del video y el borrador de este informe, que se genera automáticamente a partir de las evidencias.'),
  p('El estudiante definió los requisitos y las reglas de trabajo, aprobó el plan, el catálogo de servicios y los 10 casos de evaluación, decidió no ajustar el diccionario de sinónimos a los casos de prueba y revisó cada fase antes del commit. Los resultados de pruebas, llamadas al modelo, tokens, latencias y costos provienen de ejecuciones reales y no fueron editados a mano.'),
  p('[[COMPLETAR: qué revisaste o cambiaste tú personalmente (código, textos, decisiones), y cualquier otra herramienta de IA que hayas usado.]]', { indent: {} }),
);

// Anexo A
const fewShotPrompt = caseRow(3, 'few_shot').prompt;
add(
  pageBreak(),
  h1('Anexo A. Prompt few-shot completo enviado al modelo (caso 3)'),
  ...code(fewShotPrompt, 13),
);

return children;
}

buildContent(); // primera pasada: numeros de tablas y figuras
const children = buildContent();

// ------------------------------------------------------------------ documento
const doc = new Document({
  creator: 'MecaTrack',
  title: 'Informe Guía 5 MecaTrack',
  description: 'API REST con OpenAPI 3.0 e integración de un LLM',
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: '000000' },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 240, after: 0, line: DOUBLE }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: '000000' },
        paragraph: { spacing: { before: 120, after: 0, line: DOUBLE }, outlineLevel: 1, keepNext: true } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 24, bold: true, italics: true, color: '000000' },
        paragraph: { spacing: { before: 120, after: 0, line: DOUBLE }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'rag', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 15840 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] }) },
    footers: { default: new Footer({ children: [] }) },
    children,
  }],
});

const out = path.join(__dirname, 'Informe_Guia5_MecaTrack.docx');
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log(`Informe generado: ${path.relative(ROOT, out)} (${tableNo} tablas, ${figureNo} figuras, ${(buf.length / 1024 / 1024).toFixed(1)} MB)`);
});
