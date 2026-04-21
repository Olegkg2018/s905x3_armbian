--- README.md 


+++ README.md 
# s905x3_armbian - Home Assistant Core на TV-приставке

[![Platform](https://img.shields.io/badge/platform-ARM64-blue.svg)](https://www.armbian.com/)
[![Device](https://img.shields.io/badge/device-S905X3-orange.svg)](https://en.wikipedia.org/wiki/Amlogic)
[![RAM](https://img.shields.io/badge/RAM-4GB-green.svg)]()
[![Storage](https://img.shields.io/badge/Storage-32GB-green.svg)]()
[![OS](https://img.shields.io/badge/OS-Armbian-red.svg)](https://www.armbian.com/)
[![Software](https://img.shields.io/badge/software-Home%20Assistant%20Core-purple.svg)](https://www.home-assistant.io/)

## 📋 Описание проекта

Проект посвящен развертыванию **Home Assistant Core** на TV-приставке с процессором **Amlogic S905X3** (4GB RAM / 32GB Storage) под управлением операционной системы **Armbian**.

Данное решение превращает обычную ТВ-приставку в полноценный умный дом-сервер с минимальными затратами энергии и средств.

## 🔧 Технические характеристики

### Оборудование
- **Процессор**: Amlogic S905X3 (Quad-core ARM Cortex-A55)
- **GPU**: Mali-G31 MP2
- **Оперативная память**: 4GB DDR4
- **Встроенная память**: 32GB eMMC
- **Сеть**: Gigabit Ethernet, Wi-Fi 802.11ac, Bluetooth 4.2
- **Порты**: USB 3.0, USB 2.0, HDMI 2.1, AV

### Программное обеспечение
- **ОС**: Armbian (Linux на базе Debian/Ubuntu)
- **Платформа умного дома**: Home Assistant Core
- **Архитектура**: ARM64 (aarch64)

## ✨ Преимущества решения

- 💡 **Энергоэффективность** - потребление всего 5-10Вт
- 💰 **Экономичность** - использование доступного оборудования
- 🔇 **Бесшумность** - пассивное охлаждение
- 📦 **Компактность** - минимальное занимаемое пространство
- 🚀 **Производительность** - 4GB RAM достаточно для большинства сценариев умного дома

## 📖 Содержание документации

- [Установка Armbian](docs/installation.md)
- [Настройка Home Assistant Core](docs/homeassistant-setup.md)
- [Оптимизация системы](docs/optimization.md)
- [Резервное копирование](docs/backup.md)
- [Частые проблемы и решения](docs/troubleshooting.md)

## 🚀 Быстрый старт

1. Скачайте образ Armbian для S905X3
2. Запишите образ на microSD карту или установите на eMMC
3. Настройте сеть и подключитесь по SSH
4. Установите зависимости для Home Assistant
5. Разверните Home Assistant Core
6. Настройте интеграции и автоматизации

## 📁 Структура репозитория

```
s905x3_armbian/
├── docs/                    # Документация
│   ├── installation.md      # Установка Armbian
│   ├── homeassistant-setup.md # Настройка HA
│   ├── optimization.md      # Оптимизация
│   ├── backup.md            # Резервное копирование
│   └── troubleshooting.md   # Решение проблем
├── scripts/                 # Скрипты автоматизации
├── configs/                 # Примеры конфигураций
├── docker/                  # Docker конфигурации (опционально)
└── README.md               # Этот файл
```

## 🔗 Полезные ссылки

- [Официальный сайт Armbian](https://www.armbian.com/)
- [Документация Home Assistant](https://www.home-assistant.io/docs/)
- [Форум Armbian](https://forum.armbian.com/)
- [Сообщество Home Assistant](https://community.home-assistant.io/)

## 🤝 Вклад в проект

Если вы используете данную конфигурацию или у вас есть полезные дополнения:

1. Создайте форк репозитория
2. Создайте ветку (`git checkout -b feature/AmazingFeature`)
3. Закоммитьте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. Подробнее см. в файле [LICENSE](LICENSE).

## ⚠️ Отказ от ответственности

Использование данного руководства осуществляется на ваш страх и риск. Автор не несет ответственности за возможные повреждения оборудования или потерю данных. Всегда создавайте резервные копии перед внесением изменений.

## 📞 Контакты и поддержка

- Вопросы задавайте в разделе [Issues](https://github.com/yourusername/s905x3_armbian/issues)
- Обсуждение в [Discussions](https://github.com/yourusername/s905x3_armbian/discussions)

---

**Made with ❤️ for the Home Assistant Community**


Полезное
Технічна інформація з інтеграціі інверторів, mppt та BMS до ESPHome:
PowMr (RS232) - github.com/odya/esphome-powmr-hybrid-inverter 
Easun, ISolar, Anenji (RS232)  - github.com/syssi/esphome-smg-ii
Voltronic  - github.com/syssi/esphome-votronic
Victron - github.com/krahabb/esphome-victron-vedirect
PipSolar (RS232) - github.com/syssi/esphome-pipsolar
APC UPS (RS232) - github.com/syssi/esphome-apc-ups
Must (RS485) - github.com/vladyspavlov/esphome-must-inverter
Growatt (RS485) - github.com/klatremis/esphome-for-growatt
Deye (RS485) - github.com/Lewa-Reka/esphome-deye-inverter
Deye (RS485) - github.com/klatremis/esphome-for-deye
Solis (RS485) - github.com/hn/ginlong-solis
SRNE (RS485) - github.com/topics/srne
PACE BMS (RS485) - github.com/syssi/esphome-pace-bms
Epever MPPT (RS485) - devices.esphome.io/devices/epever_mptt_tracer_an
JK-BMS (UART-TTL or BLE) - github.com/syssi/esphome-jk-bms
Daly-BMS (UART) - esphome.io/components/sensor/daly_bms.html
Daly-BMS (BLE) - github.com/syssi/esphome-daly-bms
Налаштування ESPHome - dou.ua/forums
Modbus Controller - esphome.io
Інформація з підключення різних модулів / сенсорів до ESPHome - github.com/esphome/esphome-docs
Ethernet LAN8720 - github.com/flusflas/esp32-ethernet
Плата адаптера модуля ESP32 дозволяє підключити будь який пристрій з інтерфейсами: RS232, RS485, UART.
Приклади конфігурацій для ESPHome:
SMG II + PZEM + JK-BMS - завантажити
PowMr + PZEM + JK-BMS - завантажити
Easun SMH III - завантажити
JK-BMS  4S 12V - завантажити
Epever Tracer-AN - завантажити

*Последнее обновление: $(date +%Y-%m-%d)*
