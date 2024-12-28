StatusDashboard - Мониторинг серверов с веб-интерфейсом

StatusDashboard — это простой и удобный инструмент для мониторинга состояния серверов с помощью веб-интерфейса. Проект позволяет отслеживать важные параметры серверов, такие как время работы (uptime), загрузка процессора, использование памяти и температура. Все данные собираются через SSH и отображаются на чистом и интуитивно понятном дашборде.

Особенности проекта:

Мониторинг нескольких серверов одновременно.
Отображение актуальной информации о нагрузке на процессор и использовании памяти.
Визуализация времени работы (uptime) сервера и температуры.
Простота в настройке и использовании.
Темная и светлая темы интерфейса для удобства работы.
Логирование событий и ошибок для дальнейшего анализа.
Этот проект идеально подходит для системных администраторов и тех, кто хочет следить за состоянием серверов в реальном времени.

Используемые технологии:

Python (paramiko для подключения через SSH).
Flask для создания веб-интерфейса.
JavaScript для динамической смены тем и обновления информации.
Стандарты CSS для стилизации интерфейса.
Проект может быть легко расширен, добавляя новые метрики или улучшая интерфейс.﻿# StatusServer

![image](https://github.com/user-attachments/assets/b72e750d-ba7c-40ef-b5d2-45678704e4e5)
![image](https://github.com/user-attachments/assets/0e1dd5f5-3c1d-4cec-9124-2427940627dc)


## Установка

### 1. Установите Python 3
```bash
sudo apt install python3 python3-pip
```

### 2. Создайте виртуальное окружение (опционально)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установите зависимости
```bash
pip install -r requirements.txt
```

### 4. Настройте файл конфигурации серверов
Создайте файл `servers.json` в корневой директории проекта со следующим содержимым:
```json
[
    {
        "host": "192.168.1.1",
        "port": 22,
        "username": "user",
        "password": "password"
    }
]
```
Добавьте информацию о ваших серверах.

### 5. Запустите скрипт
```bash
python3 main.py
```

## Автоматизация запуска (опционально)
Чтобы скрипт запускался автоматически при старте системы, создайте systemd-сервис:

Создайте файл `/etc/systemd/system/status_dashboard.service` со следующим содержимым:
```ini
[Unit]
Description=StatusDashboard Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/main.py
WorkingDirectory=/path/to/project
Restart=always
User=your_user

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable status_dashboard.service
sudo systemctl start status_dashboard.service
```
Теперь ваш скрипт будет автоматически запускаться при загрузке системы.

## Решение проблем

### Если не отображается температура
1. Убедитесь, что `sensors` установлен. На сервере выполните:
   ```bash
   sensors
   ```

2. Если команда не найдена, установите `lm-sensors`:
   ```bash
   sudo apt install lm-sensors -y  # Для Debian/Ubuntu
   sudo yum install lm_sensors -y  # Для CentOS/RHEL
   ```

3. Запустите настройку `sensors`. После установки выполните:
   ```bash
   sudo sensors-detect
   ```
   Следуйте инструкциям для обнаружения поддерживаемых датчиков.


