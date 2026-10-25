"""
Capturas de evidencia de la Guia 6 -> docs/evidencia/*.png

Cada captura sale de una ejecucion REAL: los comandos se ejecutan aqui y su
salida se guarda en docs/evidencia/salidas/*.txt antes de convertirse en
imagen; la UI y GitHub se capturan con Playwright (Chromium headless).

Etapas (las orquesta scripts/generar_evidencia.sh):
    terminal     01-12: estructura, pytest, codigo, APIs, breaker, retry, DuckDB
    ui           13, 17: panel Mercado y Swagger (backend normal en :5000)
    ui-breaker   14: breaker ABIERTO en la UI (backend con datos.gov.co invalido: DEMOSTRACION CONTROLADA)
    web          15-16: CI en GitHub Actions y ADR en GitHub (repositorio publico)

    backend/venv/bin/python scripts/evidencia/capturar.py terminal ui ui-breaker web
"""

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402
from render import code_panel, find_lines, terminal_panel  # noqa: E402

ROOT = render.ROOT
OUT = os.path.join(ROOT, 'docs', 'evidencia')
TXT = os.path.join(OUT, 'salidas')
PY = os.path.join(ROOT, 'backend', 'venv', 'bin', 'python')
API = 'http://127.0.0.1:5000'
FRONTEND = 'http://127.0.0.1:5500'
OWNER = {'email': os.environ.get('EVIDENCIA_EMAIL', 'carlos.owner@tallermecanico.com'),
         'password': os.environ.get('EVIDENCIA_PASSWORD', 'test1234')}
REPO = 'pablo-rodriguez091004/TallerDeProgramaci-n'
BRANCH = 'mecatrack-final'
NOW = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M %Z')


def run(command, cwd=ROOT, env=None, name=None, check=True):
    """Ejecuta un comando REAL, guarda su salida en salidas/<name>.txt y la devuelve."""
    result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True,
                            env={**os.environ, 'COLUMNS': '118', **(env or {})})
    output = result.stdout + (result.stderr if result.returncode else '')
    if name:
        with open(os.path.join(TXT, f'{name}.txt'), 'w', encoding='utf-8') as f:
            f.write(f'# {command}\n# cwd: {os.path.relpath(cwd, ROOT) or "."} | {NOW} | exit {result.returncode}\n\n')
            f.write(render.strip_ansi(output))
    if check and result.returncode != 0:
        raise SystemExit(f'Fallo el comando ({result.returncode}): {command}\n{output[-3000:]}')
    return output


def save(browser, name, title, subtitle, panels, width=1180):
    render.render(browser, os.path.join(OUT, name), title, subtitle, panels, width)
    print(f'  {name}')


def lines_of(text, start_marker, end_marker=None):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if start_marker in line)
    end = len(lines) if end_marker is None else next(i for i, line in enumerate(lines) if i > start and end_marker in line)
    return '\n'.join(lines[start:end])


# ------------------------------------------------------------------------------------------ terminal

def stage_terminal(browser):
    # 01. Estructura hexagonal (salida real de tree)
    tree_core = run("tree -L 2 --noreport -I '__pycache__' domain application",
                    cwd=os.path.join(ROOT, 'backend'), name='01_tree_domain_application')
    tree_edges = run("tree -L 2 --noreport -I '__pycache__' api infrastructure",
                     cwd=os.path.join(ROOT, 'backend'), name='01_tree_api_infrastructure')
    tree_root = run("tree -L 1 --noreport -I '__pycache__|venv|var|pytest-report.xml'",
                    cwd=os.path.join(ROOT, 'backend'), name='01_tree_backend')
    counts = run("for l in domain application api infrastructure; do printf '%-15s %3s archivos .py\\n' $l "
                 "$(find $l -name '*.py' ! -name '__init__.py' | wc -l); done",
                 cwd=os.path.join(ROOT, 'backend'), name='01_conteo')
    save(browser, '01_estructura_hexagonal.png', 'Arquitectura hexagonal: 4 capas en backend/',
         f'Salida real de tree y find ({NOW}). Bounded contexts como subpaquetes de domain/ y application/.',
         [[terminal_panel(['cd backend', "tree -L 1 --noreport -I '__pycache__|venv|var|pytest-report.xml'"], tree_root),
           terminal_panel("for l in domain application api infrastructure; do ...; done  # archivos por capa", counts)],
          [terminal_panel("tree -L 2 --noreport -I '__pycache__' domain application", tree_core),
           terminal_panel("tree -L 2 --noreport -I '__pycache__' api infrastructure", tree_edges)]])

    # 02. pytest completo
    pytest_out = run('venv/bin/python -m pytest -q -p no:warnings --color=yes', cwd=os.path.join(ROOT, 'backend'),
                     name='02_pytest_completo')
    python = run('venv/bin/python --version', cwd=os.path.join(ROOT, 'backend')).strip()
    commit = run('git rev-parse --short HEAD').strip()
    save(browser, '02_pytest_verde.png', 'Suite completa de pytest en verde',
         f'{python} · commit {commit} · {NOW}. tests/unit (sin BD, con mocks) + tests/integration (Flask + PostgreSQL).',
         [terminal_panel(['cd backend', 'venv/bin/python -m pytest -q -p no:warnings --color=yes'], pytest_out)])

    # Conteos separados (solo texto, para el informe)
    run('venv/bin/python -m pytest tests/unit -q -p no:warnings', cwd=os.path.join(ROOT, 'backend'),
        name='02b_pytest_unitarias')
    run('venv/bin/python -m pytest tests/integration -q -p no:warnings', cwd=os.path.join(ROOT, 'backend'),
        name='02c_pytest_integracion')
    run('git log --format="%h %ad %s" --date=short 7cca398..HEAD', name='commits_guia6')

    # 03. Puerto en domain + adaptador en infrastructure
    port = 'backend/domain/scheduling/ports.py'
    adapter = 'backend/infrastructure/persistence/repositories/appointment_repository.py'
    save(browser, '03_puerto_y_adaptador.png', 'Puerto (domain) y su adaptador (infrastructure)',
         'AppointmentRepository es una clase abstracta del dominio; SqlAlchemyAppointmentRepository la implementa con SQL.',
         [code_panel(port, *find_lines(port, r'^class AppointmentRepository', r'def save')),
          code_panel(adapter, *find_lines(adapter, r'^from', r'^_VIEW_OPTIONS', include_end=False)),
          code_panel(adapter, *find_lines(adapter, r'^class SqlAlchemy', r'model, entity, pk')),
          code_panel(adapter, *find_lines(adapter, r'def has_blocking_overlap', r'return db.session.query'))])

    # 04. Servicio con DI por constructor + composition root
    service = 'backend/application/scheduling/services.py'
    boot = 'backend/bootstrap.py'
    save(browser, '04_servicio_di_constructor.png', 'Inyección de dependencias por constructor',
         'AppointmentService recibe sus 6 puertos en __init__; bootstrap.py (composition root) los cablea.',
         [code_panel(service, *find_lines(service, r'^class AppointmentService', r'self._uow.commit\(\)')),
          code_panel(boot, *find_lines(boot, r'^def build_container', r'^def install', include_end=False))])

    # 05. Test con mocks + ejecucion
    test = 'backend/tests/unit/test_appointment_service.py'
    mock_out = run('venv/bin/python -m pytest -p no:warnings --color=yes tests/unit/test_appointment_service.py '
                   'tests/unit/test_payment_service.py', cwd=os.path.join(ROOT, 'backend'), name='05_pytest_mocks')
    save(browser, '05_test_con_mock.png', 'Prueba unitaria con mocks (unittest.mock.create_autospec)',
         'Las 6 dependencias de AppointmentService son mocks del puerto: sin Flask ni PostgreSQL.',
         [code_panel(test, *find_lines(test, r'^@pytest.fixture', r"deps\['uow'\].commit.assert_called_once_with")),
          terminal_panel(['cd backend', 'venv/bin/python -m pytest tests/unit/test_appointment_service.py '
                          'tests/unit/test_payment_service.py'], mock_out)])

    # 06-07. APIs colombianas (respuesta real recortada)
    datos = run(f'{PY} scripts/evidencia/consultar_apis.py datos.gov.co', name='06_api_datos_gov_co')
    save(browser, '06_api_datos_gov_co.png', 'API 1: datos.gov.co (Socrata) responde',
         'Consulta real con el cliente resiliente del proyecto (retry + circuit breaker). JSON recortado a 3 registros.',
         [terminal_panel('backend/venv/bin/python scripts/evidencia/consultar_apis.py datos.gov.co', datos)])
    dane = run(f'{PY} scripts/evidencia/consultar_apis.py dane', name='07_api_dane')
    save(browser, '07_api_dane.png', 'API 2: geoportal del DANE (ArcGIS REST) responde',
         'Población total censada CNPV 2018 por municipio. JSON recortado a 3 registros.',
         [terminal_panel('backend/venv/bin/python scripts/evidencia/consultar_apis.py dane', dane)])

    # 08, 10. Demostracion controlada (una sola ejecucion real; se muestra en dos partes)
    demo = run(f'{PY} scripts/demo_resilience.py --json docs/evidencia/salidas/demo_resilience.json',
               name='08_10_demo_resilience')
    header = '\n'.join(demo.splitlines()[:2])
    part_b = lines_of(demo, '=== Parte B')
    part_a = lines_of(demo, '=== Parte A', '=== Parte B')
    save(browser, '08_circuit_breaker_estados.png', 'Circuit breaker: CLOSED → OPEN → HALF_OPEN → CLOSED',
         'DEMOSTRACIÓN CONTROLADA con red real: los fallos se fuerzan con un host .invalid (RFC 2606) y los éxitos '
         'van a datos.gov.co.',
         [terminal_panel('backend/venv/bin/python scripts/demo_resilience.py', f'{header}\n...\n{part_b}',
                         note='Se omite la Parte A (retry) de esta misma ejecución: aparece en la figura 10.')])
    save(browser, '10_retry_backoff.png', 'Retry con backoff exponencial y jitter: tiempos reales',
         'Misma ejecución que la figura 8. Techo = min(8, 0,5·2^(n-1)) s; espera = techo/2 + U(0, techo/2).',
         [terminal_panel('backend/venv/bin/python scripts/demo_resilience.py', f'{header}\n...\n{part_a}',
                         note='Se omite la Parte B (circuit breaker) de esta misma ejecución: aparece en la figura 8.')])

    # 09. Pruebas de transiciones
    cb_tests = run('venv/bin/python -m pytest -p no:warnings --color=yes tests/unit/test_circuit_breaker.py '
                   'tests/unit/test_retry.py tests/unit/test_resilient_http_client.py',
                   cwd=os.path.join(ROOT, 'backend'), name='09_pytest_resiliencia')
    save(browser, '09_circuit_breaker_pruebas.png', 'Pruebas de los 3 estados del breaker y del retry',
         'Reloj, sleep y transporte HTTP simulados: las transiciones se prueban sin esperas ni red.',
         [terminal_panel(['cd backend', 'venv/bin/python -m pytest tests/unit/test_circuit_breaker.py '
                          'tests/unit/test_retry.py tests/unit/test_resilient_http_client.py'], cb_tests)])

    # 11-12. DuckDB
    queries_file = 'backend/infrastructure/analytics/queries.py'
    q1 = run(f'{PY} scripts/evidencia/consultas_duckdb.py q1', name='11_duckdb_q1')
    save(browser, '11_duckdb_q1_antiguedad.png', 'DuckDB · Q1: antigüedad del parque por clase',
         'Estadísticas descriptivas ponderadas por número de vehículos sobre el JSON de RUNT.',
         [code_panel(queries_file, *find_lines(queries_file, r'^FLEET_AGE_BY_CLASS', r'^"""', include_end=True,
                                               after=find_lines(queries_file, r'^FLEET_AGE_BY_CLASS')[0] - 1)),
          terminal_panel('backend/venv/bin/python scripts/evidencia/consultas_duckdb.py q1', q1)], width=1380)
    q2 = run(f'{PY} scripts/evidencia/consultas_duckdb.py q2', name='12_duckdb_q2')
    run(f'{PY} scripts/evidencia/exportar_analitica.py', name='analitica_resumen')
    start = find_lines(queries_file, r'^MOTORIZATION_BY_DEPARTMENT')[0]
    save(browser, '12_duckdb_q2_motorizacion.png', 'DuckDB · Q2: motorización por departamento',
         'Cruce RUNT (MinTransporte) + DIVIPOLA + CNPV 2018 (DANE) y estadísticas entre departamentos.',
         [code_panel(queries_file, *find_lines(queries_file, r'^cruce AS', r'^"""', after=start)),
          code_panel(queries_file, *find_lines(queries_file, r'^MOTORIZATION_SUMMARY', r'^"""', after=start + 5)),
          terminal_panel('backend/venv/bin/python scripts/evidencia/consultas_duckdb.py q2', q2)], width=1380)


# ------------------------------------------------------------------------------------------ UI

def owner_page(browser, width=1280, height=900):
    context = browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=1.5)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(f'{FRONTEND}/index.html')
    response = page.request.post(f'{API}/auth/login', data=OWNER)
    if response.status != 200:
        raise SystemExit(f'Login del owner fallo ({response.status}). Define EVIDENCIA_EMAIL/EVIDENCIA_PASSWORD.')
    return page, errors


def guard_page(page, name):
    render.assert_no_secrets(page.content(), name)


def stage_ui(browser):
    page, errors = owner_page(browser)
    page.goto(f'{FRONTEND}/pages/mercado.html')
    page.click('#btn-actualizar')  # descarga REAL desde las 3 fuentes
    expect(page.locator('#mercado-info')).to_contain_text('Datos actualizados', timeout=90_000)
    page.wait_for_selector('#tabla-fuentes .badge')
    page.wait_for_selector('#tabla-antiguedad tbody tr')
    page.wait_for_timeout(600)
    guard_page(page, '13')
    # La pagina completa (~3400 px) no cabe legible en el informe: dos capturas por seccion.
    sections = page.locator('.mercado-bloque')
    motorization = sections.nth(1).bounding_box()
    page.screenshot(path=os.path.join(OUT, '13a_ui_mercado_fuentes_motorizacion.png'), full_page=True,
                    clip={'x': 0, 'y': 0, 'width': 1280, 'height': motorization['y'] + motorization['height'] + 16})
    # La barra de navegacion es sticky: al hacer scroll al elemento taparia la tabla.
    page.add_style_tag(content='.navbar { position: static !important; }')
    sections.nth(2).screenshot(path=os.path.join(OUT, '13b_ui_mercado_antiguedad.png'))
    print('  13a_ui_mercado_fuentes_motorizacion.png')
    print('  13b_ui_mercado_antiguedad.png')
    if errors:
        raise SystemExit(f'Errores de JavaScript en la UI: {errors}')

    page.goto(f'{API}/docs')
    expect(page.locator('.opblock').first).to_be_visible(timeout=20_000)
    section = page.locator('.opblock-tag-section').filter(has=page.locator('h3', has_text='Market'))
    section.scroll_into_view_if_needed()
    guard_page(page, '17')
    section.screenshot(path=os.path.join(OUT, '17_swagger_market.png'))
    print('  17_swagger_market.png')
    page.context.close()


def stage_ui_breaker(browser):
    """El backend corre con MARKET_SOCRATA_BASE_URL apuntando a un host .invalid (ver el .sh)."""
    page, _ = owner_page(browser)
    page.goto(f'{FRONTEND}/pages/mercado.html')
    page.wait_for_selector('#circuitos .circuito')
    page.click('#btn-actualizar')  # 1a: RUNT (2 intentos) + DIVIPOLA (1) = 3 fallos -> OPEN
    expect(page.locator('#mercado-info')).to_contain_text('Fallaron', timeout=60_000)
    page.click('#btn-actualizar')  # 2a: con el circuito abierto se rechaza sin salir a la red
    page.wait_for_function("document.querySelector('#btn-actualizar').disabled === false")
    expect(page.locator('#tabla-fuentes')).to_contain_text('Circuito abierto')
    page.wait_for_timeout(400)
    page.evaluate("document.querySelector('.page-header p').textContent = "
                  "'DEMOSTRACIÓN CONTROLADA: datos.gov.co apunta a un host .invalid; el DANE usa su URL real'")
    block = page.locator('.mercado-bloque').first
    guard_page(page, '14')
    block.screenshot(path=os.path.join(OUT, '14_ui_circuit_breaker_abierto.png'))
    print('  14_ui_circuit_breaker_abierto.png')
    page.context.close()


# ------------------------------------------------------------------------------------------ web

# Rutas que disparan el workflow (ver .github/workflows/mecatrack-tests.yml).
CI_PATHS = 'backend scripts/export_openapi.py docs/openapi.json .github/workflows/mecatrack-tests.yml'


def stage_web(browser):
    # El CI solo corre cuando cambia el backend: se busca el ultimo run terminado cuyo commit
    # INCLUYE el ultimo cambio relevante (los commits posteriores solo tocan docs/evidencia).
    relevant = run(f'git log -1 --format=%H -- {CI_PATHS}').strip()
    with urllib.request.urlopen(f'https://api.github.com/repos/{REPO}/actions/runs?branch={BRANCH}&per_page=20') as r:
        runs = [x for x in json.load(r)['workflow_runs'] if x['status'] == 'completed']
    covering = [x for x in runs if subprocess.run(['git', 'merge-base', '--is-ancestor', relevant, x['head_sha']],
                                                   cwd=ROOT, capture_output=True).returncode == 0]
    if not covering:
        raise SystemExit(f'Ningun CI terminado incluye el commit {relevant[:7]} (ultimo cambio del backend): haz push y '
                         'espera a que termine el workflow.')
    latest = covering[0]
    if latest['conclusion'] != 'success':
        raise SystemExit(f"El CI del ultimo cambio del backend no esta en verde: {latest['conclusion']} {latest['html_url']}")
    with open(os.path.join(TXT, '15_ci_run.json'), 'w', encoding='utf-8') as f:
        json.dump({k: latest[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion', 'html_url',
                                          'run_started_at', 'updated_at')}
                  | {'ultimo_commit_backend': relevant, 'head_local': run('git rev-parse HEAD').strip()}, f, indent=1)
    note = f'(incluye el ultimo cambio del backend, {relevant[:7]})'
    page = browser.new_page(viewport={'width': 1366, 'height': 900}, device_scale_factor=1.5)
    page.goto(latest['html_url'])
    page.wait_for_load_state('networkidle')
    page.screenshot(path=os.path.join(OUT, '15_ci_verde.png'))
    print(f"  15_ci_verde.png  (run {latest['id']}, commit {latest['head_sha'][:7]}) {note}")

    page.goto(f'https://github.com/{REPO}/blob/{BRANCH}/docs/adr/0001-hexagonal-architecture.md')
    article = page.locator('article.markdown-body').first
    article.wait_for(timeout=30_000)
    # Desde el titulo hasta el final de la tabla de bounded contexts (seccion 2.1).
    box = article.bounding_box()
    end = page.locator('article.markdown-body h3', has_text='2.2 Context map').first.bounding_box()
    page.screenshot(path=os.path.join(OUT, '16_adr.png'), full_page=True,
                    clip={'x': box['x'], 'y': box['y'], 'width': box['width'], 'height': end['y'] - box['y']})
    print('  16_adr.png (secciones 1 a 2.1)')
    page.close()


STAGES = {'terminal': stage_terminal, 'ui': stage_ui, 'ui-breaker': stage_ui_breaker, 'web': stage_web}


def main(stages):
    os.makedirs(TXT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for stage in stages:
            print(f'==> etapa {stage}')
            STAGES[stage](browser)
        browser.close()


if __name__ == '__main__':
    main(sys.argv[1:] or list(STAGES))
