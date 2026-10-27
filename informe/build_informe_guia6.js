// Genera informe/Informe_Guia6_MecaTrack.docx (normas APA 7, mismo formato que la Guía 5).
// Todas las cifras se LEEN de docs/evidencia/salidas/ (ejecuciones reales); las figuras son
// las capturas de docs/evidencia/. Regenerar con ./scripts/generar_evidencia.sh o `node build_informe_guia6.js`.
//
// Los únicos campos pendientes (códigos estudiantiles) van resaltados en amarillo: [[COMPLETAR ...]].

const fs = require('fs');
const path = require('path');
const { Packer } = require('docx');
const A = require('./apa');

const { p, plain, center, h1, h2, h3, bullet, link, pageBreak, code, reference, Paragraph, TextRun, AlignmentType } = A;
const ROOT = path.resolve(__dirname, '..');
const EVID = path.join(ROOT, 'docs', 'evidencia');
const OUT_TXT = path.join(EVID, 'salidas');
const read = (name) => fs.readFileSync(path.join(OUT_TXT, name), 'utf8');
const readJson = (name) => JSON.parse(read(name));
const img = (name) => path.join(EVID, name);

// ------------------------------------------------------------------ datos reales
const fmt = (n, d = 0) => Number(n).toLocaleString('es-CO', { minimumFractionDigits: d, maximumFractionDigits: d });
function pytestSummary(name) {
  const m = read(name).match(/(\d+) passed[^\n]*? in ([\d.]+)s/);
  if (!m) throw new Error(`Sin resumen de pytest en ${name}`);
  return { passed: Number(m[1]), seconds: Number(m[2]) };
}
const ALL = pytestSummary('02_pytest_completo.txt');
const UNIT = pytestSummary('02b_pytest_unitarias.txt');
const INTEG = pytestSummary('02c_pytest_integracion.txt');
const MOCKS = pytestSummary('05_pytest_mocks.txt');
const RESIL = pytestSummary('09_pytest_resiliencia.txt');
if (UNIT.passed + INTEG.passed !== ALL.passed) throw new Error('Los conteos de pytest no cuadran');

const LAYERS = Object.fromEntries(read('01_conteo.txt').split('\n')
  .map((l) => l.match(/^(domain|application|api|infrastructure)\s+(\d+) archivos/)).filter(Boolean)
  .map((m) => [m[1], Number(m[2])]));

function apiCalls(name) {
  const text = read(name);
  const out = [];
  const re = /^### (.+)\nGET (\S+)[\s\S]*?^-> HTTP 200 en (\d+) ms \| intentos: (\d+) \| breaker: (\w+) \| (\d+) registros/gm;
  let m;
  while ((m = re.exec(text))) out.push({ title: m[1], url: m[2], ms: Number(m[3]), attempts: Number(m[4]), state: m[5], rows: Number(m[6]) });
  return out;
}
const DATOS = apiCalls('06_api_datos_gov_co.txt');
const DANE = apiCalls('07_api_dane.txt');
const CONSULTA = read('06_api_datos_gov_co.txt').match(/Consulta real: (\S+)/)[1];

const DEMO = readJson('demo_resilience.json');
const REJECTED = DEMO.events.filter((e) => e.kind === 'REJECTED').map((e) => Number(e.message.match(/(\d+) us\)/)[1]));
const ANALYTICS = readJson('analitica.json');
const Q1 = ANALYTICS.fleet_age_by_class;
const Q2 = ANALYTICS.motorization_by_department;
const Q3 = ANALYTICS.age_distribution;
const byClass = Object.fromEntries(Q1.rows.map((r) => [r.clase, r]));
const S2 = Q2.summary;
const motoShare = (tipo, rango) => Q3.rows.find((r) => r.tipo_taller === tipo && r.rango === rango).pct_del_tipo;
const dept = (cod) => Q2.rows.find((r) => r.cod_dpto === cod);
const CI = readJson('15_ci_run.json');
const COMMITS = read('commits_guia6.txt').split('\n').filter((l) => /^[0-9a-f]{7} /.test(l)).reverse();

// ------------------------------------------------------------------ contenido
const N = A.numbering();
const { table, figure, tab, fig } = N;
const AUTHORS = ['Pablo Alejandro Rodriguez Suarez', 'Daniel Steven Londoño Vanegas', 'Omar David Gutierrez Torrez'];
const REPO_URL = 'https://github.com/pablo-rodriguez091004/TallerDeProgramaci-n';
const VIDEO_URL = 'https://youtu.be/MchkTFUkQmU?feature=shared';
const TITLE = 'Guía de Laboratorio 6: Arquitectura Hexagonal, DDD y APIs de Datos Abiertos Colombianos en MecaTrack';

function buildContent() {
  N.reset();
  const children = [];
  const add = (...items) => items.flat().forEach((i) => children.push(i));

  // Portada (APA 7, trabajo de estudiante; mismo esquema que la versión final de la Guía 5)
  add(
    ...Array.from({ length: 3 }, () => new Paragraph({ spacing: { line: A.DOUBLE }, children: [] })),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: A.DOUBLE, after: 480 }, children: [new TextRun({ text: TITLE, bold: true })] }),
    ...AUTHORS.map((a) => center(`${a} — Código [[COMPLETAR: código]]`)),
    center('Facultad de Ingeniería, Universidad Manuela Beltrán (UMB)'),
    center('Taller de Programación — Sesiones 11 y 12'),
    center('26 de octubre de 2026'),
    pageBreak(),
  );

  // Introducción
  add(
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: A.DOUBLE }, children: [new TextRun({ text: TITLE, bold: true })] }),
    h1('Introducción'),
    p('MecaTrack es el sistema de citas y seguimiento de vehículos de un taller mecánico (Flask, SQLAlchemy y PostgreSQL, con frontend en HTML, CSS y JavaScript sin frameworks). En esta guía se reorganizó el backend con arquitectura hexagonal (puertos y adaptadores) dividida por *bounded contexts* de diseño guiado por el dominio (DDD), se aplicó inyección de dependencias por constructor con pruebas unitarias que usan objetos simulados (*mocks*), y se integraron dos APIs públicas colombianas —datos.gov.co y el geoportal del DANE— protegidas con un *circuit breaker* y reintentos con *backoff* exponencial. Los datos descargados se analizan con DuckDB y se muestran en una vista nueva del panel del dueño.'),
    p(`Como el stack del proyecto es Python, la "demostración de testabilidad con Mockito" que pide la guía se hizo con \`unittest.mock\`, la librería estándar equivalente. Todas las cifras de este informe provienen de ejecuciones reales guardadas en \`docs/evidencia/salidas/\` (consulta a las APIs del ${CONSULTA.slice(0, 10)}), y el documento se genera a partir de esos archivos con \`informe/build_informe_guia6.js\`.`),
    h2('Objetivos'),
    bullet('Refactorizar el backend a cuatro capas (domain, application, api, infrastructure) sin romper la funcionalidad existente, con un dominio que no dependa de Flask, SQLAlchemy ni librerías de red.'),
    bullet('Aplicar inyección de dependencias por constructor en al menos dos servicios y demostrar su testabilidad con mocks.'),
    bullet('Documentar en inglés la decisión arquitectónica y los bounded contexts en un ADR.'),
    bullet('Integrar al menos dos APIs colombianas con circuit breaker de tres estados y reintentos con backoff exponencial, y procesar el JSON con DuckDB.'),
    bullet('Escribir al menos dos consultas analíticas con estadísticas descriptivas y visualizarlas en la interfaz sin librerías.'),
  );

  // 1. Arquitectura hexagonal
  add(
    h1('Arquitectura Hexagonal'),
    p(`Antes de esta guía, las rutas de Flask llamaban directamente a funciones de repositorio y contenían reglas de negocio (por ejemplo, el depósito del 30 % se calculaba dentro de \`POST /appointments\`), y las 31 pruebas existentes eran todas de integración. La arquitectura hexagonal (Cockburn, 2005) separa el núcleo de negocio de la tecnología: el núcleo define *puertos* (interfaces) y la infraestructura los implementa con *adaptadores*. La Figura ${fig('01_estructura_hexagonal.png')} muestra la estructura resultante y la Tabla ${tab('Capas de la arquitectura y regla de dependencias')} resume qué contiene y qué puede importar cada capa.`),
    ...table('Capas de la arquitectura y regla de dependencias', ['Capa', 'Archivos .py', 'Contenido', 'Puede importar'], [
      ['`domain/`', String(LAYERS.domain), 'Entidades (dataclasses), reglas puras, puertos (clases abstractas) y errores de dominio', 'Solo la librería estándar'],
      ['`application/`', String(LAYERS.application), 'Casos de uso; cada dependencia es un puerto recibido por el constructor', '`domain`'],
      ['`api/`', String(LAYERS.api), 'Blueprints de Flask (rutas antiguas y `/api/v1`), esquemas, sesión y traducción de errores a HTTP', '`application`, `domain`'],
      ['`infrastructure/`', String(LAYERS.infrastructure), 'Modelos y repositorios SQLAlchemy, cliente HTTP resiliente, fuentes de datos abiertos, DuckDB, Gemini', '`domain`'],
      ['`bootstrap.py`', '1', 'Composition root: único lugar donde se crean los adaptadores y se inyectan', 'Todo'],
    ], [1700, 1100, 4560, 2000], { notes: 'Conteo real de `find` sin contar `__init__.py` (archivo `docs/evidencia/salidas/01_conteo.txt`).' }),
    figure(img('01_estructura_hexagonal.png'), 'Estructura de carpetas del backend por capas', 'Salida real de `tree` y `find`. Los bounded contexts son subpaquetes de `domain/` y `application/`.', 620),
    p(`La regla de dependencias no queda solo como convención: \`tests/unit/test_architecture.py\` analiza los *imports* de cada archivo con el módulo \`ast\` y falla si \`domain\` importa algo fuera de la librería estándar, si \`application\` importa un framework o una librería de entrada/salida, o si \`api\` importa \`infrastructure\`. Para comprobar que la prueba realmente detecta violaciones se agregó temporalmente \`import flask\` a un módulo del dominio: la prueba falló y luego se revirtió el cambio.`),
    p(`La Figura ${fig('03_puerto_y_adaptador.png')} muestra un puerto y su adaptador. \`AppointmentRepository\` declara en el dominio, sin SQL, lo que el agendamiento necesita (por ejemplo \`has_blocking_overlap\`, la consulta de solapamiento de horarios); \`SqlAlchemyAppointmentRepository\` la implementa en la infraestructura con una consulta SQL que no trae todas las citas a memoria.`),
    figure(img('03_puerto_y_adaptador.png'), 'Puerto AppointmentRepository (domain) y su adaptador SQLAlchemy (infrastructure)', 'Fragmentos reales con los números de línea de cada archivo.', 640),
    h2('Refactor sin romper la funcionalidad'),
    p(`El refactor se protegió con las pruebas de integración existentes, que pasaron sin cambiar ninguna aserción (solo los *imports*). Como varias rutas no tenían pruebas (seguimiento, repuestos, mecánicos, vehículos), se escribieron 7 pruebas de caracterización y se ejecutaron primero contra el código original (7/7) y después contra el código refactorizado (7/7). Además, \`flask db check\` confirmó que el esquema de la base no cambió y la especificación OpenAPI exportada quedó idéntica.`),
  );

  // 2. DDD y ADR
  add(
    h1('Bounded Contexts y ADR'),
    p(`Siguiendo a Evans (2003), el dominio se dividió en siete *bounded contexts*, cada uno con su lenguaje y sus puertos (Tabla ${tab('Bounded contexts identificados')}). El agendamiento es el subdominio central (*core*): la regla de disponibilidad simultánea de bahía y mecánico es lo que diferencia al producto. En total el dominio expone 18 puertos abstractos.`),
    ...table('Bounded contexts identificados', ['Contexto', 'Tipo', 'Conceptos principales', 'Puertos'], [
      ['Agendamiento (`scheduling`)', 'Core', 'Cita, estados bloqueantes, solapamiento [inicio, fin), `ResourceAllocator`', '`AppointmentRepository`'],
      ['Pagos (`payments`)', 'Soporte', 'Depósito/saldo 30/70, el depósito confirma la cita', '`PaymentRepository`, `Clock`'],
      ['Seguimiento (`tracking`)', 'Soporte', 'Registro de avance, repuestos usados, descuento de stock todo o nada', '`TrackingRepository`, `PartRepository`'],
      ['Gestión del negocio (`catalog`)', 'Soporte', 'Taller, bahía, servicio, repuesto, vehículo', '5 repositorios'],
      ['Identidad (`identity`)', 'Genérico', 'Usuario, rol, credenciales', '`UserRepository`, `PasswordHasher`'],
      ['Asistente IA (`ai_assistant`)', 'Soporte', 'Recuperación RAG, prompts, validación de la respuesta, cuota', '`LlmGateway`, `AiCallLog`'],
      ['Datos de mercado (`market_data`)', 'Genérico', 'Fuentes abiertas, snapshots, resultado analítico, salud de la fuente', '`DataSource` (+3), `SnapshotStore`, `HealthMonitor`, `MarketAnalytics`'],
    ], [2400, 1100, 3460, 2400], { notes: '`UnitOfWork` y `Clock` son puertos compartidos (`domain/shared`).' }),
    p(`Las relaciones entre contextos se documentaron en un mapa de contextos. Agendamiento y Pagos tienen una relación cliente/proveedor y comparten transacción (al agendar se crean los dos pagos). Hacia datos.gov.co, el DANE y el proveedor del modelo de lenguaje hay una *capa anticorrupción*: los adaptadores traducen los formatos externos (SoQL de Socrata, ArcGIS REST) y sus errores técnicos a objetos y errores del dominio, de modo que esos modelos nunca entran al núcleo.`),
    p(`La decisión quedó registrada en inglés en \`docs/adr/0001-hexagonal-architecture.md\` con el formato de Nygard (2011): contexto, decisión, alternativas descartadas y consecuencias positivas y negativas, con métricas reales (Figura ${fig('16_adr.png')}). Entre las consecuencias negativas se reconoce la duplicación entre entidades del dominio y modelos ORM, la necesidad de llamar explícitamente a \`save()\` y el acoplamiento conocido entre Pagos y Agendamiento.`),
    figure(img('16_adr.png'), 'ADR 0001 en inglés renderizado en GitHub (secciones 1 a 2.1)', 'Captura de la página pública del repositorio. El ADR completo incluye además el mapa de contextos, la estrategia de DI y de resiliencia, las alternativas, las consecuencias y las referencias.', 640),
  );

  // 3. DI y mocks
  add(
    h1('Inyección de Dependencias y Pruebas con Mocks'),
    p(`Cada servicio de aplicación recibe sus dependencias por el constructor y nunca crea adaptadores. La Figura ${fig('04_servicio_di_constructor.png')} muestra \`AppointmentService\`, que recibe seis puertos (citas, vehículos, servicios, asignador de recursos, pagos y unidad de trabajo), y el *composition root* \`bootstrap.py\`, que es el único lugar donde se instancian las implementaciones concretas. \`PaymentService\` recibe además un puerto \`Clock\`, para que la fecha de pago sea determinista en las pruebas.`),
    figure(img('04_servicio_di_constructor.png'), 'AppointmentService con inyección por constructor y composition root', null, 640),
    p(`Gracias a esa inyección, las pruebas unitarias reemplazan cada puerto por un mock creado con \`create_autospec(Puerto, instance=True)\` (Python Software Foundation, s. f.-b). A diferencia de un \`Mock()\` genérico, este mock solo acepta los métodos y firmas que declara el puerto, así que una prueba falla si el servicio usa algo que la interfaz no ofrece. La Figura ${fig('05_test_con_mock.png')} muestra una de estas pruebas y la ejecución de las ${MOCKS.passed} pruebas de \`AppointmentService\` y \`PaymentService\`.`),
    figure(img('05_test_con_mock.png'), 'Prueba unitaria de AppointmentService con mocks y su ejecución', null, 640),
    p(`La Tabla ${tab('Pruebas automatizadas por tipo')} compara los dos tipos de prueba. Las unitarias corren sin PostgreSQL ni red (también pasan con una URL de base de datos inválida). Para comprobar que verifican algo real se cambió temporalmente el depósito al 40 %: fallaron exactamente las 3 pruebas de la regla 30/70.`),
    ...table('Pruebas automatizadas por tipo', ['Tipo', 'Carpeta', 'Pruebas', 'Duración', 'Dependencias'], [
      ['Unitarias', '`tests/unit/`', String(UNIT.passed), `${fmt(UNIT.seconds, 2)} s`, 'Ninguna: mocks, reloj y transporte HTTP simulados, fixtures JSON reales'],
      ['Integración', '`tests/integration/`', String(INTEG.passed), `${fmt(INTEG.seconds, 2)} s`, 'Flask + PostgreSQL reales; APIs externas simuladas'],
      ['Total', '`tests/`', String(ALL.passed), `${fmt(ALL.seconds, 2)} s`, 'Antes de la guía: 31 pruebas, todas de integración'],
    ], [1500, 1900, 1100, 1300, 3560], { notes: 'Salidas reales en `docs/evidencia/salidas/02*_pytest_*.txt`. La Figura ' + fig('02_pytest_verde.png') + ' muestra la suite completa.' }),
    figure(img('02_pytest_verde.png'), 'Suite completa de pytest en verde', null, 520),
  );

  // 4. APIs colombianas
  const runt = DATOS[0];
  const divipola = DATOS[1];
  const dane = DANE[0];
  add(
    h1('Integración de APIs Públicas Colombianas'),
    p('Antes de escribir código se consultaron los endpoints reales para verificar que existían y qué JSON devolvían, y se eligieron los datos por su utilidad para un taller mecánico (Tabla ' + tab('Fuentes de datos abiertos integradas') + '). Se descartaron los precios de combustible publicados en datos.gov.co (último dato de 2018) y el IPC del geoportal del DANE (2012–2013) por estar desactualizados.'),
    ...table('Fuentes de datos abiertos integradas', ['Fuente', 'API', 'Registros', 'Tiempo', 'Uso en el taller'], [
      ['Crecimiento del parque automotor RUNT 2.0 (Ministerio de Transporte, 2026), `u3vn-bdcy`', 'datos.gov.co (Socrata, SoQL)', fmt(runt.rows), `${fmt(runt.ms)} ms`, 'Edad del parque por clase: un parque más viejo demanda más mantenimiento'],
      ['DIVIPOLA, códigos de municipios (DANE, 2025), `gdxc-w37w`', 'datos.gov.co (Socrata)', fmt(divipola.rows), `${fmt(divipola.ms)} ms`, 'Puente entre los nombres de departamento de RUNT y los códigos del DANE'],
      ['Población total censada CNPV 2018 por municipio (DANE, s. f.-b)', 'Geoportal del DANE (ArcGIS REST)', fmt(dane.rows), `${fmt(dane.ms)} ms`, 'Vehículos por cada 1.000 habitantes: demanda potencial por departamento'],
    ], [2900, 1700, 1000, 900, 2860], { notes: `Medición real del ${CONSULTA.replace('T', ' ')} con el cliente resiliente del proyecto (${runt.attempts} intento en cada consulta; breaker ${runt.state}). RUNT se pide agregado en el servidor por departamento, clase y año de registro: unas 28 mil filas (~3 MB) en lugar de 192 mil (~27 MB).` }),
    p(`Las Figuras ${fig('06_api_datos_gov_co.png')} y ${fig('07_api_dane.png')} muestran las respuestas reales, recortadas a tres registros. Los adaptadores manejan las particularidades de cada API: Socrata pagina con \`$limit\`/\`$offset\` y entrega todos los valores como texto (Tyler Technologies, s. f.); ArcGIS pagina con \`resultOffset\` y puede responder HTTP 200 con un objeto \`error\` en el cuerpo (Esri, s. f.), caso que se trata como fallo.`),
    figure(img('06_api_datos_gov_co.png'), 'Respuesta real de datos.gov.co (RUNT y DIVIPOLA)', 'JSON recortado a 3 registros por fuente; la captura indica cuántos se omitieron.', 600),
    figure(img('07_api_dane.png'), 'Respuesta real del geoportal del DANE (CNPV 2018)', 'JSON recortado a 3 registros.', 520),
  );

  // 5. Resiliencia
  const gaps = DEMO.retry.gaps_s;
  add(
    h1('Circuit Breaker y Reintentos con Backoff'),
    p(`Las APIs externas pueden fallar o tardar, por eso cada host tiene su propio *circuit breaker* (Fowler, 2014; Nygard, 2018). En estado CLOSED las llamadas pasan y se cuentan los fallos seguidos; con 3 fallos pasa a OPEN y rechaza las llamadas al instante, sin tocar la red; después de 30 segundos pasa a HALF_OPEN y deja pasar una sola llamada de prueba: si funciona vuelve a CLOSED y si falla vuelve a OPEN con el temporizador reiniciado. Usar un breaker por host aísla las fallas: si datos.gov.co se cae, el DANE sigue funcionando.`),
    p(`Dentro del breaker, los fallos transitorios (*timeout*, error de conexión, HTTP 429 o 5xx) se reintentan con backoff exponencial y *jitter* (Brooker, 2015): el techo de espera es min(8; 0,5 · 2^(n−1)) segundos y la espera real es la mitad del techo más un valor aleatorio hasta completarlo. Los errores 4xx no se reintentan ni abren el circuito, porque indican una petición mal formada y no una dependencia caída, y un circuito abierto tampoco se reintenta.`),
    p(`Para demostrar los estados se usó una **demostración controlada**: los fallos se fuerzan con un host del dominio reservado \`.invalid\` (Eastlake & Panitz, 1999), que nunca resuelve, y las llamadas exitosas van a datos.gov.co de verdad. La Figura ${fig('08_circuit_breaker_estados.png')} muestra el recorrido real CLOSED → OPEN → HALF_OPEN → OPEN → HALF_OPEN → CLOSED, y la Tabla ${tab('Tiempos reales entre reintentos')} los tiempos medidos del retry (Figura ${fig('10_retry_backoff.png')}). Con el circuito abierto, el rechazo tardó ${REJECTED.map((us) => `${us} µs`).join(' y ')}, sin salir a la red.`),
    ...table('Tiempos reales entre reintentos', ['Reintento', 'Techo (s)', 'Espera planificada (s)', 'Separación medida entre intentos (s)'],
      gaps.map((g, i) => [String(i + 1), fmt(Math.min(8, 0.5 * 2 ** i), 1), fmt(DEMO.retry.planned_s[i], 3), fmt(g, 3)]),
      [1800, 1800, 2700, 3060], { notes: 'Demostración controlada (host `.invalid`), archivo `docs/evidencia/salidas/demo_resilience.json`. La diferencia entre lo planificado y lo medido es el tiempo del propio intento.' }),
    figure(img('08_circuit_breaker_estados.png'), 'Transiciones reales del circuit breaker (demostración controlada)', 'Fallos forzados con un host `.invalid`; éxitos contra datos.gov.co. Tiempo de recuperación reducido a 5 s para la demostración (30 s en la aplicación).', 600),
    figure(img('10_retry_backoff.png'), 'Reintentos con backoff exponencial y jitter: tiempos reales', 'Misma ejecución que la figura anterior (parte A).', 460),
    p(`Las transiciones también están cubiertas por pruebas que usan un reloj, un \`sleep\` y un transporte HTTP simulados (\`httpx.MockTransport\`), así que no esperan ni usan red (Figura ${fig('09_circuit_breaker_pruebas.png')}; ${RESIL.passed} pruebas en ${fmt(RESIL.seconds, 2)} s). Al cambiar a propósito el umbral del breaker (\`>=\` por \`>\`) fallaron 4 de ellas. En la interfaz, la Figura ${fig('14_ui_circuit_breaker_abierto.png')} muestra el breaker de datos.gov.co en OPEN mientras el del DANE sigue CLOSED, también como demostración controlada: el backend se arrancó con \`MARKET_SOCRATA_BASE_URL\` apuntando al host \`.invalid\`.`),
    figure(img('09_circuit_breaker_pruebas.png'), 'Pruebas de los tres estados del breaker y del retry', null, 520),
    figure(img('14_ui_circuit_breaker_abierto.png'), 'Breaker de datos.gov.co abierto en la interfaz (demostración controlada)', 'El DANE, con su propio breaker, sigue descargando. La tabla conserva la última descarga exitosa de cada fuente.', 480),
  );

  // 6. DuckDB
  const moto = byClass.MOTOCICLETA;
  const auto = byClass.AUTOMOVIL;
  const top = Q2.rows[0];
  const bogota = dept('11');
  add(
    h1('Análisis de Datos con DuckDB'),
    p(`Los JSON descargados se guardan como *snapshots* en disco y DuckDB los consulta directamente con \`read_json\` y \`unnest\` (DuckDB Foundation, s. f.), en una conexión en memoria por consulta. Se escribieron tres consultas analíticas (Anexo A); las dos principales calculan estadísticas descriptivas.`),
    h2('Consulta 1: antigüedad del parque por clase'),
    p(`RUNT entrega los datos agregados (una fila representa N vehículos con el mismo año de registro), por eso la media y la desviación estándar se ponderan por el número de vehículos y los percentiles se toman de la distribución acumulada. Se excluyeron ${fmt(Q1.summary.excluidos_por_calidad)} vehículos con año de registro anterior a 1950 (valores de relleno como 1900). Para validar el método, se comparó con las funciones de DuckDB aplicadas a los datos expandidos a una fila por vehículo: los resultados coinciden exactamente en las 9 clases. La Tabla ${tab('Antigüedad del parque automotor activo por clase (años desde el registro)')} resume el resultado (Figura ${fig('11_duckdb_q1_antiguedad.png')}).`),
    ...table('Antigüedad del parque automotor activo por clase (años desde el registro)',
      ['Clase', 'Vehículos', 'Media', 'Desv.', 'P25', 'Mediana', 'P75', 'P90', '% 10+ años'],
      Q1.rows.map((r) => [r.clase, fmt(r.vehiculos), fmt(r.media, 2), fmt(r.desviacion, 2), String(r.p25), String(r.mediana), String(r.p75), String(r.p90), fmt(r.pct_10_anios_o_mas, 1)]),
      [1640, 1300, 860, 860, 760, 1000, 760, 760, 1420],
      { notes: `Corte RUNT ${Q1.summary.corte_runt}; ${fmt(Q1.summary.vehiculos_analizados)} vehículos activos de las clases que atiende el taller. Antigüedad media ponderada: ${fmt(Q1.summary.antiguedad_media_ponderada, 2)} años. Tiempo de la consulta en DuckDB: ${fmt(Q1.elapsed_ms, 1)} ms.` }),
    figure(img('11_duckdb_q1_antiguedad.png'), 'Consulta 1 en DuckDB: SQL y resultado', null, 600),
    h2('Consulta 2: motorización por departamento'),
    p(`La segunda consulta cruza tres conjuntos de datos: los vehículos de RUNT, la población del CNPV 2018 del DANE y la DIVIPOLA para unir nombres con códigos. Los nombres no coincidían exactamente ("BOGOTA D.C." frente a "BOGOTÁ, D.C."; San Andrés aparece recortado en RUNT), así que se normalizaron a solo letras y se aceptó la coincidencia por prefijo únicamente para claves largas; una prueba verifica que el total de vehículos no se pierde ni se duplica en el cruce. La Tabla ${tab('Estadísticas descriptivas de la motorización entre departamentos')} resume el resultado (Figura ${fig('12_duckdb_q2_motorizacion.png')}).`),
    ...table('Estadísticas descriptivas de la motorización entre departamentos', ['Estadístico', 'Vehículos por cada 1.000 habitantes'], [
      ['Departamentos (con datos en RUNT)', `${S2.departamentos} (${S2.con_datos})`],
      ['Media', fmt(S2.media, 1)], ['Mediana', fmt(S2.mediana, 1)], ['Desviación estándar', fmt(S2.desviacion, 1)],
      ['Mínimo – máximo', `${fmt(S2.minimo, 1)} – ${fmt(S2.maximo, 1)}`], ['Percentil 25 – percentil 75', `${fmt(S2.p25, 1)} – ${fmt(S2.p75, 1)}`],
      ['Nacional (total de vehículos / total de habitantes)', fmt(S2.nacional_por_1000_hab, 1)],
    ], [5000, 4360], { notes: `Sin registros en RUNT: ${S2.sin_vehiculos_en_runt.join(', ')}. Tiempo de la consulta en DuckDB: ${fmt(Q2.elapsed_ms, 1)} ms.` }),
    figure(img('12_duckdb_q2_motorizacion.png'), 'Consulta 2 en DuckDB: SQL del cruce, resultado por departamento y resumen', null, 640),
    h2('Visualización e interpretación'),
    p(`La vista Mercado del panel del dueño (Figuras ${fig('13a_ui_mercado_fuentes_motorizacion.png')} y ${fig('13b_ui_mercado_antiguedad.png')}) muestra el estado de los breakers, las fuentes, indicadores clave, tablas y dos gráficos dibujados con la API Canvas del navegador, sin librerías: barras horizontales con la referencia nacional y barras apiladas al 100 %, ambas con información emergente al pasar el puntero. Los endpoints que alimentan la vista están documentados en Swagger (Figura ${fig('17_swagger_market.png')}).`),
    figure(img('13a_ui_mercado_fuentes_motorizacion.png'), 'Vista Mercado: fuentes, circuit breakers, indicadores y motorización', 'Captura con Playwright de la aplicación real después de pulsar «Actualizar datos».', 640),
    figure(img('13b_ui_mercado_antiguedad.png'), 'Vista Mercado: antigüedad del parque y distribución por rangos', null, 560),
    figure(img('17_swagger_market.png'), 'Endpoints /api/v1/market documentados en Swagger UI', null, 200),
    p(`Para el negocio, el resultado más útil es que la mitad de las motos (mediana de ${moto.mediana} años) y la mayoría de los automóviles (mediana de ${auto.mediana} años; ${fmt(auto.pct_10_anios_o_mas, 1)} % con 10 años o más) ya están en la edad en que aumentan las reparaciones, y que el ${fmt(motoShare('car', '20+'), 1)} % de los carros tiene más de 20 años de registro. En motorización, ${top.departamento.charAt(0) + top.departamento.slice(1).toLowerCase()} (${fmt(top.vehiculos_por_1000_hab, 1)} por cada 1.000 habitantes, ${fmt(top.pct_motos, 1)} % motos) supera a Bogotá (${fmt(bogota.vehiculos_por_1000_hab, 1)}): RUNT ubica cada vehículo en el organismo de tránsito donde se matriculó y no donde circula, así que la cifra es indicativa y la interfaz lo advierte.`),
    p(`Para la estrategia del taller, los datos sugieren tres decisiones. Primero, las motos son el ${fmt(100 * moto.vehiculos / Q1.summary.vehiculos_analizados, 1)} % del parque analizado y la mitad tiene ${moto.mediana} años o menos, así que conviene ofrecer servicios rápidos y de bajo costo para motos (mantenimiento preventivo, frenos, transmisión); hoy ninguno de los servicios del catálogo de MecaTrack es específico para motos. Segundo, en carros predomina el parque envejecido (${fmt(auto.pct_10_anios_o_mas, 1)} % de los automóviles con 10 años o más), donde son más frecuentes las reparaciones correctivas (suspensión, refrigeración, embrague); eso justifica tener inventario de repuestos para esas fallas y reservar bahías para trabajos largos. Tercero, la motorización por departamento sirve como contexto, pero no basta para decidir dónde abrir una sede, porque refleja el lugar de matrícula y no el de circulación; para esa decisión haría falta información local, como las propias citas del taller agrupadas por zona.`),
  );

  // 7. CI
  add(
    h1('Integración Continua'),
    p(`El workflow de GitHub Actions existente (PostgreSQL 16, Python 3.12, pytest y verificación de la especificación OpenAPI) no necesitó cambios: ejecuta las pruebas unitarias y de integración y DuckDB se instala desde \`requirements.txt\`. La Figura ${fig('15_ci_verde.png')} muestra la ejecución ${CI.id} del commit \`${CI.head_sha.slice(0, 7)}\` con resultado *${CI.conclusion}*. El workflow solo se dispara cuando cambia el backend; esa ejecución incluye el último cambio del backend (\`${CI.ultimo_commit_backend.slice(0, 7)}\`) y los commits posteriores solo modifican documentación y evidencia.`),
    figure(img('15_ci_verde.png'), 'Workflow de GitHub Actions en verde', `Ejecución ${CI.html_url}`, 520),
  );

  // Preguntas orientadoras
  add(
    h1('Respuestas a las Preguntas Orientadoras'),
    h2('1. Aprendizajes relacionados con el quehacer del ingeniero de software'),
    p('**Las reglas de arquitectura se pueden convertir en pruebas.** Decir que "el dominio no depende de Flask" es fácil; mantenerlo cuando el proyecto crece no lo es. Expresar la regla de dependencias como una prueba que lee los *imports* hace que una violación rompa el CI, igual que un error funcional. En un equipo profesional esto evita que la arquitectura se degrade con cada cambio apresurado.'),
    p(`**Inyectar dependencias cambia lo que se puede probar.** Con los puertos recibidos por el constructor, las reglas centrales (asignar bahía y mecánico, dividir el pago 30/70, confirmar la cita con el depósito) se prueban en milisegundos sin base de datos: ${UNIT.passed} pruebas unitarias en ${fmt(UNIT.seconds, 2)} s frente a 0 antes de la guía. Las pruebas de integración siguen siendo necesarias, pero ya no son la única red de seguridad.`),
    p('**Toda dependencia externa puede fallar y el diseño debe asumirlo.** El circuit breaker y el backoff no son teoría: la demostración controlada mostró rechazos en microsegundos cuando la API está caída y la recuperación automática cuando vuelve. Separar errores transitorios (se reintentan) de permanentes (no) y usar un breaker por dependencia son decisiones que se repiten en cualquier sistema que consuma servicios de terceros.'),
    p('**Los datos abiertos hay que verificarlos antes de concluir.** Los datos de RUNT incluían años de registro imposibles y cifras por departamento que no reflejan dónde circulan los vehículos. Validar el cálculo ponderado contra una expansión fila por fila y explicar los valores atípicos fue tan importante como escribir la consulta. Un ingeniero que entrega analítica es responsable de sus limitaciones.'),
    h2('2. Mayor dificultad y cómo se resolvió'),
    p('La mayor dificultad fue **refactorizar sin romper nada**: se movieron 9 blueprints, todos los modelos y repositorios, y la lógica de negocio pasó de las rutas a los casos de uso, mientras el frontend y la API documentada debían seguir respondiendo exactamente igual. La estrategia fue apoyarse en las pruebas existentes, agregar pruebas de caracterización donde no había cobertura y verificarlas primero contra el código original, comprobar con `flask db check` que el esquema no cambiaba y comparar la especificación OpenAPI antes y después.'),
    p('Otras dificultades reales y su solución:'),
    bullet('**Limitaciones de DuckDB.** `CREATE VIEW` no admite parámetros preparados y un `LEFT JOIN` con una subconsulta correlacionada no está soportado; se resolvió usando un literal escapado para la ruta (que sale de la configuración, no del usuario) y calculando primero la clave de cruce para luego hacer un join simple.'),
    bullet('**Nombres que no coinciden entre fuentes.** RUNT y la DIVIPOLA escriben distinto Bogotá y San Andrés; se normalizaron los nombres y una prueba verifica que el total de vehículos se conserva en el cruce.'),
    bullet('**Consulta SoQL mal codificada.** La primera prueba contra Socrata respondió `400 query.compiler.malformed` porque toda la consulta viajaba en un solo parámetro; se detectó por la respuesta real y se corrigió.'),
    bullet('**Evidencia fiel.** Las primeras capturas mostraban `->` y `!=` como símbolos (ligaduras de la fuente) y partían líneas de pytest; se corrigió la presentación sin alterar la salida real de los comandos.'),
    p('Para el equipo, la dificultad conceptual principal fue **entender la arquitectura hexagonal lo suficiente para explicarla**: al principio no era evidente por qué separar puertos y adaptadores, ni por qué un servicio debe recibir sus dependencias en lugar de crearlas. La estrategia fue seguir una petición completa a través de las capas —`POST /appointments` en `api/`, `AppointmentService.book` en `application/`, el `ResourceAllocator` y los puertos en `domain/`, y el repositorio SQLAlchemy en `infrastructure/`—, apoyarse en el ADR para entender el porqué de cada decisión y leer las pruebas con mocks, que muestran de qué depende cada servicio sin necesidad de la base de datos. La prueba de arquitectura ayudó a fijar la regla: si el dominio importa Flask, la prueba falla.'),
    h2('3. Evidencia técnica de los entregables'),
    ...table('Entregables y evidencia', ['Entregable de la guía', 'Evidencia'], [
      ['Arquitectura hexagonal de 4 capas', `\`backend/{domain,application,api,infrastructure}\`, \`bootstrap.py\`, \`tests/unit/test_architecture.py\`; Figuras ${fig('01_estructura_hexagonal.png')} y ${fig('03_puerto_y_adaptador.png')}`],
      ['DI por constructor en ≥ 2 servicios + mocks', `\`application/scheduling\`, \`application/payments\`; ${MOCKS.passed} pruebas con \`create_autospec\`; Figuras ${fig('04_servicio_di_constructor.png')} y ${fig('05_test_con_mock.png')}`],
      ['ADR en inglés con bounded contexts', `\`docs/adr/0001-hexagonal-architecture.md\`; Tabla ${tab('Bounded contexts identificados')}; Figura ${fig('16_adr.png')}`],
      ['2 APIs colombianas', `\`infrastructure/market_data/clients.py\`; Tabla ${tab('Fuentes de datos abiertos integradas')}; Figuras ${fig('06_api_datos_gov_co.png')} y ${fig('07_api_dane.png')}`],
      ['Circuit breaker (3 estados) y retry con backoff', `\`infrastructure/resilience/\`; Tabla ${tab('Tiempos reales entre reintentos')}; Figuras ${fig('08_circuit_breaker_estados.png')} a ${fig('14_ui_circuit_breaker_abierto.png')}`],
      ['≥ 2 consultas DuckDB con estadísticas + UI', `\`infrastructure/analytics/queries.py\`; Tablas ${tab('Antigüedad del parque automotor activo por clase (años desde el registro)')} y ${tab('Estadísticas descriptivas de la motorización entre departamentos')}; Figuras ${fig('11_duckdb_q1_antiguedad.png')} a ${fig('17_swagger_market.png')}`],
      ['Pruebas y CI en verde', `${ALL.passed} pruebas (${UNIT.passed} unitarias + ${INTEG.passed} de integración); Figuras ${fig('02_pytest_verde.png')} y ${fig('15_ci_verde.png')}`],
      ['Trazabilidad del uso de IA', '`docs/USO_DE_IA.md`'],
    ], [3200, 6160], { notes: 'Commits de la rama `mecatrack-final` para esta guía: ' + COMMITS.map((c) => c.split(' ')[0]).join(', ') + '. Toda la evidencia se regenera con `./scripts/generar_evidencia.sh`.' }),
    h2('4. Ventajas y errores de la IA como asistente de programación'),
    p('En esta práctica se usó Claude Code (Anthropic, 2026), un agente que trabaja en la terminal: lee el repositorio, ejecuta comandos y pruebas y aplica cambios que el equipo aprueba fase por fase. El detalle de qué generó la IA y qué se verificó está en `docs/USO_DE_IA.md`.'),
    p('**Ventajas observadas.** Consultó las APIs reales antes de escribir los clientes, en lugar de suponer URLs o campos; escribió pruebas junto con cada cambio y propuso verificaciones independientes (pruebas de caracterización contra el código original, mutaciones para comprobar que las pruebas fallan, validación cruzada de las estadísticas ponderadas); y automatizó la evidencia y este informe a partir de ejecuciones reales.'),
    p('**Errores reales de la IA y cómo se detectaron.** Dejó líneas sin sentido en dos archivos (una llamada a un método inexistente y un `if False else`), que se detectaron al revisar el código antes de las pruebas; codificó mal una consulta SoQL (respuesta 400 de la API); usó construcciones SQL que DuckDB no soporta (errores en la ejecución real); escribió en un docstring que unas pruebas se habían hecho "antes del refactor" cuando no era cierto, y en el ADR contó 11 servicios cuando eran 12 (ambos detectados al releer contra los hechos); y generó capturas con ligaduras tipográficas que cambiaban la apariencia del código (detectado al revisar cada imagen). Todo se corrigió antes del commit de cada fase. La lección es la misma de la guía anterior: la IA acelera el trabajo, pero cada salida necesita una verificación independiente.'),
    p('**Sobre GitHub Copilot.** En esta guía no se usó GitHub Copilot; toda la asistencia de IA fue con Claude Code. La evaluación crítica que pide la guía se hizo sobre una sugerencia real de ese asistente: para cruzar los departamentos de RUNT con los de la DIVIPOLA propuso un `LEFT JOIN` con una subconsulta correlacionada (`NOT EXISTS`) dentro de la condición del join. La idea era correcta —aceptar la coincidencia por prefijo solo cuando no hay coincidencia exacta—, pero la sugerencia no funcionaba: DuckDB la rechazó al ejecutarla con el error *Cannot perform non-inner join on subquery*. Se detectó en la ejecución real contra los datos descargados y se corrigió calculando primero la clave de cruce en una expresión aparte (`clave_resuelta`) y haciendo luego un join simple. Para verificar la corrección se agregó una prueba que comprueba que el total de vehículos no se pierde ni se duplica en el cruce.'),
  );

  // Enlaces
  add(
    h1('Enlaces'),
    link('Repositorio', REPO_URL, ' (ramas `master` y `mecatrack-final`).'),
    link('Pipeline CI/CD', CI.html_url, ` (ejecución ${CI.id}, resultado *${CI.conclusion}*).`),
    link('Video en inglés (YouTube)', VIDEO_URL),
  );

  // Referencias (APA 7, orden alfabético, sangría francesa)
  const refs = [
    'Anthropic. (2026). *Claude Code* [Software]. https://claude.com/claude-code',
    'Brooker, M. (2015, 4 de marzo). *Exponential backoff and jitter*. AWS Architecture Blog. https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/',
    'Cockburn, A. (2005). *Hexagonal architecture*. https://alistair.cockburn.us/hexagonal-architecture/',
    'Departamento Administrativo Nacional de Estadística [DANE]. (s. f.-a). *Censo Nacional de Población y Vivienda 2018*. Recuperado el 24 de octubre de 2026, de https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivenda-2018',
    'Departamento Administrativo Nacional de Estadística [DANE]. (s. f.-b). *Distribución de la población total censada CNPV 2018 por municipio* [Servicio de mapas ArcGIS REST]. Geoportal DANE. Recuperado el 24 de octubre de 2026, de https://geoportal.dane.gov.co/',
    'Departamento Administrativo Nacional de Estadística [DANE]. (2025). *DIVIPOLA - Códigos municipios* [Conjunto de datos]. datos.gov.co. Recuperado el 24 de octubre de 2026, de https://www.datos.gov.co/d/gdxc-w37w',
    'DuckDB Foundation. (s. f.). *DuckDB documentation: Loading JSON*. Recuperado el 24 de octubre de 2026, de https://duckdb.org/docs/stable/data/json/overview',
    'Eastlake, D., & Panitz, A. (1999). *Reserved top level DNS names* (RFC 2606). Internet Engineering Task Force. https://doi.org/10.17487/RFC2606',
    'Esri. (s. f.). *Query (Map Service/Layer)*. ArcGIS REST APIs. Recuperado el 24 de octubre de 2026, de https://developers.arcgis.com/rest/services-reference/enterprise/query-map-service-layer/',
    'Evans, E. (2003). *Domain-driven design: Tackling complexity in the heart of software*. Addison-Wesley.',
    'Fowler, M. (2014, 6 de marzo). *CircuitBreaker*. martinfowler.com. https://martinfowler.com/bliki/CircuitBreaker.html',
    'GitHub. (s. f.). *GitHub Actions documentation*. GitHub Docs. Recuperado el 24 de octubre de 2026, de https://docs.github.com/en/actions',
    'Microsoft. (s. f.). *Playwright for Python*. Recuperado el 24 de octubre de 2026, de https://playwright.dev/python/',
    'Ministerio de Transporte. (2026). *Crecimiento del parque automotor RUNT 2.0* [Conjunto de datos]. datos.gov.co. Recuperado el 24 de octubre de 2026, de https://www.datos.gov.co/Transporte/CRECIMIENTO-DEL-PARQUE-AUTOMOTOR-RUNT2-0/u3vn-bdcy',
    'Nygard, M. T. (2011, 15 de noviembre). *Documenting architecture decisions*. Cognitect. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions',
    'Nygard, M. T. (2018). *Release it! Design and deploy production-ready software* (2.ª ed.). Pragmatic Bookshelf.',
    'Pallets Projects. (s. f.). *Flask documentation (3.1.x)*. Recuperado el 24 de octubre de 2026, de https://flask.palletsprojects.com/en/stable/',
    'pytest-dev. (s. f.). *pytest documentation*. Recuperado el 24 de octubre de 2026, de https://docs.pytest.org/en/stable/',
    'Python Software Foundation. (s. f.-a). *abc — Abstract base classes*. Python 3 documentation. Recuperado el 24 de octubre de 2026, de https://docs.python.org/3/library/abc.html',
    'Python Software Foundation. (s. f.-b). *unittest.mock — mock object library*. Python 3 documentation. Recuperado el 24 de octubre de 2026, de https://docs.python.org/3/library/unittest.mock.html',
    'SQLAlchemy. (s. f.). *SQLAlchemy 2.0 documentation*. Recuperado el 24 de octubre de 2026, de https://docs.sqlalchemy.org/en/20/',
    'Tyler Technologies. (s. f.). *Queries using SODA*. Socrata Developer Portal. Recuperado el 24 de octubre de 2026, de https://dev.socrata.com/docs/queries/',
  ];
  add(
    pageBreak(),
    new Paragraph({ heading: 'Heading1', children: [new TextRun('Referencias')] }),
    ...refs.map(reference),
  );

  // Declaración de uso de IA
  add(
    h1('Declaración de Uso de Inteligencia Artificial'),
    p('En este trabajo se utilizó Claude Code (Anthropic, 2026) como asistente de programación. A partir de las instrucciones del equipo y por fases aprobadas una a una, la IA generó: el refactor a arquitectura hexagonal, los casos de uso y adaptadores, las pruebas unitarias y de integración, los clientes de las APIs con circuit breaker y reintentos, las consultas de DuckDB, la vista Mercado, el ADR, los scripts de evidencia y el borrador de este informe, que se genera a partir de las evidencias.'),
    p('El equipo definió los requisitos y las reglas de trabajo (no inventar datos, un commit por fase, no publicar sin autorización), aprobó el plan y cada fase y autorizó la publicación en GitHub. Las cifras de pruebas, tiempos, respuestas de las APIs y resultados analíticos provienen de ejecuciones reales y no se editaron a mano. El registro detallado está en `docs/USO_DE_IA.md`.'),
    p('El equipo revisó y aprobó el diagnóstico y el plan por fases, decidió migrar las nueve rutas del backend a la arquitectura nueva, aprobó los conjuntos de datos elegidos, autorizó cada publicación en GitHub, pidió eliminar del repositorio las actividades anteriores (`Taller1` y `Actividad_2`) y dejar el proyecto como raíz, y solicitó el rol de administrador con la recepción de clientes. No se usó GitHub Copilot ni otra herramienta de IA distinta de Claude Code.'),
  );

  // Anexo A: SQL real ejecutado
  add(
    pageBreak(),
    h1('Anexo A. Consultas SQL Ejecutadas en DuckDB'),
    h3('Consulta 1: antigüedad del parque por clase'),
    ...code(Q1.sql, 13),
    h3('Consulta 2: motorización por departamento y resumen'),
    ...code(Q2.sql, 13),
    h3('Consulta 3: distribución por rangos de antigüedad'),
    ...code(Q3.sql, 13),
  );

  return children;
}

buildContent(); // primera pasada: números de tablas y figuras
const children = buildContent();
const doc = A.apaDocument({ title: 'Informe Guía 6 MecaTrack', description: TITLE, children });
const out = path.join(__dirname, 'Informe_Guia6_MecaTrack.docx');
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  const { tables, figures } = N.counts();
  console.log(`Informe generado: ${path.relative(ROOT, out)} (${tables} tablas, ${figures} figuras, ${(buf.length / 1024 / 1024).toFixed(1)} MB)`);
});
