import os
import requests
import zipfile
import shutil
import time
import logging
import sys

UPDATE_URL = "https://github.com/Boris-Pisarenko/Tangiblee_Proxy/raw/master/update.zip"
LOG_FILE = "mitmproxy.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def download_update():
    """Скачивает обновление и сохраняет как update.zip"""
    update_path = os.path.join(os.getcwd(), "update.zip")
    logging.info("🔄 Начинаю загрузку обновления...")

    try:
        response = requests.get(UPDATE_URL, timeout=30, stream=True)
        if response.status_code == 200:
            with open(update_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            time.sleep(2)  
            if zipfile.is_zipfile(update_path):
                logging.info("✅ Обновление загружено и проверено как ZIP-архив!")
                return update_path
            else:
                logging.error("❌ Ошибка: скачанный файл не является ZIP-архивом!")
                os.remove(update_path)
                return None
        else:
            logging.error(f"❌ Ошибка загрузки обновления! Код {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки обновления: {e}")
        return None

def extract_update(update_path):
    """Распаковывает новые файлы с заменой"""
    temp_dir = os.path.join(os.getcwd(), "update_temp")

    try:
       
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)

        
        with zipfile.ZipFile(update_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        
        extracted_files = os.listdir(temp_dir)
        if not extracted_files:
            logging.error("❌ Ошибка: файлы не были извлечены! Проверьте ZIP-архив.")
            return False

        logging.info(f"📂 Файлы в update_temp: {extracted_files}")

        
        for item in extracted_files:
            source_path = os.path.join(temp_dir, item)
            destination_path = os.path.join(os.getcwd(), item)

            
            if item == LOG_FILE:
                continue

            try:
                if os.path.exists(destination_path):
                    os.remove(destination_path)  
                shutil.move(source_path, destination_path)
                logging.info(f"📂 Файл {item} обновлен")
            except Exception as e:
                logging.error(f"Ошибка обновления {item}: {e}")

        
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info("🗑️ Временная папка update_temp удалена")

        os.remove(update_path)

        logging.info("✅ Обновление завершено.")
        return True

    except Exception as e:
        logging.error(f"❌ Ошибка при обновлении: {e}")
        return False

def restart_app():
    """Перезапускает приложение"""
    logging.info("🔄 Перезапуск приложения...")
    time.sleep(3)
    python = sys.executable
    os.execl(python, python, *sys.argv)

def update_app():
    """Главная функция обновления"""
    update_path = download_update()
    if update_path and extract_update(update_path):
        restart_app()