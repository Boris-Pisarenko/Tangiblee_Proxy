import subprocess
import sys
import os
import logging
import time
import psutil
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QCheckBox, QLineEdit, QTextEdit, QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QIcon

VERSION = "1.0.5"

LOG_FILE = "mitmproxy.log"
MITMPROXY_INSTALLER = "mitmproxy-11.1.0-windows-x86_64-installer.exe"
MODIFY_SCRIPT = "modify_url.py"
INJECT_SCRIPT = "inject_script.py"
MITMPROXY_PROCESS_NAME = "mitmweb.exe"
UPDATE_MANAGER = "update_manager.exe"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class ProxyGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Tangiblee_Proxy v{VERSION}")
        self.setWindowIcon(QIcon("icons8-qa-64.ico"))
        self.setFixedWidth(800)  

        self.menu_bar = QMenuBar(self)
        self.menu = QMenu("Дополнительно", self)
        self.menu_bar.addMenu(self.menu)

        self.update_action = self.menu.addAction("Обновить")
        self.cert_action = self.menu.addAction("Установить сертификаты mitmproxy")
        self.install_mitmproxy_action = self.menu.addAction(f"Установить {MITMPROXY_INSTALLER}")

        self.update_action.triggered.connect(self.manual_update)
        self.cert_action.triggered.connect(self.install_certificates)
        self.install_mitmproxy_action.triggered.connect(self.install_mitmproxy)

        self.label = QLabel(f"Прокси: выключен (v{VERSION})", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status_color("red")

        self.simple_proxy_checkbox = QCheckBox("Запустить Mitmproxy Web UI (mitmweb)", self)
        self.staging_checkbox = QCheckBox("Использовать Staging вместо PROD", self)
        self.inject_checkbox = QCheckBox("Запуск Inject Script", self)

        self.domain_input = QLineEdit(self)
        self.domain_input.setPlaceholderText("Введите домен (example.com)")

        self.script_input = QTextEdit(self)
        self.script_input.setPlaceholderText(
            'Введите снипет для инъекции пример: '
            '<script async src="https://cdn.tangiblee.com/integration/5.0/managed/samsonite.com.co/revision_1/'
            'variation_original/tangiblee-bundle.min.js"></script>'
        )

        self.start_button = QPushButton("Старт", self)
        self.stop_button = QPushButton("Стоп", self)

        layout = QVBoxLayout()
        layout.setMenuBar(self.menu_bar)
        layout.addWidget(self.label)
        layout.addWidget(self.simple_proxy_checkbox)
        layout.addWidget(self.staging_checkbox)
        layout.addWidget(self.inject_checkbox)
        layout.addWidget(QLabel("Домен для Inject Script:"))
        layout.addWidget(self.domain_input)
        layout.addWidget(QLabel("JavaScript-код:"))
        layout.addWidget(self.script_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

        self.start_button.clicked.connect(self.start_proxy)
        self.stop_button.clicked.connect(self.stop_proxy)

        self.mitm_process = None
        logging.info(f"Запуск приложения Tangiblee_Proxy версии {VERSION}")

    def set_status_color(self, color):
        """Изменяет цвет текста статуса"""
        palette = self.label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("green" if color == "green" else "red"))
        self.label.setPalette(palette)

    def configure_windows_proxy(self, enable=True):
        """Настраивает прокси-сервер в Windows"""
        try:
            if enable:
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" '
                    '/v ProxyEnable /t REG_DWORD /d 1 /f',
                    shell=True, check=True)
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" '
                    '/v ProxyServer /t REG_SZ /d "127.0.0.1:8080" /f',
                    shell=True, check=True)
                logging.info("✅ Прокси включен в Windows")

            else:
                subprocess.run(
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" '
                    '/v ProxyEnable /t REG_DWORD /d 0 /f',
                    shell=True, check=True)

                try:
                    subprocess.run(
                        'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" '
                        '/v ProxyServer /f',
                        shell=True, check=True)
                except subprocess.CalledProcessError as err:
                    logging.warning(f"Ключ ProxyServer уже отсутствует: {err}")

                logging.info("✅ Прокси выключен в Windows")

        except Exception as e:
            logging.error(f"❌ Ошибка настройки прокси: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка настройки прокси: {e}")


    def install_mitmproxy(self):
        """Запускает установку mitmproxy"""
        if os.path.exists(MITMPROXY_INSTALLER):
            subprocess.Popen([MITMPROXY_INSTALLER], shell=True)
        else:
            QMessageBox.warning(self, "Ошибка", f"{MITMPROXY_INSTALLER} не найден!")

    def install_certificates(self):
        """Запускает mitmproxy перед установкой сертификатов"""
        if not self.simple_proxy_checkbox.isChecked():
            QMessageBox.warning(self, "Ошибка", "Для установки сертификатов необходимо включить mitmproxy!")
            return

        self.start_proxy()
        time.sleep(5)
        subprocess.run(["cmd", "/c", "start", "http://mitm.it/"])

    def start_proxy(self):
        """Запускает mitmproxy"""
        scripts = []

        if self.simple_proxy_checkbox.isChecked():
            self.configure_windows_proxy(True)
            self.mitm_process = subprocess.Popen(["mitmweb"])
            self.label.setText("✅ mitmproxy Web UI ВКЛЮЧЕН")
            self.set_status_color("green")
            return

        if self.staging_checkbox.isChecked():
            if os.path.exists(MODIFY_SCRIPT):
                scripts.append(MODIFY_SCRIPT)
            else:
                QMessageBox.warning(self, "Ошибка", f"Файл {MODIFY_SCRIPT} не найден!")

        if self.inject_checkbox.isChecked():
            if not self.domain_input.text().strip() or not self.script_input.toPlainText().strip():
                QMessageBox.warning(self, "Ошибка", "Введите домен и снипет для инъекции!")
                return
            if os.path.exists(INJECT_SCRIPT):
                scripts.append(INJECT_SCRIPT)
            else:
                QMessageBox.warning(self, "Ошибка", f"Файл {INJECT_SCRIPT} не найден!")

        if not scripts:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один скрипт для запуска mitmproxy!")
            return

        self.configure_windows_proxy(True)

        try:
            command = ["mitmweb", "-s"] + scripts
            self.mitm_process = subprocess.Popen(command)
            self.label.setText("✅ Прокси ВКЛЮЧЕН")
            self.set_status_color("green")
        except Exception as e:
            logging.error(f"Ошибка запуска прокси: {e}")
            QMessageBox.critical(self, "Ошибка", "Ошибка запуска mitmproxy!")

    def stop_proxy(self):
        """Останавливает mitmproxy"""
        try:
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if proc.info["name"] == MITMPROXY_PROCESS_NAME:
                    proc.kill()
                    logging.info(f"🔴 Процесс {MITMPROXY_PROCESS_NAME} убит")

            self.configure_windows_proxy(False)
            self.label.setText("🔴 Прокси ВЫКЛЮЧЕН")
            self.set_status_color("red")
        except Exception as e:
            logging.error(f"Ошибка при остановке прокси: {e}")
            QMessageBox.critical(self, "Ошибка", "Ошибка остановки mitmproxy!")

    def manual_update(self):
        """Запускает обновление"""
        if os.path.exists(UPDATE_MANAGER):
            subprocess.Popen([UPDATE_MANAGER], shell=True)
        else:
            QMessageBox.warning(self, "Ошибка", f"{UPDATE_MANAGER} не найден!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProxyGUI()
    window.show()
    sys.exit(app.exec())
