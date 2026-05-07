# 🔧 Діагностика та вирішення проблем (S905X3)

Проблеми при встановленні Armbian на S905X3 найчастіше пов'язані з відмінностями в ревізіях плат та версіях u-boot — навіть якщо корпус і назва моделі однакові.

---

## 1️⃣ Ідентифікація обладнання

Перед встановленням з'ясуйте точну модель плати:

```bash
# Модель пристрою з Device Tree
cat /proc/device-tree/model

# Інформація про мережевий чіп (допомагає підібрати DTB)
dmesg | grep -i eth

# Список USB-пристроїв
lsusb

# Повна інформація про CPU і пам'ять
cat /proc/cpuinfo | grep -E "Hardware|Revision"
free -h
```

---

## 2️⃣ Пристрій не завантажується з USB

### Перевірте:

- ✅ Флешка вставлена в **синій порт USB 3.0**
- ✅ При подачі живлення утримуйте кнопку **Reset** (сірником у отвір) **~5–10 сек**
- ✅ У образі коректно обрано **DTB-файл** для вашої ревізії плати

### Рекомендовані DTB для S905X3:

- `meson-sm1-x96-max-plus.dtb` — більшість X96 Max+ 4/64
- `meson-sm1-sei610.dtb` — ревізії з іншим Wi-Fi-чіпом

---

## 3️⃣ Wi-Fi не працює після встановлення

### Перевірка модулів та інтерфейсів:

```bash
# Перевірка завантажених модулів Wi-Fi
lsmod | grep -i wifi

# Перевірка мережевих інтерфейсів
ip link show

# Завантаження драйвера (RTL88x2cs чіп)
modprobe 88x2cs
```

---

## 4️⃣ Home Assistant не запускається

### Перевірка статусу сервісу:

```bash
# Статус сервісу
systemctl status home-assistant@homeassistant

# Перегляд логів
journalctl -u home-assistant@homeassistant -n 50 --no-pager

# Перевірка версії у віртуальному середовищі
source /srv/homeassistant/bin/activate
hass --version
```

---

## 5️⃣ Високе навантаження на eMMC (знос)

Якщо Home Assistant активно записує дані на eMMC, рекомендується перенести базу даних на зовнішній USB-диск:

```bash
chmod +x prepare_storage.sh
sudo ./prepare_storage.sh
```

---

## 6️⃣ Перевірка стану системи

### Температура CPU:

```bash
cat /sys/class/thermal/thermal_zone*/temp
```

### Використання пам'яті:

```bash
free -h
```

### Використання диска:

```bash
df -h
```

### Процеси з найбільшим навантаженням:

```bash
top -bn1 | head -20
```

---

## 📚 Корисні посилання

- [Форум Armbian](https://forum.armbian.com/)
- [Ophub S905X3 Releases](https://github.com/ophub/amlogic-s9xxx-armbian/releases)
- [Офіційна документація Armbian](https://docs.armbian.com/)

---

**Останнє оновлення:** 2026-05-07
