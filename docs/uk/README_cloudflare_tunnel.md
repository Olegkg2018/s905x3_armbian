# Cloudflare Tunnel для віддаленого доступу до Home Assistant

**Cloudflare Tunnel** (раніше Argo Tunnel) — безпечний спосіб надати доступ до вашого Home Assistant з будь-якої точки світу без відкриття портів на роутері і без статичної IP-адреси.

## 🎯 Переваги

- ✅ Без відкриття портів на роутері
- ✅ Без статичної IP-адреси
- ✅ Автоматичний HTTPS (SSL-сертифікат від Cloudflare)
- ✅ Захист від DDoS
- ✅ Безкоштовно для домашнього використання
- ✅ Доступ через власний домен або піддомен

---

## 📋 Передумови

1. Home Assistant вже встановлено і працює на `http://localhost:8123`
2. Обліковий запис на [Cloudflare](https://dash.cloudflare.com/) (безкоштовний)
3. Власний домен, підключений до Cloudflare (опціонально, але рекомендовано)

---

## 🚀 Встановлення cloudflared

### Крок 1: Завантаження та встановлення

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

### Крок 2: Перевірка встановлення

```bash
cloudflared --version
```

---

## 🔐 Налаштування тунелю

### Крок 3: Авторизація в Cloudflare

```bash
cloudflared tunnel login
```

Відкриється браузер для авторизації. Виберіть свій домен (якщо є) або створіть новий.

### Крок 4: Створення тунелю

```bash
cloudflared tunnel create homeassistant
```

Запишіть **Tunnel ID**, який з'явиться в консолі. Він знадобиться далі.

### Крок 5: Налаштування конфігурації

Створіть файл конфігурації:

```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

Додайте наступний вміст (замініть `YOUR_TUNNEL_ID` та `yourdomain.com`):

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /root/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: ha.yourdomain.com
    service: http://localhost:8123
  - service: http_status:404
```

**Примітка:** Якщо у вас немає домену, можна використовувати автоматичний піддомен Cloudflare (буде надано після запуску).

---

## 🌐 Налаштування DNS

### Крок 6: Створення DNS-запису

Виконайте команду:

```bash
cloudflared tunnel route dns homeassistant ha.yourdomain.com
```

Це автоматично створить CNAME-запис у ваших налаштуваннях Cloudflare DNS.

---

## ⚙️ Запуск як системний сервіс

### Крок 7: Створення systemd сервісу

```bash
sudo cloudflared service install
```

### Крок 8: Запуск і увімкнення автозапуску

```bash
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

### Крок 9: Перевірка статусу

```bash
sudo systemctl status cloudflared
```

---

## 🏠 Налаштування Home Assistant

### Крок 10: Додавання довіреного домену

Відредагуйте `configuration.yaml`:

```bash
sudo nano /home/homeassistant/.homeassistant/configuration.yaml
```

Додайте:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - ::1
  external_url: https://ha.yourdomain.com
  internal_url: http://localhost:8123
```

Перезапустіть Home Assistant:

```bash
sudo systemctl restart homeassistant
```

---

## 📱 Доступ з мобільного

Тепер ви можете відкрити:

```
https://ha.yourdomain.com
```

з будь-якого місця в світі через мобільний додаток Home Assistant або браузер.

### Налаштування мобільного додатку

1. Відкрийте додаток Home Assistant
2. Додайте новий сервер
3. Введіть: `https://ha.yourdomain.com`
4. Увійдіть за допомогою облікового запису

---

## 🔒 Підвищення безпеки

### Налаштування Cloudflare Access (опціонально)

Для додаткового захисту можна налаштувати Cloudflare Access:

1. Перейдіть до [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. Access → Applications → Add an application
3. Виберіть Self-hosted
4. Вкажіть `ha.yourdomain.com`
5. Налаштуйте правила доступу (email, PIN-код, тощо)

---

## 🛠 Управління тунелем

### Перегляд списку тунелів

```bash
cloudflared tunnel list
```

### Перезапуск сервісу

```bash
sudo systemctl restart cloudflared
```

### Перегляд логів

```bash
sudo journalctl -u cloudflared -f
```

### Видалення тунелю

```bash
cloudflared tunnel delete homeassistant
```

---

## ❓ Усунення проблем

### Тунель не з'єднується

```bash
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -n 50
```

Перевірте, чи правильно вказано Tunnel ID у `/etc/cloudflared/config.yml`.

### Home Assistant не приймає зовнішні з'єднання

Переконайтеся, що в `configuration.yaml` додано:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
```

### DNS-запис не створюється автоматично

Вручну додайте CNAME-запис у Cloudflare DNS:

- Type: `CNAME`
- Name: `ha` (або ваш піддомен)
- Target: `YOUR_TUNNEL_ID.cfargotunnel.com`
- Proxy status: Proxied (помаранчева хмарка)

---

## 📚 Корисні посилання

- [Офіційна документація Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
- [Інтеграція Home Assistant з Cloudflare](https://www.home-assistant.io/integrations/http/)

---

**Останнє оновлення:** 2026-05-07  
**Автор:** Olegkg2018
