"""
S25 Browser Service — Playwright API
Accessible via POST https://browser.smajor.org/task
ARKON peut appeler ce service directement pour toute tâche browser
"""
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os, base64, time

app = Flask(__name__)
try:
    from security.vault import vault_get
    SECRET = vault_get('S25_SHARED_SECRET', os.environ.get('S25_SECRET', ''))
except ImportError:
    SECRET = os.environ.get('S25_SECRET', '')

def auth(req):
    return (req.headers.get('X-S25-Secret') == SECRET or
            req.json.get('secret') == SECRET if req.is_json else False)

@app.route('/health')
def health():
    return jsonify({'ok': True, 'service': 'S25 Browser Service', 'version': '1.0'})

@app.route('/task', methods=['POST'])
def task():
    """
    Exécute une tâche browser.
    Body: {
        "secret": "<S25_SHARED_SECRET>",
        "url": "https://tradingview.com/...",
        "actions": [
            {"type": "navigate", "url": "..."},
            {"type": "click", "selector": "..."},
            {"type": "fill", "selector": "...", "value": "..."},
            {"type": "screenshot"},
            {"type": "get_text", "selector": "..."},
            {"type": "wait", "ms": 2000},
            {"type": "eval", "code": "document.title"}
        ],
        "screenshot_final": true
    }
    """
    if not auth(request):
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401

    data = request.json
    url = data.get('url', '')
    actions = data.get('actions', [])
    screenshot_final = data.get('screenshot_final', True)

    results = []
    screenshots = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            ctx = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = ctx.new_page()

            # Navigate to URL if provided
            if url:
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                results.append({'action': 'navigate', 'url': url, 'ok': True})

            # Execute actions
            for action in actions:
                atype = action.get('type', '')
                try:
                    if atype == 'navigate':
                        page.goto(action['url'], wait_until='domcontentloaded', timeout=30000)
                        results.append({'action': 'navigate', 'url': action['url'], 'ok': True})

                    elif atype == 'click':
                        page.click(action['selector'], timeout=10000)
                        results.append({'action': 'click', 'selector': action['selector'], 'ok': True})

                    elif atype == 'fill':
                        page.fill(action['selector'], action['value'], timeout=10000)
                        results.append({'action': 'fill', 'selector': action['selector'], 'ok': True})

                    elif atype == 'select':
                        page.select_option(action['selector'], action['value'])
                        results.append({'action': 'select', 'ok': True})

                    elif atype == 'wait':
                        time.sleep(action.get('ms', 1000) / 1000)
                        results.append({'action': 'wait', 'ok': True})

                    elif atype == 'wait_for':
                        page.wait_for_selector(action['selector'], timeout=15000)
                        results.append({'action': 'wait_for', 'ok': True})

                    elif atype == 'screenshot':
                        img = page.screenshot(full_page=action.get('full_page', False))
                        b64 = base64.b64encode(img).decode()
                        screenshots.append(b64)
                        results.append({'action': 'screenshot', 'ok': True, 'index': len(screenshots)-1})

                    elif atype == 'get_text':
                        text = page.text_content(action['selector'])
                        results.append({'action': 'get_text', 'text': text, 'ok': True})

                    elif atype == 'get_url':
                        results.append({'action': 'get_url', 'url': page.url, 'ok': True})

                    elif atype == 'eval':
                        result = page.evaluate(action['code'])
                        results.append({'action': 'eval', 'result': str(result), 'ok': True})

                    elif atype == 'press':
                        page.keyboard.press(action['key'])
                        results.append({'action': 'press', 'key': action['key'], 'ok': True})

                    elif atype == 'scroll':
                        page.mouse.wheel(0, action.get('y', 300))
                        results.append({'action': 'scroll', 'ok': True})

                except Exception as e:
                    results.append({'action': atype, 'ok': False, 'error': str(e)})

            # Final screenshot
            if screenshot_final:
                img = page.screenshot()
                screenshots.append(base64.b64encode(img).decode())

            final_url = page.url
            page_title = page.title()
            browser.close()

        return jsonify({
            'ok': True,
            'final_url': final_url,
            'page_title': page_title,
            'results': results,
            'screenshots': screenshots,
            'screenshots_count': len(screenshots)
        })

    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'results': results}), 500


@app.route('/screenshot', methods=['POST'])
def screenshot():
    """Prend juste un screenshot d'une URL — simple et rapide"""
    if not auth(request):
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401

    url = request.json.get('url', '')
    if not url:
        return jsonify({'ok': False, 'error': 'url required'}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)
            img = page.screenshot(full_page=True)
            browser.close()
            return jsonify({
                'ok': True,
                'url': url,
                'screenshot': base64.b64encode(img).decode()
            })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7070))
    print(f'S25 Browser Service démarré sur port {port}')
    app.run(host='0.0.0.0', port=port)
