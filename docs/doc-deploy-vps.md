# Инструкция по деплою Hunter на GCP VPS (Free Tier)

### Шаг 1: Подготовка сервера
После того как вы создали VM и зашли в нее через SSH (кнопка SSH в консоли Google), выполните команды:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

### Шаг 2: Копирование кода
Клонируйте ваш репозиторий или создайте папку и перенесите файлы через SCP/SFTP.
```bash
mkdir ~/hunter && cd ~/hunter
# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 3: Настройка .env
Создайте файл `.env` на сервере и вставьте туда ваши ключи:
```bash
nano .env
# Вставьте содержимое вашего .env, нажмите Ctrl+O, Enter, Ctrl+X
```

### Шаг 4: Первая авторизация (ВАЖНО)
Так как Telethon (Telegram) попросит код из СМС, первый раз запустите бота вручную:
```bash
python3 main.py
```
Введите номер телефона и код. Как только увидите лог `✅ Telegram Listener is connected`, нажмите `Ctrl+C`. Теперь файл `hunter_session.session` создан, и бот сможет работать в фоне.

### Шаг 5: Настройка автозапуска (Systemd)
Чтобы бот работал 24/7, создадим сервис:
```bash
sudo nano /etc/systemd/system/hunter.service
```
Вставьте туда (заменив `USER` на ваше имя пользователя в GCP):
```ini
[Unit]
Description=Hunter AI Job Sniper
After=network.target

[Service]
User=USER
WorkingDirectory=/home/USER/hunter
ExecStart=/home/USER/hunter/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Шаг 6: Запуск
```bash
sudo systemctl daemon-reload
sudo systemctl enable hunter
sudo systemctl start hunter
```

Теперь можно проверить статус: `sudo systemctl status hunter`. Бот будет работать, даже если вы закроете терминал и выключите ноутбук.
