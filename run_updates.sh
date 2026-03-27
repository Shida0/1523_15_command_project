#!/bin/bash

# Пути (измените под свою систему)
PROJECT_DIR="/home/dinvosh/projects/python/school_project"          # полный путь к проекту
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"      # полный путь к python в виртуальном окружении
SCRIPT="$PROJECT_DIR/run_update.py"              # путь к run_update.py
LOG_FILE="/var/log/asteroid_update.log"          # лог-файл

# Команда для cron
CRON_CMD="0 0 * * * cd $PROJECT_DIR && $VENV_PYTHON $SCRIPT >> $LOG_FILE 2>&1"

# Проверяем, существует ли уже такое задание в crontab
if crontab -l 2>/dev/null | grep -F "$CRON_CMD" > /dev/null; then
    echo "Задание уже есть в crontab. Ничего не делаю."
else
    # Добавляем новое задание
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Задание добавлено в crontab."
fi