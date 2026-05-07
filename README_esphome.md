# 📡 ESPHome — создание умных устройств для Home Assistant

> **Прошивка ESP8266/ESP32 без программирования — только YAML-конфигурация**

ESPHome — это открытый проект для создания дешёвых Wi-Fi и Bluetooth устройств **без знания языков программирования**. Основан на платформах **ESP8266**, **ESP32** и **RP2040** (Raspberry Pi Pico).

---

## ❓ Что такое ESPHome?

ESPHome преобразует простой YAML-файл в прошивку для микроконтроллеров. Вы описываете, что хотите получить (реле, датчик температуры, светодиодную ленту), а ESPHome создаёт готовую прошивку.

### 🎯 Основные возможности:

- ✅ **Автоматическая интеграция** с Home Assistant (через Native API)
- ✅ **Большой выбор периферии**: датчики, реле, светодиоды, дисплеи, моторы
- ✅ **OTA-обновления** (прошивка по Wi-Fi без проводов)
- ✅ **Веб-интерфейс** для управления без Home Assistant
- ✅ **Создание новых устройств** без программного обеспечения
- ✅ **Перепрошивка готовых устройств** (Sonoff, Shelly, Tuya)

---

## 💻 Способы установки ESPHome

Есть **3 основных способа** установки ESPHome:

### 1️⃣ **ESPHome Builder Desktop** (рекомендуется для ПК)

**Преимущества:**
- ✅ Простой графический интерфейс
- ✅ Автоматическое распознавание USB-портов
- ✅ Не требует Home Assistant
- ✅ Работает на Windows, macOS, Linux

**Установка:**

1. Скачайте инсталлятор с [GitHub Releases](https://github.com/esphome/esphome-desktop/releases/latest):

| Платформа | Файл |
|----------|-------|
| **Windows** | `ESPHome.Builder_x.x.x_x64-setup.exe` |
| **macOS (Apple Silicon)** | `ESPHome.Builder_x.x.x_aarch64.dmg` |
| **macOS (Intel)** | `ESPHome.Builder_x.x.x_x64.dmg` |
| **Linux** | `ESPHome.Builder_x.x.x_amd64.AppImage` / `.deb` |

2. Установите приложение
3. Запустите **ESPHome Builder**

---

### 2️⃣ **Docker на TV-приставке S905X3** (рекомендуется)

**Преимущества:**
- ✅ Всегда доступен в сети
- ✅ Не занимает ПК
- ✅ Интегрирован с Home Assistant

**Установка на S905X3 с Armbian:**

Подключитесь к приставке по SSH:

```bash
ssh root@<IP-адрес-приставки>
```

#### Шаг 1: Создайте директорию для конфигураций

```bash
mkdir -p /home/$(whoami)/esphome/config
```

#### Шаг 2: Запустите Docker-контейнер ESPHome

```bash
docker run -d \
  --name esphome \
  --restart=unless-stopped \
  -e TZ=Europe/Kiev \
  -v /home/$(whoami)/esphome/config:/config \
  -p 6052:6052 \
  esphome/esphome:latest
```

#### Шаг 3: Проверьте статус

```bash
docker ps | grep esphome
```

**Ожидаемый результат:**

```
xxxxxxxxx   esphome/esphome:latest   "/entrypoint.sh..."   Up 10 seconds   0.0.0.0:6052->6052/tcp
```

#### Шаг 4: Откройте веб-интерфейс

В браузере перейдите по адресу:

```
http://<IP-адрес-приставки>:6052
```

---

### 3️⃣ **Адд-он в Home Assistant** (простой способ)

**Преимущества:**
- ✅ Интегрирован в Home Assistant
- ✅ Не требует отдельного Docker
- ✅ Автоматическое обнаружение устройств

**Установка:**

1. Откройте Home Assistant
2. Перейдите в **Настройки** → **Дополнения** → **Магазин дополнений**
3. Найдите **ESPHome**
4. Нажмите **Установить**
5. После установки нажмите **Запустить**
6. Откройте **Боковое меню** → **ESPHome**

---

## 🔨 Создание первого устройства

### Пример 1: Реле на ESP8266 (NodeMCU)

#### Шаг 1: Создайте новое устройство

В веб-интерфейсе ESPHome нажмите **+ NEW DEVICE** и выберите:

- **Name**: `relay` (имя устройства)
- **Wi-Fi SSID**: имя вашей сети
- **Wi-Fi Password**: пароль
- **Board**: `nodemcuv2` (для ESP8266 NodeMCU)

#### Шаг 2: Редактируйте YAML-файл

Нажмите **EDIT** и добавьте реле:

```yaml
esphome:
  name: relay
  platform: ESP8266
  board: nodemcuv2

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

  # Резервная точка доступа (на случай, если Wi-Fi недоступен)
  ap:
    ssid: "Relay Fallback"
    password: "12345678"

# Автоматическая интеграция с Home Assistant
api:
  encryption:
    key: "YOUR_ENCRYPTION_KEY"

# OTA-обновления (прошивка по Wi-Fi)
ota:
  password: "ota_password"

# Веб-сервер для управления без Home Assistant
web_server:
  port: 80

# Логгер
logger:

# Реле на пине D3 (GPIO0)
switch:
  - platform: gpio
    name: "Relay"
    pin: D3
    id: relay_1
```

#### Шаг 3: Сохраните и загрузите прошивку

1. Нажмите **SAVE**
2. Нажмите **INSTALL**
3. Выберите **Plug into this computer** (первая прошивка через USB)
4. Подключите ESP8266 через USB
5. Выберите COM-порт (например, `/dev/ttyUSB0` или `COM3`)
6. Дождитесь завершения прошивки

✅ **Устройство готово!** Все последующие обновления можно делать по Wi-Fi (через **Wirelessly**).

---

### Пример 2: Датчик температуры DHT22

Добавьте в YAML:

```yaml
sensor:
  - platform: dht
    pin: D4
    model: DHT22
    temperature:
      name: "Temperature"
    humidity:
      name: "Humidity"
    update_interval: 60s
```

---

### Пример 3: Управление светодиодной лентой (WS2812B)

```yaml
light:
  - platform: fastled_clockless
    chipset: WS2812B
    pin: D2
    num_leds: 60
    rgb_order: GRB
    name: "LED Strip"
```

---

## 🔗 Интеграция с Home Assistant

### Способ 1: Native API (рекомендуется)

Добавьте в YAML:

```yaml
api:
  encryption:
    key: "YOUR_ENCRYPTION_KEY"
```

Home Assistant **автоматически обнаружит** устройство после прошивки.

Перейдите в **Настройки** → **Устройства и службы** → **Интеграции** — там появится новое устройство.

---

### Способ 2: MQTT

Добавьте в YAML:

```yaml
mqtt:
  broker: 192.168.1.41  # IP-адрес MQTT-брокера
  port: 1883
  username: admin
  password: mqtt_password
```

> ⚠️ **Не используйте MQTT одновременно с Native API** — это приведёт к конфликту.

---

### Способ 3: REST API (через Web Server)

Добавьте в YAML:

```yaml
web_server:
  port: 80
  auth:
    username: admin
    password: web_password
```

**Управление через HTTP:**

- **Включить реле**: `http://relay.local/switch/relay/turn_on`
- **Выключить реле**: `http://relay.local/switch/relay/turn_off`
- **Переключить**: `http://relay.local/switch/relay/toggle`

---

## 🧩 Полезные компоненты

### Датчики:
- **DHT11/DHT22** (температура + влажность)
- **BMP280/BME280** (температура, давление, влажность)
- **HC-SR04** (ультразвуковой дальномер)
- **PIR** (датчик движения)
- **Photoresistor** (освещённость)

### Исполнительные устройства:
- **GPIO реле**
- **Светодиодные ленты** (WS2812B, APA102)
- **Сервоприводы**
- **Шаговые двигатели**

### Дисплеи:
- **OLED (SSD1306, SH1106)**
- **LCD I2C**
- **TFT**

---

## 🔧 Автоматизации в ESPHome

ESPHome позволяет создавать **локальные автоматизации** (без Home Assistant).

### Пример 1: Включение реле по кнопке

```yaml
binary_sensor:
  - platform: gpio
    pin: D5
    name: "Button"
    on_press:
      then:
        - switch.toggle: relay_1
```

### Пример 2: Включение вентилятора при перегреве

```yaml
sensor:
  - platform: dht
    pin: D4
    model: DHT22
    temperature:
      name: "Temperature"
      on_value_range:
        - above: 30.0
          then:
            - switch.turn_on: fan
        - below: 25.0
          then:
            - switch.turn_off: fan
```

---

## 📚 Полезные ссылки

- [Официальная документация ESPHome](https://esphome.io/)
- [ESPHome Builder Desktop (GitHub)](https://github.com/esphome/esphome-desktop)
- [Готовые устройства с ESPHome на AliExpress](https://aliexpress.com) (ищите по запросу "made for ESPHome")
- [Налаштовуємо ESPHome. Посібник для початківців (DOU)](https://dou.ua/forums/topic/42488/)
- [Home Assistant Интеграция ESPHome](https://www.home-assistant.io/integrations/esphome/)

---

## 🛠 Решение проблем

### Проблема 1: Устройство не подключается к Wi-Fi

**Причины:**
- Неправильный SSID или пароль
- Wi-Fi на 5 GHz (ESP8266 поддерживает только 2.4 GHz)

**Решение:**
- Проверьте логи через USB: `esphome logs relay.yaml`
- Подключитесь к резервной точке доступа (`Relay Fallback`)

---

### Проблема 2: Home Assistant не обнаруживает устройство

**Причины:**
- Отсутствует `api:` в YAML
- Неправильный ключ шифрования

**Решение:**
- Добавьте `api:` в YAML и перепрошейте
- Вручную добавьте интеграцию: **Настройки** → **Интеграции** → **+ Добавить** → **ESPHome**

---

### Проблема 3: Не могу прошить через USB

**Причины:**
- Не установлены драйверы CH340/CP2102
- Неправильно выбран COM-порт

**Решение:**
- Установите драйверы CH340 (для Windows/macOS/Linux)
- Проверьте COM-порт в Диспетчере устройств (Windows) или `ls /dev/ttyUSB*` (Linux)

---

## 🤝 Вклад в проект

Если вы нашли ошибку или хотите улучшить документацию — создайте Issue или Pull Request.

---

## 📄 Лицензия

MIT License
