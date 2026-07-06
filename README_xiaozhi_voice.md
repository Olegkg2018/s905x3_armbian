# 🎙️ Умная колонка Xiaozhi AI Voice — альтернатива "Алисе" для Home Assistant

Превращаем Home Assistant в интеллектуального голосового помощника, который понимает состояние сенсоров вашего дома и имеет доступ к интернету. Полный аналог популярных колонок, но с вашей приватной экосистемой и поддержкой русского и украинского языков.

## 🚀 Основные возможности

* **Голосовой диалог**: Естественное общение (STT/TTS) на русском и украинском языках.
* **Интеграция с HA**: Помощник знает всё о вашем доме (температуру, состояние света, BMS и т.д.) и может управлять устройствами.
* **Доступ к знаниям**: Получение данных из интернета (погода, новости, общие вопросы).
* **Приватность**: Вы сами управляете сервисами распознавания и синтеза речи.

## 🛠 Оборудование

Для проекта используется модуль:
**ESP32-S3 N16R8 Development Board Xiaozhi AI Voice Dialogue Robot Module**
* **Дисплей**: 0.96 inch OLED
* **Интерфейс**: Type-C
* **Особенность**: Встроенный микрофон и аудио-выход.

🛒 **Где купить**: [AliExpress](https://www.aliexpress.com/item/1005009398980859.html)
📖 **Подробное описание на 4PDA**: [Тема Xiaozhi на 4PDA](https://4pda.to/forum/index.php?showtopic=1117943)

## 📦 Программное обеспечение и прошивка

Вы можете выбрать один из проектов для реализации:

1. **xiaozhi-esp32 (официальные релизы)**: [GitHub Releases](https://github.com/78/xiaozhi-esp32/releases)
2. **XIAOZHI-AI-Voice-Assistant**: [GitHub Guide](https://github.com/techiesms/XIAOZHI-AI-Voice-Assistant/blob/main/README.md)
3. **Xiaozhi ESPHome (Рекомендуется)**: [GitHub Repository](https://github.com/RealDeco/xiaozhi-esphome)

### ⚙️ Конфигурация для данной платы
Конкретно для версии платы **N16R8** (Breadboard Mini) идеально подходит этот YAML-файл:
📄 [breadboard_mini.yaml](https://github.com/RealDeco/xiaozhi-esphome/blob/main/devices/Breadboard/breadboard_mini.yaml)

## 🔊 Модернизация (Hardware Mod)

Для получения качественного звука рекомендуется **вставить устройство в обычную компьютерную колонку**:
1. Разберите колонку.
2. Подключите аудио-выход модуля к усилителю колонки.
3. Выведите OLED-экран и микрофон на корпус.
4. Питание можно взять напрямую от внутреннего БП колонки через стабилизатор.

Это превратит дешёвый модуль в полноценную акустическую систему с ИИ-помощником.

---

## 💻 Локальный сервер умной колонки «Алиса» на S905x3 (Armbian)

Если вы хотите развернуть свой собственный приватный сервер на S905x3 (Armbian), который будет полностью заменять оригинальное китайское облако, в репозитории подготовлена сборка в папке [xiaozhi-server/](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/).

### Возможности локальной сборки:
* **Адаптация под «Алису»**: Исключены любые иероглифы в дикторской речи и подсказках. Создан чистый шаблон системного промпта [agent-base-prompt-ru.txt](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/agent-base-prompt-ru.txt) и русифицирован плеер.
* **Новости Украины**: Разработан плагин [get_news_ru.py](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/plugins_func/functions/get_news_ru.py), считывающий актуальные новости через RSS-ленту «Украинской Правды».
* **Погода без API-ключей**: Плагин [get_weather_ru.py](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/plugins_func/functions/get_weather_ru.py) автоматически делает геокодинг любого города и получает погоду с Open-Meteo.
* **Свободный поиск в Google**: Плагин [web_search.py](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/plugins_func/functions/web_search.py) напрямую парсит результаты google.com на русском языке без ключей API.
* **Умное проигрывание музыки из интернета**: Плагин [play_music.py](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/plugins_func/functions/play_music.py) ищет песни локально, а если их нет — озвучивает статус, находит и скачивает трек с YouTube (через `yt-dlp`), конвертирует в MP3 с помощью `ffmpeg` и стримит в динамик колонки. Поддерживает произвольные запросы (например, *«включи спокойную музыку»*, *«песню Алсу Иногда»* и т.д.).

### Быстрый запуск на S905x3:
1. Зарегистрируйте ключи API: Groq ASR (бесплатно на console.groq.com) и DeepSeek LLM.
2. Пропишите ключи в файле [xiaozhi-server/data/.config.yaml](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/data/.config.yaml).
3. Запустите через Docker Compose:
   ```bash
   cd xiaozhi-server
   docker-compose up -d
   ```

---

## 📂 Файлы в репозитории
* `README_xiaozhi_voice.md` — эта инструкция (RU).
* [docs/uk/README_xiaozhi_voice.md](docs/uk/README_xiaozhi_voice.md) — українська версія.
* [xiaozhi-server/](file:///home/oleg/s905x/s905x3_armbian/xiaozhi-server/) — конфигурации и плагины локального сервера «Алисы» для S905x3.

---
**Автор проекта**: Olegkg2018
**Поддержка**: [Issues](https://github.com/Olegkg2018/s905x3_armbian/issues)
