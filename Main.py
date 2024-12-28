import asyncio
import logging
import paramiko
import json
import threading
import time
from flask import Flask, render_template
from logging.handlers import RotatingFileHandler
import os

# Создание папки logs, если она не существует
if not os.path.exists('logs'):
    os.makedirs('logs')

# Создание объекта логгера
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования на DEBUG для подробных логов

# Создание обработчика для записи логов в файл с ротацией (ограничение размера файла до 50 MB)
file_handler = RotatingFileHandler('logs/server_monitor.log', maxBytes=50 * 1024 * 1024, backupCount=5)  # 50 MB
file_handler.setLevel(logging.WARNING)  # Устанавливаем уровень для записи в файл
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавление обработчика для записи в файл в логгер
logger.addHandler(file_handler)

# Создание консольного обработчика (чтобы выводить только ошибки и предупреждения)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Устанавливаем уровень для вывода в консоль
console_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger.addHandler(console_handler)

# Переменная для хранения времени последнего вывода
last_log_time = 0
log_interval = 300  # Интервал в секундах (5 минут)


# Асинхронная функция для выполнения команд на серверах
async def execute_command(server, command):
    global last_log_time
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server["host"],
            port=server["port"],
            username=server["username"],
            password=server["password"]
        )
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        ssh.close()
        return output
    except (paramiko.ssh_exception.NoValidConnectionsError, paramiko.ssh_exception.AuthenticationException) as e:
        # Ловим ошибки подключения и аутентификации
        current_time = time.time()  # Получаем текущее время
        if current_time - last_log_time >= log_interval:  # Проверяем, прошло ли 5 минут с последнего лога
            logger.warning(f"Ошибка подключения к серверу {server['host']}: {e}")
            last_log_time = current_time  # Обновляем время последнего лога
        return "Попытка установить соединение была безуспешной."
    except Exception as e:
        # Ловим другие ошибки и выводим их в журнал
        current_time = time.time()  # Получаем текущее время
        if current_time - last_log_time >= log_interval:  # Проверяем, прошло ли 5 минут с последнего лога
            logger.warning(f"Ошибка при выполнении команды на сервере {server['host']}: {e}")
            last_log_time = current_time  # Обновляем время последнего лога
        return "Попытка установить соединение была безуспешной."


# Функция для мониторинга серверов
async def monitor_server(server, data_store):
    while True:
        server_data = {}
        try:
            # Получаем информацию о времени работы сервера
            uptime = await execute_command(server, "uptime")
            if uptime:
                server_data["uptime"] = uptime
            else:
                server_data["uptime"] = "Нет данных"

            # Получаем информацию о памяти
            memory = await execute_command(server, "free -m")
            if memory:
                server_data["memory"] = memory
            else:
                server_data["memory"] = "Нет данных"

            # Получаем загрузку процессора
            cpu_usage = await execute_command(server, "mpstat 1 1")
            if cpu_usage:
                server_data["cpu_usage"] = cpu_usage
            else:
                server_data["cpu_usage"] = "Нет данных"

            # Получаем температуру
            temperature = await execute_command(server, "sensors")
            if temperature:
                server_data["temperature"] = temperature
            else:
                server_data["temperature"] = "Нет данных"

            # Сохраняем данные для текущего сервера
            data_store[server["host"]] = server_data
            logger.debug(f"Обновленные данные для сервера {server['host']}")
        except Exception as e:
            logger.error(f"Ошибка мониторинга сервера {server['host']}: {e}")

        await asyncio.sleep(5)  # Ждем 5 секунд перед следующим циклом


# Инициализация Flask приложения
app = Flask(__name__)

# Устанавливаем Flask в продакшн-режим
app.config['ENV'] = 'production'  # Устанавливаем в продакшн режим
app.config['DEBUG'] = False  # Отключаем отладочный режим

# Отключение логирования сообщений от Flask (werkzeug)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Устанавливаем уровень логирования на ERROR, чтобы исключить лишний вывод

# Словарь для хранения данных о серверах
data_store = {}


# Функция загрузки информации о серверах из файла
def load_servers(filename='servers.json'):
    try:
        with open(filename, 'r') as file:
            servers = json.load(file)
        logger.debug(f"Загруженные сервера: {servers}")
        return servers
    except Exception as e:
        logging.error(f"Ошибка при загрузке серверов из файла: {e}")
        return []


# Запуск мониторинга серверов с использованием asyncio в отдельном потоке
def run_monitoring():
    servers = load_servers()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [loop.create_task(monitor_server(server, data_store)) for server in servers]
    loop.run_until_complete(asyncio.gather(*tasks))


# Главная страница
@app.route("/")
def index():
    try:
        # Рендерим HTML из файла index.html в папке templates
        return render_template("index.html", data_store=data_store)
    except Exception as e:
        logger.error(f"Ошибка рендеринга страницы: {e}")
        return f"Ошибка рендеринга страницы: {e}"


# Запуск Flask приложения в отдельном потоке
def run_flask():
    host = "0.0.0.0"
    port = 3500
    print(f"Cервис запущен и доступен по адресу: http://{host}:{port}")
    try:
        app.run(host=host, port=port)
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")


# Запуск Flask и мониторинга серверов
if __name__ == "__main__":
    # Запуск Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Запуск мониторинга серверов в отдельном потоке
    monitoring_thread = threading.Thread(target=run_monitoring)
    monitoring_thread.daemon = True
    monitoring_thread.start()

    # Блокируем основной поток, чтобы программа не завершилась
    flask_thread.join()
    monitoring_thread.join()
