# s905x3_armbian — Home Assistant Core на TV-приставке

---

## 🌐 Language / Мова / Мова

**[English](docs/en/README.md)** | **[Русский](README.md)** | **[Українська](docs/uk/README.md)**

> 📚 Документация доступна на трёх языках:
>
> * **Русский** — основная документация (README.md, README_*.md)
> * **Українська** — повний переклад в каталозі `docs/uk/`
> * **English** — coming soon in `docs/en/`

### 📝 Доступні інструкції українською

* 🏠 [Встановлення Home Assistant](docs/uk/README_homeassistent.md)
* 🌐 [Cloudflare Tunnel для віддаленого доступу](docs/uk/README_cloudflare_tunnel.md)
* 📡 [ESPHome — встановлення та налаштування](docs/uk/README_esphome.md)
* 🎙️ [Розумна колонка Xiaozhi AI Voice](docs/uk/README_xiaozhi_voice.md)

---

## 📋 Описание проекта

Проект посвящён развёртыванию **Home Assistant Core** на TV-приставке с процессором **Amlogic S905X3** (4 GB RAM / 32–64 GB eMMC) под управлением **Armbian**.

Решение превращает обычную ТВ-приставку в полноценный сервер умного дома с минимальными затратами энергии и средств.

## 🔧 Технические характеристики

### Оборудование

* **Процессор**: Amlogic S905X3 (Quad-core ARM Cortex-A55, 1.9 GHz)
* **GPU**: Mali-G31 MP2
* **Оперативная память**: 4 GB DDR4
* **Встроенная память**: 32–64 GB eMMC
* **Сеть**: Gigabit Ethernet, Wi-Fi 802.11ac, Bluetooth 4.2
* **Порты**: USB 3.0 × 1, USB 2.0 × 1, HDMI 2.1, AV

### Программное обеспечение

* **ОС**: Armbian (ядро 5.10 / 5.15 LTS, Debian/Ubuntu base)
* **Платформа умного дома**: Home Assistant Core (Python venv)
* **Архитектура**: ARM64 (aarch64)

## ✨ Преимущества решения

* 💡 **Энергоэффективность** — потребление ~2–10 Вт
* 💰 **Экономичность** — доступное б/у оборудование
* 🔇 **Бесшумность** — пассивное охлаждение
* 📦 **Компактность** — минимальный форм-фактор
* 🚀 **Производительность** — 4 GB RAM достаточно для десятков интеграций HA

## 📁 Структура репозитория

```
s905x3_armbian/
├── README.md                      # Главная документация (этот файл)
├── README_install_armbian.md      # Установка Armbian на eMMC
├── README_homeassistent.md        # Установка Home Assistant Core
├── README_esp32.md                # ESP32-шлюз для JK-BMS и Sumry-инвертора
├── README_xiaozhi_voice.md        # Голосовой помощник Xiaozhi AI (аналог Алисы)
├── Add_AP.md                      # Настройка Wi-Fi точки доступа
├── troubleshooting.md             # Диагностика и решение типовых проблем
├── install_to_emmc.sh             # Скрипт установки Armbian на eMMC
├── prepare_storage.sh             # Скрипт настройки внешнего USB-диска
└── jk-sumry-inverter.yaml         # Конфигурация ESPHome
```

## 🎙️ Голосовой помощник (Аналог Алисы)

Проект поддерживает создание умной колонки на базе модуля **Xiaozhi AI Voice** (ESP32-S3). Помощник понимает состояние ваших сенсоров в Home Assistant и может отвечать на вопросы из интернета на русском и украинском языках.

* 📖 **Инструкция**: [README_xiaozhi_voice.md](README_xiaozhi_voice.md)
* 🛒 **Купить модуль**: [AliExpress](https://www.aliexpress.com/item/1005009398980859.html)

## 🚀 Быстрый старт

1. Скачайте образ Armbian для S905X3 → [ophub/amlogic-s9xxx-armbian](https://github.com/ophub/amlogic-s9xxx-armbian/releases)
2. Запишите образ на USB-флешку (BalenaEtcher)
3. Загрузитесь с флешки (удерживайте Reset ~5 сек при подаче питания)
4. Подключитесь по SSH и выполните `armbian-install` для записи на eMMC
5. Настройте сеть, установите зависимости Home Assistant Core

Подробные инструкции — в файлах документации:

| Тема | Файл |
|---|---|
| Установка Armbian | [README_install_armbian.md](README_install_armbian.md) |
| Установка Home Assistant | [README_homeassistent.md](README_homeassistent.md) |
| Голосовой помощник Xiaozhi | [README_xiaozhi_voice.md](README_xiaozhi_voice.md) |
| ESP32-шлюз (BMS) | [README_esp32.md](README_esp32.md) |
| Wi-Fi точка доступа | [Add_AP.md](Add_AP.md) |

## 🔌 Интеграции через ESPHome

* [Modbus Controller](https://esphome.io/components/modbus_controller/)
* [Настройка ESPHome (статья на DOU)](https://dou.ua/forums/topic/42488/)

## 🔗 Полезные ссылки

* [Официальный сайт Armbian](https://www.armbian.com/)
* [Документация Home Assistant](https://www.home-assistant.io/docs/)

---
**Последнее обновление**: 2026-05-07
