# s905x3_armbian — Home Assistant Core на TV-приставке

[![Platform](https://img.shields.io/badge/platform-ARM64-blue.svg)](https://www.armbian.com/)
[![Device](https://img.shields.io/badge/device-S905X3-orange.svg)](https://en.wikipedia.org/wiki/Amlogic)
[![RAM](https://img.shields.io/badge/RAM-4GB-green.svg)]()
[![Storage](https://img.shields.io/badge/Storage-32–64GB-green.svg)]()
[![OS](https://img.shields.io/badge/OS-Armbian-red.svg)](https://www.armbian.com/)
[![Software](https://img.shields.io/badge/software-Home%20Assistant%20Core-purple.svg)](https://www.home-assistant.io/)

## 📋 Описание проекта

Проект посвящён развёртыванию **Home Assistant Core** на TV-приставке с процессором **Amlogic S905X3**
(4 GB RAM / 32–64 GB eMMC) под управлением **Armbian**.

Решение превращает обычную ТВ-приставку в полноценный сервер умного дома с минимальными затратами
энергии и средств.

## 🔧 Технические характеристики

### Оборудование
- **Процессор**: Amlogic S905X3 (Quad-core ARM Cortex-A55, 1.9 GHz)
- **GPU**: Mali-G31 MP2
- **Оперативная память**: 4 GB DDR4
- **Встроенная память**: 32–64 GB eMMC
- **Сеть**: Gigabit Ethernet, Wi-Fi 802.11ac, Bluetooth 4.2
- **Порты**: USB 3.0 × 1, USB 2.0 × 1, HDMI 2.1, AV

### Программное обеспечение
- **ОС**: Armbian (ядро 5.10 / 5.15 LTS, Debian/Ubuntu base)
- **Платформа умного дома**: Home Assistant Core (Python venv)
- **Архитектура**: ARM64 (aarch64)

## ✨ Преимущества решения

- 💡 **Энергоэффективность** — потребление ~2–10 Вт
- 💰 **Экономичность** — доступное б/у оборудование
- 🔇 **Бесшумность** — пассивное охлаждение
- 📦 **Компактность** — минимальный форм-фактор
- 🚀 **Производительность** — 4 GB RAM достаточно для десятков интеграций HA

## 📁 Структура репозитория

```
s905x3_armbian/
├── README.md                    # Главная документация (этот файл)
├── README_install_armbian.md    # Установка Armbian на eMMC (с внешним диском)
├── README_homeassistent.md      # Установка Home Assistant Core
├── README_esp32.md              # ESP32-шлюз для JK-BMS и Sumry-инвертора
├── Add_AP.md                    # Настройка Wi-Fi точки доступа (hostapd + dnsmasq)
├── troubleshooting.md           # Диагностика и решение типовых проблем
├── install_to_emmc.sh           # Скрипт установки Armbian на eMMC
├── prepare_storage.sh           # Скрипт настройки внешнего USB-диска
└── jk-sumry-inverter.yaml       # Конфигурация ESPHome (JK-BMS + Sumry CP3200)
```

## 🚀 Быстрый старт

1. Скачайте образ Armbian для S905X3 → [ophub/amlogic-s9xxx-armbian](https://github.com/ophub/amlogic-s9xxx-armbian/releases)
2. Запишите образ на USB-флешку (BalenaEtcher)
3. Загрузитесь с флешки (удерживайте Reset ~5 сек при подаче питания)
4. Подключитесь по SSH и выполните `armbian-install` для записи на eMMC
5. Настройте сеть, установите зависимости Home Assistant Core
6. (Опционально) Подключите внешний USB-диск и запустите `prepare_storage.sh`

Подробные инструкции — в файлах документации:

| Тема | Файл |
|------|------|
| Установка Armbian + внешний диск | [README_install_armbian.md](README_install_armbian.md) |
| Установка Home Assistant Core | [README_homeassistent.md](README_homeassistent.md) |
| ESP32-шлюз (JK-BMS + инвертор) | [README_esp32.md](README_esp32.md) |
| Wi-Fi точка доступа | [Add_AP.md](Add_AP.md) |
| Диагностика проблем | [troubleshooting.md](troubleshooting.md) |

## 🔌 Интеграции инверторов и BMS через ESPHome

Ниже приведены ссылки на компоненты ESPHome для подключения различных устройств:

| Устройство | Интерфейс | Ссылка |
|-----------|-----------|--------|
| PowMr | RS232 | [esphome-powmr-hybrid-inverter](https://github.com/odya/esphome-powmr-hybrid-inverter) |
| Easun / ISolar / Anenji | RS232 | [esphome-smg-ii](https://github.com/syssi/esphome-smg-ii) |
| Voltronic | RS232 | [esphome-votronic](https://github.com/syssi/esphome-votronic) |
| Victron | VE.Direct | [esphome-victron-vedirect](https://github.com/krahabb/esphome-victron-vedirect) |
| PipSolar | RS232 | [esphome-pipsolar](https://github.com/syssi/esphome-pipsolar) |
| APC UPS | RS232 | [esphome-apc-ups](https://github.com/syssi/esphome-apc-ups) |
| Must | RS485 | [esphome-must-inverter](https://github.com/vladyspavlov/esphome-must-inverter) |
| Growatt | RS485 | [esphome-for-growatt](https://github.com/klatremis/esphome-for-growatt) |
| Deye | RS485 | [esphome-deye-inverter](https://github.com/Lewa-Reka/esphome-deye-inverter) |
| Solis / Ginlong | RS485 | [ginlong-solis](https://github.com/hn/ginlong-solis) |
| SRNE | RS485 | [topics/srne](https://github.com/topics/srne) |
| PACE BMS | RS485 | [esphome-pace-bms](https://github.com/syssi/esphome-pace-bms) |
| Epever MPPT | RS485 | [esphome devices](https://devices.esphome.io/devices/epever_mptt_tracer_an) |
| JK-BMS | UART-TTL / BLE | [esphome-jk-bms](https://github.com/syssi/esphome-jk-bms) |
| Daly-BMS | UART | [esphome daly_bms](https://esphome.io/components/sensor/daly_bms.html) |
| Daly-BMS | BLE | [esphome-daly-bms](https://github.com/syssi/esphome-daly-bms) |

**Полезные ресурсы ESPHome:**
- [Modbus Controller](https://esphome.io/components/modbus_controller/)
- [Документация по всем компонентам](https://github.com/esphome/esphome-docs)
- [Ethernet LAN8720 для ESP32](https://github.com/flusflas/esp32-ethernet)
- [Настройка ESPHome (статья)](https://dou.ua/forums/topic/42488/)

**Готовые примеры конфигураций:**
- [SMG II + PZEM + JK-BMS](https://ledinstal.com.ua/diy_files/smg-ii_v1.2.rar)
- [PowMr + PZEM + JK-BMS](https://ledinstal.com.ua/diy_files/powmr-test.rar)
- [Easun SMH III](https://ledinstal.com.ua/diy_files/smh-iii.rar)
- [JK-BMS 4S 12V](https://ledinstal.com.ua/diy_files/jk-bms_4s.rar)
- [Epever Tracer-AN](https://ledinstal.com.ua/diy_files/epever.rar)

## 🔗 Полезные ссылки

- [Официальный сайт Armbian](https://www.armbian.com/)
- [Образы для S905X3 (ophub)](https://github.com/ophub/amlogic-s9xxx-armbian/releases)
- [Документация Home Assistant](https://www.home-assistant.io/docs/)
- [Форум Armbian](https://forum.armbian.com/)
- [Сообщество Home Assistant](https://community.home-assistant.io/)

## 🤝 Вклад в проект

Если вы используете данную конфигурацию или есть полезные дополнения:

1. Создайте форк репозитория
2. Создайте ветку (`git checkout -b feature/MyFeature`)
3. Закоммитьте изменения (`git commit -m 'Add MyFeature'`)
4. Отправьте ветку (`git push origin feature/MyFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Проект распространяется под лицензией MIT.

## ⚠️ Отказ от ответственности

Использование данного руководства осуществляется на ваш страх и риск. Автор не несёт ответственности за
возможные повреждения оборудования или потерю данных. Всегда создавайте резервные копии перед изменениями.

## 📞 Контакты и поддержка

- Вопросы — в разделе [Issues](https://github.com/Olegkg2018/s905x3_armbian/issues)
- Обсуждение — в [Discussions](https://github.com/Olegkg2018/s905x3_armbian/discussions)

---
*Последнее обновление: 2026-05-07*
