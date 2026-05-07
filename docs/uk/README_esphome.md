# 📡 ESPHome — створення розумних пристроїв для Home Assistant

> **Прошивка ESP8266/ESP32 без програмування — тільки YAML-конфігурація**

ESPHome — це відкритий проєкт для створення дешевих Wi-Fi та Bluetooth пристроїв **без знання мов програмування**. Оснований на платформах **ESP8266**, **ESP32** та **RP2040** (Raspberry Pi Pico).

## ❓ Що таке ESPHome?

ESPHome перетворює простий YAML-файл у прошивку для мікроконтролерів. Ви описуєте, що хочете отримати (реле, датчик температури, світлодіодну стрічку), а ESPHome створює готову прошивку.

### 🎯 Основні можливості:

* ✅ **Автоматична інтеграція** з Home Assistant (через Native API)
* ✅ **Великий вибір периферії**: датчики, реле, світлодіоди, дисплеї, двигуни
* ✅ **OTA-оновлення** (прошивка по Wi-Fi без проводів)
* ✅ **Веб-інтерфейс** для управління без Home Assistant
* ✅ **Створення нових пристроїв** без програмного забезпечення
* ✅ **Перепрошивка готових пристроїв** (Sonoff, Shelly, Tuya)

## 💻 Способи встановлення ESPHome

Є **3 основних способи** встановлення ESPHome:

### 1️⃣ **ESPHome Builder Desktop** (рекомендовано для ПК)

**Переваги:**

* ✅ Простий графічний інтерфейс
* ✅ Автоматичне розпізнавання USB-портів
* ✅ Не потребує Home Assistant
* ✅ Працює на Windows, macOS, Linux

**Встановлення:**

1. Завантажте інсталятор з [GitHub Releases](https://github.com/esphome/esphome-desktop/releases/latest):

| Платформа | Файл |
|---|---|
| **Windows** | `ESPHome.Builder_x.x.x_x64-setup.exe` |
| **macOS (Apple Silicon)** | `ESPHome.Builder_x.x.x_aarch64.dmg` |
| **macOS (Intel)** | `ESPHome.Builder_x.x.x_x64.dmg` |
| **Linux** | `ESPHome.Builder_x.x.x_amd64.AppImage` / `.deb` |

2. Встановіть додаток
3. Запустіть **ESPHome Builder**

### 2️⃣ **Docker на TV-приставці S905X3** (рекомендовано)

**Переваги:**

* ✅ Завжди доступний у мережі
* ✅ Не займає ПК
* ✅ Інтегрований з Home Assistant

**Встановлення на S905X3 з Armbian:**

Підключіться до приставки по SSH:

```bash
ssh root@<IP-адреса-приставки>
```

#### Крок 1: Створіть директорію для конфігурацій

```bash
mkdir -p /home/$(whoami)/esphome/config
```

#### Крок 2: Запустіть Docker-контейнер ESPHome

```bash
docker run -d \\
  --name esphome \\
  --restart=unless-stopped \\
  -e TZ=Europe/Kiev \\
  -v /home/$(whoami)/esphome/config:/config \\
  -p 6052:6052 \\
  esphome/esphome:latest
```

#### Крок 3: Перевірте статус

```bash
docker ps | grep esphome
```

**Очікуваний результат:**

```
xxxxxxxxx esphome/esphome:latest "/entrypoint.sh..." Up 10 seconds 0.0.0.0:6052->6052/tcp
```

#### Крок 4: Відкрийте веб-інтерфейс

В браузері перейдіть за адресою:

```
http://<IP-приставки>:6052
```

### 3️⃣ **Адд-он у Home Assistant** (простий спосіб)

**Переваги:**

* ✅ Інтегрований в Home Assistant
* ✅ Не потребує окремого Docker
* ✅ Автоматичне виявлення пристроїв

**Встановлення:**

1. Відкрийте Home Assistant
2. Перейдіть в **Налаштування** → **Додатки** → **Магазин додатків**
3. Знайдіть **ESPHome**
4. Натисніть **Встановити**
5. Після встановлення натисніть **Запустити**
6. Відкрийте **Бокове меню** → **ESPHome**

## 🔨 Створення першого пристрою

### Приклад 1: Реле на ESP8266 (NodeMCU)

#### Крок 1: Створіть новий пристрій

В веб-інтерфейсі ESPHome натисніть **+ NEW DEVICE** та оберіть:

* **Name**: `relay` (назва пристрою)
* **Wi-Fi SSID**: назва вашої мережі
* **Wi-Fi Password**: пароль
* **Board**: `nodemcuv2` (для ESP8266 NodeMCU)

#### Крок 2: Редагуйте YAML-файл

Натисніть **EDIT** та додайте реле:

```yaml
esphome:
  name: relay
  platform: ESP8266
  board: nodemcuv2

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  
  # Резервна точка доступу (на випадок, якщо Wi-Fi недоступний)
  ap:
    ssid: "Relay Fallback"
    password: "12345678"

# Автоматична інтеграція з Home Assistant
api:
  encryption:
    key: "YOUR_ENCRYPTION_KEY"

# OTA-оновлення (прошивка по Wi-Fi)
ota:
  password: "ota_password"

# Веб-сервер для управління без Home Assistant
web_server:
  port: 80

# Логер
logger:

# Реле на піні D3 (GPIO0)
switch:
  - platform: gpio
    name: "Relay"
    pin: D3
    id: relay_1
```

#### Крок 3: Збережіть та завантажте прошивку

1. Натисніть **SAVE**
2. Натисніть **INSTALL**
3. Оберіть **Plug into this computer** (перша прошивка через USB)
4. Підключіть ESP8266 через USB
5. Оберіть COM-порт (наприклад, `/dev/ttyUSB0` або `COM3`)
6. Дочекайтеся завершення прошивки

✅ **Пристрій готовий!** Всі наступні оновлення можна робити по Wi-Fi (через **Wirelessly**).

### Приклад 2: Датчик температури DHT22

Додайте в YAML:

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

### Приклад 3: Управління світлодіодною стрічкою (WS2812B)

```yaml
light:
  - platform: fastled_clockless
    chipset: WS2812B
    pin: D2
    num_leds: 60
    rgb_order: GRB
    name: "LED Strip"
```

## 🔗 Інтеграція з Home Assistant

### Спосіб 1: Native API (рекомендовано)

Додайте в YAML:

```yaml
api:
  encryption:
    key: "YOUR_ENCRYPTION_KEY"
```

Home Assistant **автоматично виявить** пристрій після прошивки.

Перейдіть в **Налаштування** → **Пристрої та служби** → **Інтеграції** — там з'явиться новий пристрій.

### Спосіб 2: MQTT

Додайте в YAML:

```yaml
mqtt:
  broker: 192.168.1.41  # IP-адреса MQTT-брокера
  port: 1883
  username: admin
  password: mqtt_password
```

> ⚠️**Не використовуйте MQTT одночасно з Native API** — це призведе до конфлікту.

### Спосіб 3: REST API (через Web Server)

Додайте в YAML:

```yaml
web_server:
  port: 80
  auth:
    username: admin
    password: web_password
```

**Управління через HTTP:**

* **Увімкнути реле**: `http://relay.local/switch/relay/turn_on`
* **Вимкнути реле**: `http://relay.local/switch/relay/turn_off`
* **Перемикати**: `http://relay.local/switch/relay/toggle`

## 🧩 Корисні компоненти

### Датчики:

* **DHT11/DHT22** (температура + вологість)
* **BMP280/BME280** (температура, тиск, вологість)
* **HC-SR04** (ультразвуковий дальномір)
* **PIR** (датчик руху)
* **Photoresistor** (освітленість)

### Виконавчі пристрої:

* **GPIO реле**
* **Світлодіодні стрічки** (WS2812B, APA102)
* **Сервоприводи**
* **Крокові двигуни**

### Дисплеї:

* **OLED (SSD1306, SH1106)**
* **LCD I2C**
* **TFT**

## 🔧 Автоматизації в ESPHome

ESPHome дозволяє створювати **локальні автоматизації** (без Home Assistant).

### Приклад 1: Увімкнення реле по кнопці

```yaml
binary_sensor:
  - platform: gpio
    pin: D5
    name: "Button"
    on_press:
      then:
        - switch.toggle: relay_1
```

### Приклад 2: Увімкнення вентилятора при перегріві

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

## 📚 Корисні посилання

* [Офіційна документація ESPHome](https://esphome.io/)
* [ESPHome Builder Desktop (GitHub)](https://github.com/esphome/esphome-desktop)
* [Готові пристрої з ESPHome на AliExpress](https://aliexpress.com/) (шукайте за запитом "made for ESPHome")
* [Налаштовуємо ESPHome. Посібник для початківців (DOU)](https://dou.ua/forums/topic/42488/)
* [Home Assistant Інтеграція ESPHome](https://www.home-assistant.io/integrations/esphome/)

## 🛠 Вирішення проблем

### Проблема 1: Пристрій не підключається до Wi-Fi

**Причини:**

* Неправильний SSID або пароль
* Wi-Fi на 5 GHz (ESP8266 підтримує тільки 2.4 GHz)

**Вирішення:**

* Перевірте логи через USB: `esphome logs relay.yaml`
* Підключіться до резервної точки доступу (`Relay Fallback`)

### Проблема 2: Home Assistant не виявляє пристрій

**Причини:**

* Відсутній `api:` в YAML
* Неправильний ключ шифрування

**Вирішення:**

* Додайте `api:` в YAML та перепрошийте
* Вручну додайте інтеграцію: **Налаштування** → **Інтеграції** → **+ Додати** → **ESPHome**

### Проблема 3: Не можу прошити через USB

**Причини:**

* Не встановлені драйвери CH340/CP2102
* Неправильно обрано COM-порт

**Вирішення:**

* Встановіть драйвери CH340 (для Windows/macOS/Linux)
* Перевірте COM-порт в Диспетчері пристроїв (Windows) або `ls /dev/ttyUSB*` (Linux)

## 🤝 Внесок в проєкт

Якщо ви знайшли помилку або хочете покращити документацію — створіть Issue або Pull Request.

## 📄 Ліцензія

MIT License
