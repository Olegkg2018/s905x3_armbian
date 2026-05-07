#!/bin/bash
# install_to_emmc.sh - Установка Armbian на eMMC для S905X3
# Учитывает нюансы загрузки и сохраняет рабочие DTB
#
# Использование: sudo bash install_to_emmc.sh

set -euo pipefail

# --- Проверка прав root ---
if [[ $EUID -ne 0 ]]; then
  echo "Ошибка: скрипт должен запускаться от root (sudo bash install_to_emmc.sh)"
  exit 1
fi

echo "=== Установка Armbian на eMMC (S905X3) ==="
echo "Текущая версия ядра: $(uname -r)"
echo ""

# --- Проверка: не загружены ли мы уже с eMMC ---
ROOT_DEV=$(findmnt -n -o SOURCE /)
if [[ "$ROOT_DEV" == /dev/mmcblk2* ]]; then
  echo "Вы уже загружены с eMMC. Установка не требуется."
  exit 0
fi

# --- Проверка наличия armbian-install ---
if ! command -v armbian-install &>/dev/null; then
  echo "Ошибка: утилита armbian-install не найдена."
  echo "Установите пакет: apt install armbian-zconfig"
  exit 1
fi

# --- Предупреждение ---
echo "ВНИМАНИЕ: Этот процесс удалит Android и все данные на внутренней памяти (eMMC)!"
read -rp "Продолжить? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Операция отменена."
  exit 0
fi

# --- Резервное копирование DTB и настроек загрузки ---
BOOT_DIR="/boot"
BACKUP_DIR="/root/emmc_backup_$(date +%F_%H%M)"

echo "Сохранение конфигурации загрузки в $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
cp -r "$BOOT_DIR" "$BACKUP_DIR/"
echo "Бэкап сохранён: $BACKUP_DIR"
echo ""

# --- Запуск armbian-install ---
# armbian-install интерактивен: позволяет выбрать целевой диск и файловую систему
echo "Запуск armbian-install..."
armbian-install

echo ""
echo "=== Установка завершена! ==="
echo "Извлеките USB-накопитель и перезагрузите устройство."
echo ""

read -rp "Перезагрузить сейчас? (yes/no): " REBOOT
if [[ "$REBOOT" == "yes" ]]; then
  echo "Перезагрузка..."
  reboot
fi
