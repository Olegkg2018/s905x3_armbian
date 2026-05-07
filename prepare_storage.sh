#!/bin/bash
# prepare_storage.sh - Настройка внешнего диска для S905X3 Armbian
# Монтирование в /mnt/data и перенос тяжёлых каталогов
#
# Использование: sudo bash prepare_storage.sh

set -euo pipefail

# --- Проверка прав root ---
if [[ $EUID -ne 0 ]]; then
  echo "Ошибка: скрипт должен запускаться от root (sudo bash prepare_storage.sh)"
  exit 1
fi

MOUNT_POINT="/mnt/data"
TARGET_DISK=""

echo "=== Настройка внешнего диска для S905X3 Armbian ==="
echo ""

# --- Показываем список дисков ---
echo "Доступные блочные устройства:"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE
echo ""

# --- Ввод устройства ---
read -rp "Введите имя устройства для форматирования (например, sda или sdb1): " TARGET_DISK

if [[ -z "$TARGET_DISK" ]]; then
  echo "Ошибка: устройство не указано. Выход."
  exit 1
fi

DEV_PATH="/dev/${TARGET_DISK}"

if [[ ! -b "$DEV_PATH" ]]; then
  echo "Ошибка: устройство $DEV_PATH не найдено!"
  exit 1
fi

# --- Защита от случайного форматирования системного диска ---
ROOT_DEV=$(findmnt -n -o SOURCE /)
if [[ "$DEV_PATH" == "$ROOT_DEV" || "$ROOT_DEV" == ${DEV_PATH}* ]]; then
  echo "Ошибка: $DEV_PATH является системным диском. Операция запрещена!"
  exit 1
fi

# --- Предупреждение и подтверждение ---
echo ""
echo "ВНИМАНИЕ: Все данные на $DEV_PATH будут уничтожены!"
read -rp "Вы уверены? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Операция отменена."
  exit 0
fi

# --- Форматирование ---
echo "Форматирование $DEV_PATH в ext4..."
mkfs.ext4 -F -L armbian-data "$DEV_PATH"

# --- Создание точки монтирования ---
echo "Создание точки монтирования $MOUNT_POINT..."
mkdir -p "$MOUNT_POINT"

# --- Получение UUID и добавление в /etc/fstab ---
UUID=$(blkid -s UUID -o value "$DEV_PATH")
if [[ -z "$UUID" ]]; then
  echo "Ошибка: не удалось получить UUID устройства."
  exit 1
fi

echo "Добавление в /etc/fstab (UUID=$UUID)..."
# Удаляем старую запись для этой точки монтирования, если есть
if grep -q "$MOUNT_POINT" /etc/fstab; then
  sed -i "\|$MOUNT_POINT|d" /etc/fstab
fi
echo "UUID=$UUID $MOUNT_POINT ext4 defaults,noatime 0 2" >> /etc/fstab

# --- Монтирование ---
echo "Монтирование..."
mount -a

if ! mountpoint -q "$MOUNT_POINT"; then
  echo "Ошибка монтирования! Проверьте /etc/fstab и dmesg."
  exit 1
fi

echo "Диск успешно смонтирован в $MOUNT_POINT"

# --- Остановка сервисов перед переносом данных ---
echo ""
echo "Остановка сервисов..."
systemctl stop docker 2>/dev/null || true
systemctl stop home-assistant@homeassistant 2>/dev/null || true

# --- Перенос каталогов ---
# Переносим только те каталоги, которые существуют и не являются симлинками
DIRS_TO_MOVE=("homeassistant" "srv" "backup")

for dir in "${DIRS_TO_MOVE[@]}"; do
  SRC="/$dir"
  DST="$MOUNT_POINT/$dir"

  if [[ -d "$SRC" && ! -L "$SRC" ]]; then
    echo "Перенос $SRC -> $DST"
    mkdir -p "$DST"
    rsync -avxHAX "$SRC/" "$DST/"
    mv "$SRC" "${SRC}.bak"
    ln -s "$DST" "$SRC"
    echo "OK: $SRC перенесён, создана символическая ссылка."
  fi
done

# --- Перенос /var/lib/docker (особый случай) ---
if [[ -d "/var/lib/docker" && ! -L "/var/lib/docker" ]]; then
  echo "Перенос /var/lib/docker..."
  mkdir -p "$MOUNT_POINT/docker"
  rsync -avxHAX /var/lib/docker/ "$MOUNT_POINT/docker/"
  mv /var/lib/docker /var/lib/docker.bak
  ln -s "$MOUNT_POINT/docker" /var/lib/docker
  echo "OK: /var/lib/docker перенесён."
fi

# --- Перезапуск сервисов ---
echo ""
echo "Перезапуск сервисов..."
systemctl daemon-reload
systemctl start docker 2>/dev/null || true
systemctl start home-assistant@homeassistant 2>/dev/null || true

echo ""
echo "=== Готово! Внешний диск настроен и используется ==="
df -h | grep "$MOUNT_POINT"
