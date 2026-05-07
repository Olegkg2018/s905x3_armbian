# 🔧 Диагностика и решение проблем (S905X3)

Проблемы при установке Armbian на S905X3 чаще всего связаны с различиями
в ревизиях плат и версиях u-boot — даже если корпус и название модели одинаковы.

## 1. Идентификация железа

Перед установкой выясните точную модель платы:

```bash
# Модель устройства из Device Tree
cat /proc/device-tree/model

# Информация о сетевом чипе (помогает подобрать DTB)
dmesg | grep -i eth

# Список USB-устройств
lsusb

# Полная информация о CPU и памяти
cat /proc/cpuinfo | grep -E "Hardware|Revision"
free -h
```

## 2. Устройство не загружается с USB

- Убедитесь, что флешка вставлена в **синий порт USB 3.0**.
- При подаче питания удерживайте кнопку **Reset** (спичкой в отверстие) ~5–10 сек.
- Проверьте, что в образе корректно выбран DTB-файл для вашей ревизии платы.
  Рекомендуемые DTB для S905X3:
  - `meson-sm1-x96-max-plus.dtb` (большинство X96 Max+ 4/64)
  - `meson-sm1-sei610.dtb` (ревизии с другим WiFi-чипом)

## 3. Wi-Fi не работает после установки

```bash
# Проверить загруженные модули
lsmod | grep -i wifi

# Посмотреть доступные интерфейсы
ip link show

# Принудительно загрузить модуль (пример для rtl8822cs)
modprobe 88x2cs
```

## 4. Home Assistant не запускается

```bash
# Статус сервиса
systemctl status home-assistant@homeassistant

# Последние строки лога
journalctl -u home-assistant@homeassistant -n 50 --no-pager

# Проверка виртуального окружения
source /srv/homeassistant/bin/activate
hass --version
```

## 5. Высокая нагрузка на eMMC (износ)

Перенесите папки с активной записью на внешний USB-диск:

```bash
# Использование скрипта из репозитория
chmod +x prepare_storage.sh
sudo ./prepare_storage.sh
```

## 6. Проверка состояния системы

```bash
# Температура CPU
cat /sys/class/thermal/thermal_zone*/temp

# Использование RAM и диска
free -h
df -h

# Нагрузка процессора
top -bn1 | head -20
```
