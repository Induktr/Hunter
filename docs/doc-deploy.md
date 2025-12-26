# Руководство по Деплою

### 1. Подготовка Сервера (Linux Ubuntu/Debian)

Мы используем `systemd` для обеспечения работы 24/7.

1.  Скопировать проект в `/opt/hunter`.
2.  Настроить права доступа.

### 2. Настройка Сервиса

Создать файл `/etc/systemd/system/hunter.service`:

```ini
[Unit]
Description=Hunter AI Job Sniper
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hunter
ExecStart=/opt/hunter/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

3. Команды Управления
Запустить: sudo systemctl start hunter
Включить автозапуск: sudo systemctl enable hunter
Смотреть логи: journalctl -u hunter -f
Остановить: sudo systemctl stop hunter
4. Логирование (Контроль Охотника)
Все действия записываются в logs/hunter.log и дублируются в logs/history.md в формате:
[FILTERED]: Отсеяно по стоп-словам.
[LOW SCORE]: ИИ оценил низко (3/10).
[SENT]: Уведомление отправлено.