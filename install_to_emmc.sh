#!/bin/bash
# install_to_emmc.sh - Установка Armbian на eMMC для S905X3
# С учетом нюансов загрузки и сохранения рабочих DTB

set -e

echo "🛡 Скрипт установки Armbian на eMMC (S905X3)"
echo "Текущая версия ядра: $(uname -r)"

# Проверка, что мы не уже на eMMC
ROOT_DEV=$(findmnt -n -o SOURCE /)
if [[ "$ROOT_DEV" == /dev/mmcblk2* ]]; then
    echo "⚠️  Вы уже загружены с eMMC! Установка не требуется."
    exit 0
fi

echo "⚠️  ВНИМАНИЕ: Этот процесс удалит Android и все данные на внутренней памяти (eMMC)!"
read -p "Продолжить? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    exit 0
fi

# Резервное копирование текущих настроек загрузки
echo "💾 Сохранение текущей конфигурации загрузки..."
BOOT_DIR="/boot"
BACKUP_DIR="/root/emmc_backup_$(date +%F_%H%M)"
mkdir -p "$BACKUP_DIR"
cp -r "$BOOT_DIR" "$BACKUP_DIR/"
echo "Бэкап сохранен в $BACKUP_DIR"

# Запуск стандартной утилиты armbian-install с флагами
# -y: автоматическое согласие
# -b: выбор платы (если потребуется)
if command -v armbian-install &> /dev/null; then
    echo "🚀 Запуск armbian-install..."
    # Используем режим 'yes' для автоматического выбора параметров, если возможно
    # В некоторых версиях нужно выбрать номер диска вручную, поэтому оставляем интерактив для выбора диска
    armbian-install
else
    echo "❌ Утилита armbian-install не найдена. Установите пакет armbian-zconfig или armbian-firmware."
    exit 1
fi

echo "✅ Установка завершена!"
echo "🔄 Пожалуйста, извлеките USB-накопитель и перезагрузите систему:"
read -p "Перезагрузить сейчас? (yes/no): " REBOOT
if [ "$REBOOT" == "yes" ]; then
    reboot
fi
