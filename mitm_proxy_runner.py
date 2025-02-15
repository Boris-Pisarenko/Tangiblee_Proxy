import subprocess
import logging

LOG_FILE = "mitmproxy.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def start_mitmproxy_simple():
    """Запускает mitmproxy без скриптов, просто в режиме веб-интерфейса"""
    try:
        logging.info("✅ Запуск mitmproxy в простом режиме...")
        
        
        subprocess.run([
            "reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
            "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "1", "/f"
        ], check=True)

        subprocess.run([
            "reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
            "/v", "ProxyServer", "/t", "REG_SZ", "/d", "127.0.0.1:8080", "/f"
        ], check=True)

        
        subprocess.Popen(["mitmweb"])

        logging.info("✅ mitmproxy запущен!")
    except Exception as e:
        logging.error(f"❌ Ошибка запуска mitmproxy: {e}")
