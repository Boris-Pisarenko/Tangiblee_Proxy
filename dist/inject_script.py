from mitmproxy import http
import json
import os

# Файл со скриптами
SCRIPT_STORAGE_FILE = "inject_scripts.json"

# Загружаем скрипты
if os.path.exists(SCRIPT_STORAGE_FILE):
    with open(SCRIPT_STORAGE_FILE, "r", encoding="utf-8") as file:
        try:
            TARGET_SCRIPTS = json.load(file)
        except json.JSONDecodeError:
            TARGET_SCRIPTS = {}
else:
    TARGET_SCRIPTS = {}

def response(flow: http.HTTPFlow) -> None:
    """
    Инжектит скрипт в HTML-страницы перед `</body>`.
    """
    url = flow.request.pretty_url

    for domain, script in TARGET_SCRIPTS.items():
        if domain in url:
            if "text/html" in flow.response.headers.get("Content-Type", ""):
                # Убираем строгий `Content-Security-Policy`, чтобы скрипт загружался
                if "Content-Security-Policy" in flow.response.headers:
                    del flow.response.headers["Content-Security-Policy"]

                # Вставляем скрипт перед `</body>`
                flow.response.text = flow.response.text.replace("</body>", script + "</body>")

                print(f"✅ Script injected for {domain} into: {url}")
                break
