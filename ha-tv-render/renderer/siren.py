"""Воздушная тревога по региону из публичного API siren.pp.ua (обёртка ukrainealarm, без токена).

Только стандартная библиотека; используется боевым run.py (.130) и рендерером pi/panel.py.
Регион 279 — «м. Кривий Ріг та Криворізька територіальна громада» (тревога района наследуется).
Показываем только воздушную тревогу (type AIR): red / yellow; AIR без уровня считаем красной.
"""
import json
import urllib.error
import urllib.request

BASE = "https://siren.pp.ua/api/v3/alerts/"
DEFAULT_REGION = "279"
TIMEOUT = 8
MAX_BYTES = 1_000_000
STALE_AFTER = 300           # c: данные старше 5 минут считаем неизвестными (слово не показываем)
LEVELS = ("red", "yellow")


class SirenError(Exception):
    """Источник недоступен или вернул неожиданный ответ (текст безопасен для логов)."""


def validate_region(region):
    r = str(region).strip()
    if not r.isdigit() or len(r) > 6:
        raise ValueError("ALERT_REGION должен быть числовым id региона, например 279")
    return r


def parse_level(data):
    """JSON ответа -> 'red' | 'yellow' | '' (нет воздушной тревоги). Мусор -> SirenError."""
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise SirenError("неожиданный формат ответа")
    found = set()
    for region in data:
        alerts = region.get("activeAlerts") or []
        if not isinstance(alerts, list):
            raise SirenError("неожиданный формат activeAlerts")
        for a in alerts:
            if not isinstance(a, dict) or str(a.get("type", "")).upper() != "AIR":
                continue
            levels = {str(x.get("alertLevel", "")).lower() for x in (a.get("activeAlertLevels") or [])
                      if isinstance(x, dict)}
            found |= (levels & set(LEVELS)) or {"red"}
    return "red" if "red" in found else "yellow" if "yellow" in found else ""


def fetch_level(region=DEFAULT_REGION, base=BASE, timeout=TIMEOUT):
    url = base + validate_region(region)
    req = urllib.request.Request(url, headers={"User-Agent": "ha-tv-renderer"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise SirenError("ответ слишком большой")
        return parse_level(json.loads(raw))
    except urllib.error.HTTPError as e:
        raise SirenError(f"HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SirenError(f"нет связи ({type(e).__name__})") from None
    except ValueError:
        raise SirenError("ответ не JSON") from None


def fresh_level(level, fetched_at, now, ttl=STALE_AFTER):
    """Последний известный уровень, если он не старше ttl; иначе '' (не знаем — не показываем)."""
    if level in LEVELS and fetched_at is not None and 0 <= now - fetched_at <= ttl:
        return level
    return ""
