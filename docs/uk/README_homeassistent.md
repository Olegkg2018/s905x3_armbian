# Встановлення Home Assistant Core на Armbian (S905X3)

Покрокова інструкція зі встановлення **Home Assistant Core** через `armbian-software` на TV-приставці з Amlogic S905X3 під управлінням Armbian.

## 📋 Передумови

- ✅ TV-приставка з Amlogic S905X3 (4 GB RAM / 32–64 GB eMMC)
- ✅ Armbian встановлено на eMMC (інструкція: `README_install_armbian.md`)
- ✅ Підключення до інтернету (Ethernet або Wi-Fi)
- ✅ SSH-доступ до пристрою

---

## 🚀 Покрокова установка

### Крок 1: Оновлення системних пакетів

Підключіться до приставки по SSH та виконайте:

```bash
sudo armbian-software -u
```

Ця команда оновить список доступних пакетів в утиліті `armbian-software`.

### Крок 2: Запуск інтерфейсу armbian-software

```bash
sudo armbian-software
```

Відкриється текстовий інтерфейс із списком доступного програмного забезпечення.

### Крок 3: Встановлення Docker (ID 101)

У меню виберіть:

```
101 → Docker
```

- Натисніть `Space` для вибору
- Натисніть `Enter` для підтвердження
- Дочекайтеся завершення встановлення Docker

### Крок 4: Встановлення Portainer (ID 102)

Далі встановіть **Portainer** — зручний веб-інтерфейс для управління Docker-контейнерами:

```
102 → Portainer
```

- Натисніть `Space` → `Enter`
- Після встановлення Portainer буде доступний за адресою:

```
http://<IP-адреса-приставки>:9000
```

### Крок 5: Встановлення Home Assistant (ID 108)

Тепер встановіть сам **Home Assistant Core**:

```
108 → Home Assistant
```

- Натисніть `Space` → `Enter`
- Дочекайтеся завершення встановлення
- Після завершення Home Assistant буде доступний за адресою:

```
http://<IP-адреса-приставки>:8123
```

### Крок 6: Перше налаштування Home Assistant

1. Відкрийте браузер та перейдіть до `http://<IP>:8123`
2. Створіть обліковий запис адміністратора
3. Налаштуйте місцезнаходження та часовий пояс
4. Виберіть інтеграції для додавання (можна пропустити)

---

## 📦 Встановлення HACS (Home Assistant Community Store)

**HACS** — магазин додаткових інтеграцій та тем для Home Assistant.

### Спосіб 1: Через термінал

Виконайте команду:

```bash
wget -O - https://get.hacs.xyz | bash -
```

### Спосіб 2: Через інтерфейс Home Assistant

1. Увійдіть у Home Assistant
2. Перейдіть до **Settings** → **Add-ons** → **Add-on Store**
3. У правому верхньому куті натисніть три крапки → **Repositories**
4. Додайте:

```
https://github.com/hacs/integration
```

5. Оновіть список та встановіть HACS
6. Перезапустіть Home Assistant

### Активація HACS

1. Перейдіть до **Settings** → **Devices & Services**
2. Натисніть **+ Add Integration** → знайдіть **HACS**
3. Пройдіть авторизацію через GitHub
4. Після активації HACS з'явиться в бічному меню

---

## 🔧 Управління сервісом Home Assistant

### Перевірка статусу

```bash
sudo systemctl status homeassistant
```

### Перезапуск

```bash
sudo systemctl restart homeassistant
```

### Зупинка

```bash
sudo systemctl stop homeassistant
```

### Запуск

```bash
sudo systemctl start homeassistant
```

### Перегляд логів

```bash
sudo journalctl -u homeassistant -f
```

---

## 🛠 Налаштування автозапуску

Home Assistant автоматично налаштовується на запуск при завантаженні системи. Перевірити це можна командою:

```bash
sudo systemctl is-enabled homeassistant
```

Якщо сервіс не увімкнено, активуйте його:

```bash
sudo systemctl enable homeassistant
```

---

## 🌐 Доступ ззовні (опціонально)

Для безпечного віддаленого доступу до Home Assistant рекомендується використовувати:

- **Cloudflare Tunnel** — інструкція: `docs/uk/README_cloudflare_tunnel.md`
- **Tailscale / WireGuard VPN**
- **DuckDNS + Let's Encrypt**

---

## ❓ Усунення проблем

Якщо Home Assistant не запускається:

```bash
sudo journalctl -u homeassistant -n 50
```

Перевірте наявність помилок у логах.

### Типові проблеми:

**Помилка: "Cannot connect to Home Assistant"**

- Перевірте статус сервісу: `systemctl status homeassistant`
- Перевірте, чи зайнятий порт 8123: `sudo netstat -tulpn | grep 8123`

**Home Assistant повільно працює**

- Перевірте використання пам'яті: `free -h`
- Перевірте навантаження на CPU: `htop`

---

## 📚 Корисні посилання

- [Офіційна документація Home Assistant](https://www.home-assistant.io/docs/)
- [Форум Home Assistant](https://community.home-assistant.io/)
- [HACS Documentation](https://hacs.xyz/docs/configuration/start)
- [Інтеграції та компоненти](https://www.home-assistant.io/integrations/)

---

## 🎯 Наступні кроки

Після встановлення Home Assistant рекомендуємо:

1. 📱 Встановити мобільний додаток Home Assistant
2. 🔐 Налаштувати Cloudflare Tunnel для віддаленого доступу → `docs/uk/README_cloudflare_tunnel.md`
3. 🏠 Додати перші інтеграції (освітлення, датчики, клімат)
4. 📊 Налаштувати ESPHome для ESP32 пристроїв → `docs/uk/README_esphome.md`
5. ⚡ Під'єднати інвертор/BMS через ESPHome → `docs/uk/README_esp32.md`

---

**Останнє оновлення:** 2026-05-07  
**Автор:** Olegkg2018
