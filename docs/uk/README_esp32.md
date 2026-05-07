# 🔋 ESP32 JK-BMS & Sumry Inverter Gateway

Універсальний шлюз на базі **ESP32 (ESP32-ETH01)** для моніторингу та управління системою накопичення енергії. Об'єднує дані від BMS (по Bluetooth) та гібридного інвертора (по RS485) в єдину екосистему Home Assistant через ESPHome.

## ☀️ Можливості

* **JK-BMS**: Читання напружень яцеек, токів, температур, SOC, управління балансуванням і реле (через Bluetooth BLE).
* **Sumry CP3200**: Опрос даних інвертора (напруження мережі, батареї, потужність, помилки) через Modbus RTU.
* **Інтеграція**: Повна нативна підтримка в Home Assistant.
* **Апаратна частина**: Використання ізольованого перетворювача TTL-RS485 для надійного зв'язку.

## 🔌 Схема підключення (Wiring Diagram)

Використовується плата **ESP32-ETH01** (WROOM/WROVER) и модуль **Isolated TTL to RS485**.

### Pinout ESP32 -> RS485 Module

| **ESP32 GPIO** | **RS485 Module** | **Описание**          |
|----------------|------------------|-----------------------|
| GPIO17 (TX)    | RXD              | UART передача         |
| GPIO16 (RX)    | TXD              | UART прийом           |
| GND            | GND              | Загальна земля        |
| 3.3V           | VCC              | Живлення модуля       |

### Sumry CP3200 -> RS485 Module

| **Термінал Sumry** | **RS485 Module** |
|--------------------|------------------|
| RS485-A            | A+               |
| RS485-B            | B-               |
| GND                | GND (optional)   |

> ⚠️ **Важливо**: Використовуйте **ізольований** TTL-RS485 модуль для захисту ESP32 від перенапруг і високих потенціалів з боку інвертора.

---

## 📦 Встановлення

### 1. Підготовка середовища ESPHome

Установіть ESPHome (на хості або в Docker):

```bash
pip3 install esphome
# або
docker pull esphome/esphome
```

### 2. Створення конфігураційного файлу

Створіть файл `jk-sumry-inverter.yaml` з наступною структурою:

```yaml
esphome:
  name: jk-sumry-gateway
  platform: ESP32
  board: esp32dev

wifi:
  ssid: "YOUR_WIFI_SSID"
  password: "YOUR_WIFI_PASSWORD"

logger:
  level: DEBUG

api:
  encryption:
    key: "YOUR_API_KEY"

ota:
  password: "YOUR_OTA_PASSWORD"

# Modbus RTU для Sumry
modbus:
  id: modbus_sumry
  uart_id: uart_bus

modbus_controller:
  - id: sumry_cp3200
    address: 0x01  # Modbus адреса інвертора
    modbus_id: modbus_sumry
    update_interval: 10s

uart:
  - id: uart_bus
    tx_pin: GPIO17
    rx_pin: GPIO16
    baud_rate: 9600
    stop_bits: 1
    parity: NONE

# BLE для JK-BMS
esp32_ble_tracker:

ble_client:
  - mac_address: "XX:XX:XX:XX:XX:XX"  # MAC JK-BMS
    id: jk_bms_client
```

### 3. Додавання сенсорів Modbus

Приклад читання напруги батареї:

```yaml
sensor:
  - platform: modbus_controller
    modbus_controller_id: sumry_cp3200
    name: "Sumry Battery Voltage"
    address: 0x0106
    register_type: holding
    value_type: U_WORD
    unit_of_measurement: "V"
    accuracy_decimals: 1
    filters:
      - multiply: 0.1
```

### 4. Прошивка ESP32

```bash
esphome run jk-sumry-inverter.yaml
```

Або через Docker:

```bash
docker run --rm -v "${PWD}":/config -it esphome/esphome run jk-sumry-inverter.yaml
```

### 5. Додавання в Home Assistant

Після першої прошивки пристрій з'явиться в **Settings → Devices & Services → ESPHome**.

---

## ⚙️ Налаштування Modbus для Sumry CP3200

### Основні регістри

| **Параметр**                  | **Адреса** | **Тип**   | **Множник** | **Одиниці** |
|-------------------------------|------------|-----------|-------------|-------------|
| Напруга батареї               | 0x0106     | holding   | 0.1         | V           |
| Струм батареї                 | 0x0107     | holding   | 0.01        | A           |
| SOC батареї                   | 0x0100     | holding   | 1           | %           |
| Напруга мережі (L1)           | 0x0213     | holding   | 0.1         | V           |
| Вихідна потужність            | 0x0213     | holding   | 1           | W           |
| Стан інвертора                | 0x0200     | holding   | —           | —           |

### Приклад читання SOC:

```yaml
sensor:
  - platform: modbus_controller
    modbus_controller_id: sumry_cp3200
    name: "Battery SOC"
    address: 0x0100
    register_type: holding
    value_type: U_WORD
    unit_of_measurement: "%"
    device_class: battery
```

---

## 📂 Файли

| Файл                        | Опис                                          |
|-----------------------------|-----------------------------------------------|
| `jk-sumry-inverter.yaml`    | Основний конфігураційний файл ESPHome        |
| `jk-sumry-inverter.yaml`    | Розширена конфігурація з усіма сенсорами     |
| `prepare_storage.sh`        | Скрипт підготовки накопичувача                |

---

## ⚠️ Дисклеймер

> Цей проєкт призначений для навчальних і експериментальних цілей. Автор не несе відповідальності за пошкодження обладнання, втрату даних або порушення гарантії. Використовуйте на свій ризик.

---

## 📜 Ліцензія

MIT License

---

**Автор**: Olegkg2018  
**Репозиторій**: [s905x3_armbian](https://github.com/Olegkg2018/s905x3_armbian)
