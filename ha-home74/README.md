# ha-home74 — дашборд «home74 PRO» и панель для ТВ

Дашборд Home Assistant (sections-вид, стеклянные карточки, анимации) и вспомогательные файлы. Сделан для домашней энергосистемы (инвертор + батарея JK-BMS + автомат ввода + отключения света), но структура переносима.

## Состав
| Путь | Что |
|---|---|
| `dashboards/dashboard_home74.json` | Конфиг дашборда (`.storage/lovelace.dashboard_home74`), 3 вида: Главная / Энергия / Погода. Номер счёта ДТЭК заменён на `ACCOUNT_ID`. |
| `www/dtek-schedule.html` | Лента графика отключений ДТЭК (24 плитки по часу, две половинки по 30 мин, маркер «сейчас», плашки «отключение идёт» / «ремонт» / «аварийный режим ЯСНО»). Читает данные из родителя (`parent…hass.states`), показывается в `iframe`-карточке. |
| `www/tv.html` | Лёгкая панель для ТВ/регистратора (см. `../ha-tv-render`). |
| `www/home74-bg.svg` | Анимированный фон дашборда. |
| `custom_components/dtek_schedule/` | Кастом-компонент: сенсор `sensor.dtek_schedule_today` (48 получасовых ячеек из публичного набора `Baskerville42/outage-data-ua`). |
| `pogoda/` | Скрипт, вырезающий блок погоды с pogoda.co.il в прозрачную страницу, и карточка для вкладки. |
| `config-snippets/` | Выдержки template-сенсоров (`grid_voltage_effective`, `grid_power_clamps`, `outage_soon`). |

## Требования (HACS)
mushroom, card-mod, clock-weather-card, dynamic-weather-card, sunsynk-power-flow-card, bms-battery-cells-card; интеграции `ha-dtek` (причины/ремонты), `yasno_outages`. Сущности подставьте свои.

## Установка дашборда
1. Скопируйте `www/*` в `<config>/www/`.
2. Остановите HA, положите JSON в `.storage/lovelace.dashboard_home74`, добавьте запись `dashboard-home74` в `.storage/lovelace_dashboards`, запустите HA. (Либо вставьте JSON вида в «сыром редакторе» нового дашборда.)
3. Замените `ACCOUNT_ID` на номер счёта вашей интеграции `ha-dtek` (в id сущностей `…dtek_account_ACCOUNT_ID_…`) и остальные entity_id на свои.

## Уроки по вёрстке (sections + card-mod)
- `grid_options.columns: 12` в секции на 2 колонки — это **половина** ширины; для полной нужно `"full"`.
- Markdown-карточка HA вырезает `style`; сложную разметку — отдельной страницей в `www/` в `iframe`-карточке (при правке менять `?v=N` в URL, иначе браузер держит кеш).
- iframe-страница: `color-scheme: dark` и собственная тёмная подложка; данные — из `parent.document.querySelector('home-assistant').hass.states`.
- Анимации — через `card_mod` (`:host{animation…}`; иконки mushroom: `mushroom-state-item$` → `mushroom-shape-icon$`), с `prefers-reduced-motion`.

## Про данные ДТЭК
Сайт и портал ДТЭК закрыты защитой от ботов (Incapsula) — обходить её не нужно и нельзя. Причины/ремонты берутся из `ha-dtek`, график — из публичного набора данных. Перезапуск HA сбрасывает паузу `ha-dtek` после блокировки: перезапускайте реже.
