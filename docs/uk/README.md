# s905x3_armbian — Home Assistant Core на TV-приставці

---

## 🌐 Language / Мова / Мова

**[English](../en/README.md)** | **[Русский](../../README.md)** | **[Українська](README.md)**

> 📚 Документація доступна трьома мовами:
>
> * **Русский** — основна документація (README.md, README_*.md)
> * **Українська** — повний переклад в каталозі `docs/uk/`
> * **English** — coming soon in `docs/en/`

### 📝 Доступні інструкції українською

* 🏠 [Встановлення Home Assistant](README_homeassistent.md)
* 🌐 [Cloudflare Tunnel для віддаленого доступу](README_cloudflare_tunnel.md)
* 📡 [ESPHome — встановлення та налаштування](README_esphome.md)
* 🔋 [ESP32 JK-BMS & Sumry Gateway](README_esp32.md)
* 📶 [Налаштування Wi-Fi точки доступу](Add_AP.md)
* 🛠 [Діагностика та вирішення проблем](troubleshooting.md)
* 💾 [Встановлення Armbian на eMMC](README_install_armbian.md)

---

## 📋 Опис проєкту

Проєкт присвячений розгортанню **Home Assistant Core** на TV-приставці з процесором **Amlogic S905X3** (4 GB RAM / 32–64 GB eMMC) під управлінням **Armbian**.

Рішення перетворює звичайну ТВ-приставку на повноцінний сервер розумного дому з мінімальними витратами енергії та коштів.

## 🔧 Технічні характеристики

### Обладнання

* **Процесор**: Amlogic S905X3 (Quad-core ARM Cortex-A55, 1.9 GHz)
* **GPU**: Mali-G31 MP2
* **Оперативна пам'ять**: 4 GB DDR4
* **Вбудована пам'ять**: 32–64 GB eMMC
* **Мережа**: Gigabit Ethernet, Wi-Fi 802.11ac, Bluetooth 4.2
* **Порти**: USB 3.0 × 1, USB 2.0 × 1, HDMI 2.1, AV

### Програмне забезпечення

* **ОС**: Armbian (ядро 5.10 / 5.15 LTS, Debian/Ubuntu base)
* **Платформа розумного дому**: Home Assistant Core (Python venv)
* **Архітектура**: ARM64 (aarch64)

## ✨ Переваги рішення

* 💡 **Енергоефективність** — споживання ~2–10 Вт
* 💰 **Економічність** — доступне б/в обладнання
* 🔇 **Безшумність** — пасивне охолодження
* 📦 **Компактність** — мінімальний форм-фактор
* 🚀 **Продуктивність** — 4 GB RAM достатньо для десятків інтеграцій HA

## 📁 Структура репозиторію

```
s905x3_armbian/
├── README.md                      # Головна документація (цей файл)
├── README_install_armbian.md      # Встановлення Armbian на eMMC (з зовнішнім диском)
├── README_homeassistent.md        # Встановлення Home Assistant Core
├── README_esp32.md                # ESP32-шлюз для JK-BMS і Sumry-інвертора
├── Add_AP.md                      # Налаштування Wi-Fi точки доступу (hostapd + dnsmasq)
├── troubleshooting.md             # Діагностика та вирішення типових проблем
├── install_to_emmc.sh             # Скрипт встановлення Armbian на eMMC
├── prepare_storage.sh             # Скрипт налаштування зовнішнього USB-диска
└── jk-sumry-inverter.yaml         # Конфігурація ESPHome (JK-BMS + Sumry CP3200)
```

## 🚀 Швидкий старт

1. Завантажте образ Armbian для S905X3 → [ophub/amlogic-s9xxx-armbian](https://github.com/ophub/amlogic-s9xxx-armbian/releases)
2. Запишіть образ на USB-флешку (BalenaEtcher)
3. Завантажтеся з флешки (утримуйте Reset ~5 сек при подачі живлення)
4. Підключіться по SSH та виконайте `armbian-install` для запису на eMMC
5. Налаштуйте мережу, встановіть залежності Home Assistant Core
6. (Опціонально) Підключіть зовнішній USB-диск та запустіть `prepare_storage.sh`

Докладні інструкції — у файлах документації:

| Тема | Файл |
|---|---|
| Встановлення Armbian + зовнішній диск | [README_install_armbian.md](README_install_armbian.md) |
| Встановлення Home Assistant Core | [README_homeassistent.md](README_homeassistent.md) |
| ESP32-шлюз (JK-BMS + інвертор) | [README_esp32.md](README_esp32.md) |
| Wi-Fi точка доступу | [Add_AP.md](Add_AP.md) |
| Діагностика проблем | [troubleshooting.md](troubleshooting.md) |

## 🔌 Інтеграції інверторів та BMS через ESPHome

Нижче наведені посилання на компоненти ESPHome для підключення різних пристроїв:

| Пристрій | Інтерфейс | Посилання |
|---|---|---|
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

**Корисні ресурси ESPHome:**

* [Modbus Controller](https://esphome.io/components/modbus_controller/)
* [Документація по всіх компонентах](https://github.com/esphome/esphome-docs)
* [Ethernet LAN8720 для ESP32](https://github.com/flusflas/esp32-ethernet)
* [Налаштування ESPHome (стаття)](https://dou.ua/forums/topic/42488/)

**Готові приклади конфігурацій:**

* [SMG II + PZEM + JK-BMS](https://ledinstal.com.ua/diy_files/smg-ii_v1.2.rar)
* [PowMr + PZEM + JK-BMS](https://ledinstal.com.ua/diy_files/powmr-test.rar)
* [Easun SMH III](https://ledinstal.com.ua/diy_files/smh-iii.rar)
* [JK-BMS 4S 12V](https://ledinstal.com.ua/diy_files/jk-bms_4s.rar)
* [Epever Tracer-AN](https://ledinstal.com.ua/diy_files/epever.rar)

## 🔗 Корисні посилання

* [Офіційний сайт Armbian](https://www.armbian.com/)
* [Образи для S905X3 (ophub)](https://github.com/ophub/amlogic-s9xxx-armbian/releases)
* [Документація Home Assistant](https://www.home-assistant.io/docs/)
* [Форум Armbian](https://forum.armbian.com/)
* [Спільнота Home Assistant](https://community.home-assistant.io/)

## 🤝 Внесок в проєкт

Якщо ви використовуєте дану конфігурацію або є корисні доповнення:

1. Створіть форк репозиторію
2. Створіть гілку (`git checkout -b feature/MyFeature`)
3. Закоммітьте зміни (`git commit -m 'Add MyFeature'`)
4. Відправте гілку (`git push origin feature/MyFeature`)
5. Відкрийте Pull Request

## 📝 Ліцензія

Проєкт розповсюджується під ліцензією MIT.

## ⚠️ Відмова від відповідальності

Використання даного посібника здійснюється на ваш страх і ризик. Автор не несе відповідальності за можливі пошкодження обладнання або втрату даних. Завжди створюйте резервні копії перед змінами.

## 📞 Контакти та підтримка

* Питання — в розділі [Issues](https://github.com/Olegkg2018/s905x3_armbian/issues)
* Обговорення — в [Discussions](https://github.com/Olegkg2018/s905x3_armbian/discussions)

**Останнє оновлення**: 2026-05-07
