## 2. Скрипт `scripts/prepare_storage.sh`

Этот скрипт готовит внешний диск, форматирует его и переносит данные.

```bash
#!/bin/bash
# prepare_storage.sh - Настройка внешнего диска для S905X3 Armbian
# Монтирование в /mnt/data и перенос тяжелых каталогов

set -e

MOUNT_POINT="/mnt/data"
TARGET_DISK=""

echo "🔍 Поиск подключенных дисков..."
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE

echo ""
read -p "Введите имя устройства для форматирования (например, sda1 или sdb1): " TARGET_DISK

if [ -z "$TARGET_DISK" ]; then
    echo "❌ Устройство не указано. Выход."
    exit 1
fi

DEV_PATH="/dev/${TARGET_DISK}"

if [ ! -b "$DEV_PATH" ]; then
    echo "❌ Устройство $DEV_PATH не найдено!"
    exit 1
fi

echo "⚠️  ВНИМАНИЕ: Все данные на $DEV_PATH будут уничтожены!"
read -p "Вы уверены? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Операция отменена."
    exit 0
fi

echo "🛠 Форматирование $DEV_PATH в ext4..."
mkfs.ext4 -F "$DEV_PATH"

echo "📁 Создание точки монтирования $MOUNT_POINT..."
mkdir -p "$MOUNT_POINT"

echo "🔗 Добавление в /etc/fstab..."
UUID=$(blkid -s UUID -o value "$DEV_PATH")
if grep -q "$MOUNT_POINT" /etc/fstab; then
    sed -i "\|$MOUNT_POINT|d" /etc/fstab
fi
echo "UUID=$UUID $MOUNT_POINT ext4 defaults,noatime 0 2" >> /etc/fstab

echo "⏳ Монтирование..."
mount -a

if ! mountpoint -q "$MOUNT_POINT"; then
    echo "❌ Ошибка монтирования! Проверьте /etc/fstab."
    exit 1
fi

echo "📦 Перенос данных..."
# Останавливаем сервисы, которые могут писать в эти папки
systemctl stop docker || true
systemctl stop home-assistant@homeassistant || true

DIRS_TO_MOVE=("docker" "homeassistant" "srv" "backup")

for dir in "${DIRS_TO_MOVE[@]}"; do
    SRC="/$dir"
    DST="$MOUNT_POINT/$dir"
    
    if [ -d "$SRC" ] && [ ! -L "$SRC" ]; then
        echo "Перенос /$dir -> $DST"
        rsync -avxHAX "$SRC/" "$DST/"
        mv "$SRC" "${SRC}.bak"
        ln -s "$DST" "$SRC"
        echo "✅ /$dir перенесен и заменен ссылкой."
    fi
done

# Особый случай для /var/lib/docker если он есть
if [ -d "/var/lib/docker" ] && [ ! -L "/var/lib/docker" ]; then
    mkdir -p "$MOUNT_POINT/docker"
    rsync -avxHAX /var/lib/docker/ "$MOUNT_POINT/docker/"
    mv /var/lib/docker /var/lib/docker.bak
    ln -s "$MOUNT_POINT/docker" /var/lib/docker
    echo "✅ /var/lib/docker перенесен."
fi

echo "🚀 Перезапуск сервисов..."
systemctl daemon-reload
systemctl start docker || true
systemctl start home-assistant@homeassistant || true

echo "✅ Готово! Внешний диск настроен и используется."
df -h | grep "$MOUNT_POINT"
