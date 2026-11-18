"""Сенсор «таблица графика отключений на день» (очередь ДТЕК) с дублированием источников.

Основной источник — публичный набор данных на GitHub (Baskerville42/outage-data-ua, data/dnipro.json): там лежат
те же объекты `fact`/`preset`, что на странице ДТЕК, файл обновляется каждые ~5 минут; опрос раз в час.
Резервный источник — сама страница ДТЕК: подключается только если основной молчит дольше 3 часов, устарел или
не даёт таблицу на сегодня; опрашивается не чаще двух раз в сутки (00:10 и 12:10). Защиту портала компонент НЕ
обходит: при заглушке (Incapsula) резервные запросы приостанавливаются на 3 часа. User-Agent честный.
Последние данные сохраняются при перезапуске HA (RestoreEntity); панель при отсутствии данных берёт график YASNO.

configuration.yaml:
  sensor:
    - platform: dtek_schedule
      group: "GPV2.2"
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from . import schedule_logic as sl

_LOGGER = logging.getLogger(__name__)

CONF_GROUP, CONF_URL, CONF_FALLBACK, CONF_TIMES = "group", "url", "fallback_url", "fetch_times"
CONF_UA, CONF_INTERVAL = "user_agent", "interval_minutes"
DEFAULT_URL = "https://raw.githubusercontent.com/Baskerville42/outage-data-ua/main/data/dnipro.json"
DEFAULT_FALLBACK = "https://www.dtek-dnem.com.ua/ua/shutdowns"
DEFAULT_UA = "HomeAssistant-dtek_schedule (personal use)"
TICK = timedelta(minutes=20)
STARTUP_DELAY = timedelta(minutes=10)     # после запуска HA не обращаемся к источникам сразу (рядом стартуют другие интеграции)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_GROUP): cv.matches_regex(r"^GPV\d+\.\d+$"),
    vol.Optional(CONF_NAME, default="DTEK schedule today"): cv.string,
    vol.Optional(CONF_URL, default=DEFAULT_URL): cv.url,
    vol.Optional(CONF_FALLBACK, default=DEFAULT_FALLBACK): vol.Any("", cv.url),     # "" — резерв отключён
    vol.Optional(CONF_INTERVAL, default=60): vol.All(vol.Coerce(int), vol.Range(min=15, max=1440)),
    vol.Optional(CONF_TIMES): vol.All(cv.ensure_list, [cv.matches_regex(r"^\d{2}:\d{2}$")]),   # окна резервного источника
    vol.Optional(CONF_UA, default=DEFAULT_UA): cv.string,
})


def _slots(times):
    slots = []
    for t in times or []:
        h, m = (int(x) for x in t.split(":"))
        if not (0 <= h < 24 and 0 <= m < 60):
            raise vol.Invalid(f"некорректное время {t}")
        slots.append((h, m))
    return slots or list(sl.FALLBACK_SLOTS)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([DtekScheduleSensor(config, _slots(config.get(CONF_TIMES)))])


class _Source:
    """Состояние одного источника."""

    def __init__(self, name, url):
        self.name, self.url = name, url
        self.ok_at = self.attempt_at = self.paused_until = None
        self.failures = 0
        self.status = "no_data"


class DtekScheduleSensor(SensorEntity, RestoreEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:table-clock"
    _attr_native_unit_of_measurement = "h"

    def __init__(self, config, fallback_slots):
        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = f"dtek_schedule_{config[CONF_GROUP]}".lower().replace(".", "_")
        self._group, self._ua, self._interval, self._fb_slots = config[CONF_GROUP], config[CONF_UA], config[CONF_INTERVAL], fallback_slots
        self._primary = _Source("primary", config[CONF_URL])
        self._fallback = _Source("fallback", config[CONF_FALLBACK]) if config[CONF_FALLBACK] else None
        self._days: dict[str, list[int]] = {}
        self._updated = self._source_updated = None
        self._source_ok = None
        self._data_source = None

    # ---- восстановление и запуск ----
    async def async_added_to_hass(self):
        last = await self.async_get_last_state()
        if last is not None:
            a = last.attributes
            self._days = {k: v for k, v in (a.get("days") or {}).items() if isinstance(v, list) and len(v) == sl.CELLS}
            self._updated, self._source_updated = a.get("updated"), a.get("source_updated")
            self._primary.ok_at, self._data_source = _parse_dt(a.get("primary_ok_at")), a.get("source")
            if self._fallback:
                self._fallback.ok_at = _parse_dt(a.get("fallback_ok_at"))
            self._primary.status = "restored"                                            # старый статус не переносим (мог быть «challenge» с прошлого запуска)
        self.async_on_remove(async_track_time_interval(self.hass, self._tick, TICK))
        self.async_write_ha_state()                                                      # сразу показать восстановленные данные
        self.async_on_remove(async_call_later(self.hass, STARTUP_DELAY, self._tick))    # первый запрос — не раньше чем через 10 минут

    async def _tick(self, _now):
        now = dt_util.now()
        p = self._primary
        if sl.due_interval(now, p.ok_at, p.attempt_at, p.failures, self._interval):
            await self._fetch(p, now)
        fb = self._fallback
        if fb and sl.fallback_needed(now, p.ok_at, p.status, self._today() in self._days) and sl.due(
                now, fb.ok_at, fb.attempt_at, fb.failures, fb.paused_until, self._fb_slots):
            await self._fetch(fb, now)
        self.async_write_ha_state()

    # ---- запрос (один GET за попытку, без обхода защиты) ----
    async def _fetch(self, src: _Source, now: datetime):
        src.attempt_at = now
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(src.url, headers={"User-Agent": self._ua, "Accept": "application/json, text/html;q=0.8"},
                                   timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise aiohttp.ClientError(f"HTTP {resp.status}")
                text = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            src.failures += 1
            src.status = "error"
            _LOGGER.warning("DTEK schedule [%s]: запрос не удался (%s); повтор позже", src.name, type(err).__name__)
            return
        res = sl.parse_page(text, self._group)
        src.status = res["status"]
        if res["status"] == "ok":
            src.ok_at, src.failures = now, 0
            stale = bool(res["source_updated"]) and (res["source_ok"] is False or sl.is_stale(res["source_updated"], now))
            if stale:
                src.status = "stale"
            self._apply(src, res, now, stale)
        elif res["status"] == "challenge":
            src.paused_until = now + sl.CHALLENGE_PAUSE
            src.failures += 1
            _LOGGER.warning("DTEK schedule [%s]: источник вернул страницу защиты, запросы приостановлены на %s ч",
                            src.name, sl.CHALLENGE_PAUSE.total_seconds() // 3600)
        else:
            src.failures += 1
            _LOGGER.warning("DTEK schedule [%s]: в ответе нет таблицы для %s (%s)", src.name, self._group, res["status"])

    def _apply(self, src, res, now, stale):
        # устаревшие данные основного источника не затирают свежие данные резервного
        other = self._fallback if src is self._primary else self._primary
        if stale and other and other.ok_at and now - other.ok_at < sl.FALLBACK_AFTER * 4 and other.status == "ok":
            return
        self._days, self._updated = res["days"], res["updated"]
        self._source_updated, self._source_ok, self._data_source = res["source_updated"], res["source_ok"], src.name
        _LOGGER.debug("DTEK schedule [%s]: таблица обновлена (%s)", src.name, ", ".join(sorted(res["days"])))

    # ---- состояние ----
    def _today(self):
        return dt_util.now().date().isoformat()

    @property
    def native_value(self):
        cells = self._days.get(self._today())
        return sl.outage_hours(cells) if cells else None

    @property
    def extra_state_attributes(self):
        today = self._today()
        tomorrow = (dt_util.now() + timedelta(days=1)).date().isoformat()
        cells = self._days.get(today)
        keep = sorted(self._days)[-3:]                     # хранить не больше трёх суток
        iso = lambda d: d.isoformat() if d else None
        return {
            "group": self._group, "date": today if cells else None, "cells": cells,
            "windows": [{"start": a, "end": b} for a, b in sl.windows(cells)] if cells else [],
            "tomorrow_date": tomorrow if self._days.get(tomorrow) else None, "tomorrow_cells": self._days.get(tomorrow),
            "days": {k: self._days[k] for k in keep}, "updated": self._updated,
            "source": self._data_source, "source_updated": self._source_updated, "source_ok": self._source_ok,
            "status": self._primary.status, "fallback_status": self._fallback.status if self._fallback else "disabled",
            "primary_ok_at": iso(self._primary.ok_at), "fallback_ok_at": iso(self._fallback.ok_at) if self._fallback else None,
            "fetched_at": iso(self._primary.ok_at),
            "cell_legend": "0 свет есть, 1 отключение, 2 возможно; 48 ячеек по 30 мин с 00:00",
        }


def _parse_dt(value):
    try:
        return dt_util.parse_datetime(value) if value else None
    except (TypeError, ValueError):
        return None
