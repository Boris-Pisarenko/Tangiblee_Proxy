import subprocess
import sys
import os
import logging
import json
import time
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QCheckBox, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QIcon
import update_manager  
import mitm_proxy_runner  # Импортируем новый файл

LOG_FILE = "mitmproxy.log"
SCRIPT_STORAGE_FILE = "inject_scripts.json"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class ProxyGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tangiblee_Proxy")
        self.setWindowIcon(QIcon("icons8-qa-64.ico"))

        self.label = QLabel("Прокси: выключен", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status_color("red")

        # Новая галочка для простого запуска mitmproxy
        self.simple_proxy_checkbox = QCheckBox("Просто включить mitmproxy", self)

        self.staging_checkbox = QCheckBox("Подмена для staging PROD", self)
        self.inject_checkbox = QCheckBox("Включить Inject Script", self)

        self.domain_input = QLineEdit(self)
        self.domain_input.setPlaceholderText("Введите домен (example.com)")

        self.script_input = QTextEdit(self)
        self.script_input.setPlaceholderText("Введите JavaScript-код для инжекции")

        self.start_button = QPushButton("Старт", self)
        self.stop_button = QPushButton("Стоп", self)
        self.update_button = QPushButton("🔄 Обновить")

        self.cert_button = QPushButton("Установить сертификаты mitmproxy", self)
        self.cert_button.clicked.connect(self.open_certificates_page)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.simple_proxy_checkbox)  # Новая галочка
        layout.addWidget(self.staging_checkbox)
        layout.addWidget(self.inject_checkbox)
        layout.addWidget(QLabel("Домен для Inject Script:"))
        layout.addWidget(self.domain_input)
        layout.addWidget(QLabel("JavaScript-код:"))
        layout.addWidget(self.script_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.update_button)
        layout.addWidget(self.cert_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

        self.start_button.clicked.connect(self.start_proxy)
        self.stop_button.clicked.connect(self.stop_proxy)
        self.update_button.clicked.connect(update_manager.update_app)  

        self.mitm_process = None

    def set_status_color(self, color):
        """Изменяет цвет текста статуса"""
        palette = self.label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("green" if color == "green" else "red"))
        self.label.setPalette(palette)

    def start_proxy(self):
        """Запускает mitmproxy с разными настройками"""
        
        # Если выбрана галочка "Просто включить mitmproxy"
        if self.simple_proxy_checkbox.isChecked():
            mitm_proxy_runner.start_mitmproxy_simple()
            self.label.setText("✅ mitmproxy ВКЛЮЧЕН (без скриптов)")
            self.set_status_color("green")
            return  # Прерываем выполнение других скриптов

        scripts = []

        if self.staging_checkbox.isChecked():
            scripts.append("modify_url.py")

        if self.inject_checkbox.isChecked():
            if not self.domain_input.text().strip() or not self.script_input.toPlainText().strip():
                self.label.setText("⚠️ Введите домен и скрипт!")
                self.set_status_color("red")
                return

            self.update_inject_script()
            scripts.append("inject_script.py")

        if not scripts:
            self.label.setText("⚠️ Выберите хотя бы один скрипт!")
            self.set_status_color("red")
            return

        try:
            subprocess.run([
                "reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "1", "/f"
            ], check=True)

            subprocess.run([
                "reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                "/v", "ProxyServer", "/t", "REG_SZ", "/d", "127.0.0.1:8080", "/f"
            ], check=True)

            command = ["mitmweb", "-s"] + scripts
            self.mitm_process = subprocess.Popen(command)

            self.label.setText("✅ Прокси ВКЛЮЧЕН")
            self.set_status_color("green")

        except Exception as e:
            logging.error(f"Ошибка запуска прокси: {e}")
            self.label.setText("Ошибка запуска!")
            self.set_status_color("red")

    def stop_proxy(self):
        """Останавливает mitmproxy"""
        if self.mitm_process:
            self.mitm_process.terminate()
            self.mitm_process = None

        subprocess.run(["taskkill", "/F", "/IM", "mitmweb.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.run([
            "reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
            "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "0", "/f"
        ], check=True)

        self.label.setText("🔴 Прокси ВЫКЛЮЧЕН")
        self.set_status_color("red")

    def open_certificates_page(self):
        """Открывает страницу установки сертификатов"""
        subprocess.run(["cmd", "/c", "start", "http://mitm.it/"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProxyGUI()
    window.show()
    sys.exit(app.exec())
