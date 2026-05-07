# 🌐 Удалённый доступ к Home Assistant через Cloudflare Tunnel

> **Безопасное подключение без проброса портов и статического IP**

Это руководство показывает, как настроить безопасный удалённый доступ к Home Assistant на S905X3 с помощью **Cloudflare Tunnel** (ранее Argo Tunnel). Подходит для доступа с мобильного телефона из любой точки мира.

---

## ✅ Преимущества Cloudflare Tunnel

- ✅ **Не требуется проброс портов** на роутере
- ✅ **Не нужен статический IP-адрес**
- ✅ **Бесплатно** (Free-план Cloudflare)
- ✅ **Автоматический SSL/TLS-сертификат**
- ✅ **Защита от DDoS**
- ✅ **Быстрая настройка** (15-20 минут)

---

## 📋 Что потребуется

- Home Assistant, установленный в Docker (см. [README_homeassistent.md](README_homeassistent.md))
- Бесплатный аккаунт Cloudflare (регистрация на [cloudflare.com](https://dash.cloudflare.com/sign-up))
- Собственный домен (можно зарегистрировать бесплатно на [Freenom](https://www.freenom.com) или купить на [Namecheap](https://www.namecheap.com))
- Доступ по SSH к приставке S905X3

---

## 🚀 Пошаговая настройка

### Шаг 1: Регистрация домена в Cloudflare

#### 1.1. Создайте аккаунт Cloudflare

1. Перейдите на [https://dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
2. Зарегистрируйтесь или войдите

#### 1.2. Добавьте ваш домен

1. Нажмите **Add a Site**
2. Введите ваш домен (например, `mydomain.tk`)
3. Выберите план **Free** и нажмите **Continue**

#### 1.3. Настройте DNS-сервера

Cloudflare покажет вам свои DNS-сервера (например, `alina.ns.cloudflare.com` и `brad.ns.cloudflare.com`).

1. Перейдите на сайт вашего регистратора доменов (Freenom, Namecheap и т.д.)
2. Замените DNS-сервера на указанные Cloudflare
3. Дождитесь пропагации DNS (обычно 5-30 минут, максимум 24 часа)

---

### Шаг 2: Создание Cloudflare Tunnel

#### 2.1. Перейдите в Zero Trust Dashboard

1. В панели Cloudflare нажмите на ваш домен
2. В левом меню выберите **Zero Trust** (или перейдите на [https://one.dash.cloudflare.com/](https://one.dash.cloudflare.com/))
3. Если это первый запуск, выберите **Free план**

#### 2.2. Создайте Tunnel

1. Перейдите в **Networks** → **Tunnels**
2. Нажмите **Create a tunnel**
3. Выберите **Cloudflared**
4. Введите имя туннеля (например, `homeassistant-tunnel`)
5. Нажмите **Save tunnel**

#### 2.3. Скопируйте токен туннеля

Cloudflare покажет вам команду для установки `cloudflared`. Выберите вкладку **Docker** и скопируйте **токен** (длинная строка после `--token`).

Пример:

```
eyJhIjoiYWJjMTIzLi4uXyIsInQiOiJkZWY0NTYuLi4ifQ==
```

Не закрывайте эту страницу — она понадобится на следующем шаге.

---

### Шаг 3: Установка `cloudflared` в Docker

Подключитесь к приставке по SSH:

```bash
ssh root@<IP-адрес-приставки>
```

#### 3.1. Создайте директорию для конфигурации

```bash
mkdir -p /home/$(whoami)/cloudflared
```

#### 3.2. Запустите контейнер `cloudflared`

Замените `<YOUR_TUNNEL_TOKEN>` на токен, скопированный из Cloudflare Dashboard:

```bash
docker run -d \
  --name cloudflared-tunnel \
  --restart=unless-stopped \
  cloudflare/cloudflared:latest tunnel run --token <YOUR_TUNNEL_TOKEN>
```

**Пример:**

```bash
docker run -d \
  --name cloudflared-tunnel \
  --restart=unless-stopped \
  cloudflare/cloudflared:latest tunnel run --token eyJhIjoiYWJjMTIzLi4uXyIsInQiOiJkZWY0NTYuLi4ifQ==
```

#### 3.3. Проверьте статус контейнера

```bash
docker ps | grep cloudflared
```

**Ожидаемый результат:**

```
xxxxxxxxx   cloudflare/cloudflared:latest   "cloudflared tunnel..."   Up 10 seconds
```

**Просмотр логов:**

```bash
docker logs cloudflared-tunnel
```

**Ожидаемый вывод:**

```
Connected to <tunnel-id>.cfargotunnel.com
Connection established
```

---

### Шаг 4: Настройка Public Hostname

Вернитесь в Cloudflare Zero Trust Dashboard:

#### 4.1. Добавьте Public Hostname

1. На странице вашего туннеля перейдите во вкладку **Public Hostnames**
2. Нажмите **Add a public hostname**

#### 4.2. Заполните поля:

**Subdomain:**
```
ha
```
(или любое другое имя, например `home`, `homeassistant`)

**Domain:**
```
mydomain.tk
```
(ваш домен)

**Path:** оставьте пустым

**Type:**
```
HTTP
```

**URL:**
```
http://homeassistant:8123
```

> ⚠️ **Важно:** Используйте имя контейнера Home Assistant (`homeassistant`), а не `localhost` или `127.0.0.1`, так как Docker-контейнеры находятся в общей сети.

#### 4.3. Дополнительные настройки (Additional application settings)

Разверните раздел **Additional application settings** и включите:

- **No TLS Verify**: **ON** (так как Home Assistant использует HTTP)
- **HTTP Host Header**: оставьте пустым

4. Нажмите **Save hostname**

---

### Шаг 5: Настройка Home Assistant

#### 5.1. Добавьте ваш домен в `configuration.yaml`

Подключитесь к приставке по SSH и откройте файл конфигурации:

```bash
nano /home/$(whoami)/homeassistant/configuration.yaml
```

Добавьте или измените секцию `http`:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12   # Docker сеть
    - 192.168.0.0/16  # Локальная сеть
    - 10.0.0.0/8      # Локальная сеть
  # Добавьте ваш домен
  external_url: https://ha.mydomain.tk
  internal_url: http://homeassistant:8123
```

> ⚠️ **Замените `ha.mydomain.tk` на ваш реальный домен!**

Сохраните файл (`Ctrl+O`, `Enter`, `Ctrl+X`).

#### 5.2. Перезапустите Home Assistant

```bash
docker restart homeassistant
```

Подождите 30-60 секунд для перезапуска.

---

### Шаг 6: Проверка доступа

Откройте браузер (или мобильное приложение Home Assistant) и перейдите по адресу:

```
https://ha.mydomain.tk
```

✅ **Вы должны увидеть интерфейс Home Assistant с зелёным замком SSL!**

Теперь вы можете подключаться к Home Assistant с любого устройства с интернетом.

---

## 📱 Настройка мобильного приложения

### iOS / Android

1. Скачайте приложение **Home Assistant** из App Store / Google Play
2. При первом запуске введите URL:

   ```
   https://ha.mydomain.tk
   ```

3. Войдите с вашими учётными данными

✅ Теперь вы можете управлять умным домом из любой точки мира!

---

## 🔒 Дополнительная защита (опционально)

### Добавление Cloudflare Access (2FA)

Для дополнительной защиты можно включить аутентификацию через Cloudflare Access:

1. В Zero Trust Dashboard перейдите в **Access** → **Applications**
2. Нажмите **Add an application** → **Self-hosted**
3. Задайте имя (например, `Home Assistant Access`)
4. Укажите домен: `ha.mydomain.tk`
5. Добавьте политику доступа:
   - **Rule name**: любое (например, `Allow my email`)
   - **Rule action**: **Allow**
   - **Selector**: **Emails**
   - **Value**: ваш email
6. Нажмите **Save**

Теперь перед входом в Home Assistant Cloudflare будет запрашивать подтверждение через email.

---

## 🛠 Управление контейнером `cloudflared`

### Просмотр логов:

```bash
docker logs -f cloudflared-tunnel
```

### Перезапуск контейнера:

```bash
docker restart cloudflared-tunnel
```

### Остановка контейнера:

```bash
docker stop cloudflared-tunnel
```

### Запуск контейнера:

```bash
docker start cloudflared-tunnel
```

### Удаление контейнера:

```bash
docker rm -f cloudflared-tunnel
```

---

## 🔧 Решение проблем

### Проблема 1: Не открывается сайт `ha.mydomain.tk`

**Причины:**

1. **DNS ещё не обновился**
   - Подождите 5-30 минут
   - Проверьте пропагацию: [https://dnschecker.org](https://dnschecker.org)

2. **Контейнер `cloudflared` не запущен**
   - Проверьте: `docker ps | grep cloudflared`
   - Посмотрите логи: `docker logs cloudflared-tunnel`

3. **Неправильно указан URL в Public Hostname**
   - Убедитесь, что используется `http://homeassistant:8123`, а не `localhost`

---

### Проблема 2: Ошибка «400: Bad Request»

**Причина:** Home Assistant не доверяет прокси Cloudflare.

**Решение:** Убедитесь, что в `configuration.yaml` добавлены:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12
    - 192.168.0.0/16
    - 10.0.0.0/8
  external_url: https://ha.mydomain.tk
  internal_url: http://homeassistant:8123
```

Перезапустите Home Assistant:

```bash
docker restart homeassistant
```

---

### Проблема 3: Контейнер `cloudflared` постоянно перезапускается

**Причина:** Неправильный токен туннеля.

**Решение:**

1. Удалите старый контейнер:

   ```bash
   docker rm -f cloudflared-tunnel
   ```

2. Скопируйте новый токен из Cloudflare Dashboard

3. Запустите контейнер заново с новым токеном

---

### Проблема 4: Мобильное приложение не подключается

**Причина:** В приложении указан внутренний IP-адрес.

**Решение:**

1. Откройте приложение Home Assistant
2. Перейдите в **Настройки** → **Профиль** → **Подключения**
3. Удалите старое подключение
4. Добавьте новое с URL: `https://ha.mydomain.tk`

---

## 📊 Мониторинг туннеля

В Cloudflare Zero Trust Dashboard можно просматривать:

- **Статус туннеля** (зелёный = активен)
- **Статистику запросов**
- **Логи подключений**

---

## 📚 Полезные ссылки

- [Официальная документация Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Документация Home Assistant - Remote Access](https://www.home-assistant.io/docs/configuration/remote/)
- [Инструкция по установке HA](README_homeassistent.md)
- [Docker Hub - cloudflared](https://hub.docker.com/r/cloudflare/cloudflared)

---

## ⚠️ Важные замечания

1. **Не делитесь токеном туннеля** — это полный доступ к вашему Home Assistant.
2. **Используйте сильные пароли** в Home Assistant.
3. **Включите 2FA** в Home Assistant (через профиль пользователя).
4. Cloudflare бесплатно предоставляет **до 50 пользователей Zero Trust**.

---

## 🤝 Вклад в проект

Если вы нашли ошибку или хотите улучшить документацию — создайте Issue или Pull Request.

---

## 📄 Лицензия

MIT License
