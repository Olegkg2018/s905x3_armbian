# 🏠 Установка Home Assistant на S905X3 с Armbian

> **Простая установка через armbian-software без ручной настройки Docker**

Это руководство описывает установку Home Assistant Core в Docker-контейнере на TV-приставке Amlogic S905X3 (4GB RAM / 32GB eMMC) под управлением Armbian.

---

## 📋 Что потребуется

- TV-приставка S905X3 с установленным Armbian (см. [README_install_armbian.md](README_install_armbian.md))
- Подключение по SSH
- Доступ к интернету

---

## 🚀 Пошаговая установка

### Шаг 1: Обновление скриптов armbian-software

Перед началом обновите утилиту управления пакетами:

```bash
armbian-software -u
```

**Ожидаемый результат:**

```
[ STEPS ] Updating software management scripts...
[ SUCCESS ] Scripts updated successfully.
```

---

### Шаг 2: Открытие меню armbian-software

Запустите интерактивное меню:

```bash
armbian-software
```

**Вы увидите список доступных пакетов:**

```
[ STEPS ] Displaying software list [ System: debian/trixie ]...
───────────────────────────────────────────────────────────────────
ID    NAME                           STATE           MANAGE
───────────────────────────────────────────────────────────────────
101   Docker                         not-installed   install
102   Portainer                      not-installed   install
...
108   HomeAssistant                  not-installed   install
...
───────────────────────────────────────────────────────────────────
[ OPTIONS ] Please Input Software ID:
```

---

### Шаг 3: Установка Docker (ID: 101)

**Введите:**

```
101
```

Нажмите **Enter**. Скрипт автоматически:

- Установит Docker Engine
- Настроит systemd-сервис `docker.service`
- Добавит текущего пользователя в группу `docker`
- Включит автозапуск Docker при загрузке

**Проверка установки:**

```bash
docker --version
systemctl status docker
```

**Ожидаемый результат:**

```
Docker version 24.x.x, build ...
● docker.service - Docker Application Container Engine
   Active: active (running)
```

> ⚠️ **Важно:** После установки Docker выйдите из SSH-сессии и войдите заново, чтобы изменения группы вступили в силу.

---

### Шаг 4: Установка Portainer (ID: 102)

**Введите в меню armbian-software:**

```
102
```

Portainer — это веб-интерфейс для управления Docker-контейнерами. Скрипт автоматически:

- Создаст Docker volume `portainer_data`
- Запустит контейнер Portainer на порту **9443**
- Настроит автоматический перезапуск контейнера

**Доступ к Portainer:**

Откройте браузер и перейдите по адресу:

```
http://<IP-адрес-приставки>:9443
```

При первом входе создайте учётную запись администратора:

- **Username:** `admin`
- **Password:** *(минимум 12 символов)*

Выберите **Local** (управление локальным Docker).

**Проверка контейнера:**

```bash
docker ps
```

**Ожидаемый результат:**

```
CONTAINER ID   IMAGE                          COMMAND        PORTS
xxxxxxxxx      portainer/portainer-ce:latest  "/portainer"   0.0.0.0:9443->9443/tcp
```

---

### Шаг 5: Установка Home Assistant (ID: 108)

**Введите в меню armbian-software:**

```
108
```

Скрипт автоматически:

- Создаст директорию конфигурации `/home/<user>/homeassistant` (или `/root/homeassistant`)
- Запустит контейнер Home Assistant Core на порту **8123**
- Настроит автоматический перезапуск контейнера
- Смонтирует директорию конфигурации как volume

**Первый запуск Home Assistant:**

1. Откройте браузер и перейдите по адресу:

   ```
   http://<IP-адрес-приставки>:8123
   ```

2. Дождитесь завершения первоначальной настройки (может занять 2-3 минуты).

3. Создайте учётную запись администратора:
   - **Имя**
   - **Логин**
   - **Пароль**

4. Укажите местоположение для автоматической настройки часового пояса и погоды.

**Проверка контейнера:**

```bash
docker ps
```

**Ожидаемый результат:**

```
CONTAINER ID   IMAGE                                      COMMAND         PORTS
xxxxxxxxx      ghcr.io/home-assistant/home-assistant:stable   "/init"   0.0.0.0:8123->8123/tcp
xxxxxxxxx      portainer/portainer-ce:latest                  "/portainer" 0.0.0.0:9443->9443/tcp
```

---

## 🔧 Установка HACS (Home Assistant Community Store)

**HACS** — это магазин пользовательских компонентов и интеграций для Home Assistant.

### Способ 1: Установка через SSH (рекомендуется)

#### 1. Подключитесь к контейнеру Home Assistant:

```bash
docker exec -it homeassistant bash
```

#### 2. Скачайте и запустите скрипт установки HACS:

```bash
wget -O - https://get.hacs.xyz | bash -
```

#### 3. Выйдите из контейнера:

```bash
exit
```

#### 4. Перезапустите Home Assistant:

```bash
docker restart homeassistant
```

#### 5. Активируйте HACS в интерфейсе Home Assistant:

1. Откройте **Настройки** → **Устройства и службы** → **Добавить интеграцию**
2. Найдите **HACS** и добавьте его
3. Следуйте инструкциям для авторизации через GitHub:
   - Перейдите на [https://github.com/login/device](https://github.com/login/device)
   - Введите код активации из Home Assistant
   - Подтвердите авторизацию

---

### Способ 2: Установка через Portainer (графический интерфейс)

#### 1. Откройте Portainer:

```
http://<IP-адрес-приставки>:9443
```

#### 2. Перейдите в **Containers** → найдите контейнер `homeassistant` → нажмите **>_ Console**

#### 3. Выберите **Connect** и выполните команду:

```bash
wget -O - https://get.hacs.xyz | bash -
```

#### 4. Перезапустите контейнер через Portainer (кнопка **Restart**).

#### 5. Активируйте HACS в Home Assistant (см. пункт 5 из Способа 1).

---

## 📊 Управление контейнерами

### Через командную строку (SSH)

**Просмотр запущенных контейнеров:**

```bash
docker ps
```

**Просмотр логов Home Assistant:**

```bash
docker logs -f homeassistant
```

**Перезапуск контейнера:**

```bash
docker restart homeassistant
```

**Остановка контейнера:**

```bash
docker stop homeassistant
```

**Запуск контейнера:**

```bash
docker start homeassistant
```

**Удаление контейнера:**

```bash
docker rm -f homeassistant
```

---

### Через Portainer (веб-интерфейс)

1. Откройте Portainer: `http://<IP>:9443`
2. Перейдите в **Containers**
3. Выберите контейнер `homeassistant`
4. Используйте кнопки:
   - **Start** / **Stop** / **Restart**
   - **Logs** — просмотр логов
   - **Inspect** — просмотр конфигурации
   - **Stats** — мониторинг ресурсов (CPU, RAM, сеть)

---

## 🔄 Обновление Home Assistant

### Способ 1: Через armbian-software

```bash
armbian-software
```

Выберите **ID: 108** и следуйте инструкциям для обновления.

---

### Способ 2: Вручную (Docker)

#### 1. Остановите и удалите старый контейнер:

```bash
docker stop homeassistant
docker rm homeassistant
```

#### 2. Скачайте новый образ:

```bash
docker pull ghcr.io/home-assistant/home-assistant:stable
```

#### 3. Запустите новый контейнер:

```bash
docker run -d \
  --name homeassistant \
  --restart=unless-stopped \
  -e TZ=Europe/Kiev \
  -v /home/$(whoami)/homeassistant:/config \
  -p 8123:8123 \
  ghcr.io/home-assistant/home-assistant:stable
```

---

## 🛠 Решение проблем

### Home Assistant не запускается

**Проверьте логи:**

```bash
docker logs homeassistant
```

**Типичные ошибки:**

- **Ошибка базы данных:** Удалите файл `home-assistant_v2.db` из директории конфигурации.
- **Конфликт портов:** Убедитесь, что порт `8123` не занят другим приложением.

---

### Порты заняты

**Проверьте, какие порты слушаются:**

```bash
sudo netstat -tulpn | grep LISTEN
```

**Освободите порт или измените маппинг в Docker:**

```bash
-p 8124:8123  # Использовать порт 8124 вместо 8123
```

---

### HACS не отображается

**Убедитесь, что интеграция добавлена:**

**Настройки** → **Устройства и службы** → найдите **HACS**.

**Если HACS отсутствует:**

```bash
docker exec -it homeassistant bash
ls /config/custom_components/hacs
```

Если директории нет — повторите установку.

---

## 📂 Структура файлов

```
/home/<user>/homeassistant/   # Директория конфигурации Home Assistant
├── configuration.yaml         # Основной файл конфигурации
├── automations.yaml           # Автоматизации
├── scripts.yaml               # Скрипты
├── scenes.yaml                # Сцены
├── secrets.yaml               # Секреты (пароли, токены)
├── home-assistant.log         # Лог-файл
├── home-assistant_v2.db       # База данных
└── custom_components/         # Пользовательские компоненты (HACS)
    └── hacs/
```

---

## 🔗 Полезные ссылки

- [Официальная документация Home Assistant](https://www.home-assistant.io/docs/)
- [HACS — Community Store](https://hacs.xyz/)
- [Armbian Forum](https://forum.armbian.com/)
- [Portainer Documentation](https://docs.portainer.io/)
- [Обсуждение S905X3 на 4PDA](https://4pda.to/forum/index.php?showtopic=738366)

---

## 🤝 Вклад в проект

Если вы нашли ошибку или хотите улучшить документацию — создайте Issue или Pull Request в репозитории.

---

## 📄 Лицензия

MIT License
