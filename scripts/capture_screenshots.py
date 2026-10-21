"""
Capturas de evidencia con Playwright (Chromium headless) sobre el servidor
REAL: maneja Swagger UI como una persona (Try it out -> Execute) y guarda
PNG en evidence/screenshots/.

No arranca servidores: usalo a traves de scripts/capture_screenshots.sh.
La captura del endpoint de IA hace UNA llamada real al LLM (queda en ai_calls).
"""

import os
import sys

from playwright.sync_api import expect, sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'evidence', 'screenshots')
API = os.environ.get('API_URL', 'http://127.0.0.1:5000')
FRONTEND = os.environ.get('FRONTEND_URL', 'http://127.0.0.1:5500')

AI_BODY = '{\n  "description": "Siento olor dulce dentro del carro y la temperatura sube cuando hay trancon",\n  "technique": "cot"\n}'


def opblock(page, method, path):
    return page.locator(f'.opblock-{method}').filter(
        has=page.locator('.opblock-summary-path', has_text=path).filter(has_not_text=path + '/'))


def run(page, method, path, *, param=None, body=None, expected_status, name, response_timeout=10_000):
    """Expande la operacion, Try it out, completa, Execute y captura el bloque."""
    block = opblock(page, method, path).first
    if not block.locator('.opblock-body').first.is_visible():
        block.locator('.opblock-summary').click()
    try_out = block.locator('.try-out__btn')
    if try_out.inner_text().strip() == 'Try it out':
        try_out.click()
    if param is not None:
        block.locator('tr[data-param-name] input').first.fill(str(param))
    if body is not None:
        block.locator('textarea.body-param__text').fill(body)
    block.locator('button.execute').click()
    status = block.locator('.live-responses-table tbody .response-col_status').first
    try:
        expect(status).to_have_text(str(expected_status), timeout=response_timeout)
    except AssertionError:
        block.screenshot(path=os.path.join(OUT, f'FAILED_{name}'))
        raise SystemExit(f'{name}: se esperaba HTTP {expected_status}, Swagger mostro '
                         f'{status.inner_text() if status.count() else "sin respuesta"} (ver FAILED_{name})')
    block.scroll_into_view_if_needed()
    block.screenshot(path=os.path.join(OUT, name))
    print(f'  {name}: HTTP {expected_status}')
    # Se colapsa para que la siguiente captura no herede este bloque abierto.
    block.locator('.opblock-summary').click()


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1366, 'height': 900}, device_scale_factor=1.5)

        # 1. Vista general de Swagger UI
        page.goto(f'{API}/docs')
        expect(page.locator('.opblock').first).to_be_visible(timeout=20_000)
        page.screenshot(path=os.path.join(OUT, '01_swagger_overview.png'), full_page=True)
        print('  01_swagger_overview.png')

        # 2. Documentacion de un endpoint: summary, description, ejemplo y respuestas
        post = opblock(page, 'post', '/api/v1/services').first
        post.locator('.opblock-summary').click()
        expect(post.locator('.opblock-description-wrapper').first).to_be_visible()
        post.screenshot(path=os.path.join(OUT, '02_swagger_post_docs_examples.png'))
        print('  02_swagger_post_docs_examples.png')
        post.locator('.opblock-summary').click()

        # En las capturas de ejecucion solo interesan la peticion y la respuesta
        # real: se oculta la tabla de respuestas documentadas (ya esta en la 02).
        # Tambien se quita el limite de 400 px del cuerpo para que no quede cortado.
        page.add_style_tag(content=(
            '.responses-inner > table.responses-table, .responses-inner > div > h4 { display: none; }'
            '.live-responses-table pre.microlight { max-height: none !important; }'))

        # 3. Login desde Swagger (deja la cookie de sesion en el navegador)
        run(page, 'post', '/auth/login', body=None, expected_status=200, name='03_login_200.png')

        # 4-7. Respuestas reales de la API
        run(page, 'get', '/api/v1/services', expected_status=200, name='04_get_services_200.png')
        run(page, 'get', '/api/v1/services/{service_id}', param=9999, expected_status=404,
            name='05_get_service_404.png')
        run(page, 'post', '/api/v1/services',
            body='{\n  "service_name": " ",\n  "estimated_duration_minutes": "una hora",\n  "base_price": -5\n}',
            expected_status=422, name='06_post_service_422.png')
        run(page, 'delete', '/api/v1/services/{service_id}', param=1, expected_status=409,
            name='07_delete_service_409.png')

        # 8. Endpoint de IA con el LLM real
        run(page, 'post', '/api/v1/ai/suggest-service', body=AI_BODY, expected_status=200,
            name='08_ai_suggest_service_200.png', response_timeout=60_000)

        # 9. El frontend existente sigue mostrando el catalogo (ruta antigua /services)
        if '--skip-frontend' not in sys.argv:
            page.goto(f'{FRONTEND}/pages/catalogo.html')
            page.wait_for_load_state('networkidle')
            page.screenshot(path=os.path.join(OUT, '09_frontend_catalogo.png'), full_page=True)
            print('  09_frontend_catalogo.png')

        browser.close()


if __name__ == '__main__':
    main()
