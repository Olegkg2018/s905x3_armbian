"""Чистая логика компонента dtek_schedule (без зависимостей от Home Assistant): разбор таблицы ДТЕК и расписание запросов.

Источник — страница https://www.dtek-dnem.com.ua/ua/shutdowns: график лежит в тексте страницы как
`DisconSchedule.fact = {...}` (даты -> очереди GPVx.y -> 24 часа -> yes/no/first/second/maybe/...).
Ячейка суток: 0 = свет есть, 1 = отключение, 2 = «возможно отключение»; 48 ячеек по 30 минут.
Страница читается только как текст, ничего не выполняется.
"""
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Kyiv")
CELLS = 48
_PAIR = {"yes": (0, 0), "no": (1, 1), "first": (1, 0), "second": (0, 1),
         "maybe": (2, 2), "mfirst": (2, 0), "msecond": (0, 2)}
MAX_FAILS_PER_SLOT = 4          # попыток повторов после первой неудачи в одном «окне» запросов
BACKOFF_MIN = 60                # пауза после неудачи: 60, 120, 240, 480 минут
CHALLENGE_PAUSE = timedelta(hours=3)
FALLBACK_AFTER = timedelta(hours=3)     # основной источник молчит дольше — подключаем резервный
FALLBACK_SLOTS = [(0, 10), (12, 10)]    # резерв (страница ДТЕК) опрашивается не чаще двух раз в сутки


def extract_object(html, name):
    """JSON-объект, присвоенный DisconSchedule.<name>, поиском по скобкам (без eval)."""
    m = re.search(r"DisconSchedule\." + re.escape(name) + r"\s*=\s*", html or "")
    if not m:
        return None
    i = m.end()
    if i >= len(html) or html[i] not in "{[":
        return None
    depth, in_str, esc = 0, False, False
    for j in range(i, len(html)):
        c = html[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[i:j + 1])
                except ValueError:
                    return None
    return None


def is_challenge(html):
    """Страница-заглушка защиты (Incapsula) вместо данных портала."""
    h = html or ""
    return "_Incapsula_Resource" in h and "DisconSchedule" not in h


def hours_to_cells(hours):
    """{'1': 'yes', ..., '24': 'no'} -> 48 ячеек; неполные/неизвестные данные -> None."""
    if not isinstance(hours, dict):
        return None
    cells = []
    for h in range(1, 25):
        pair = _PAIR.get(str(hours.get(str(h), "")))
        if pair is None:
            return None
        cells.extend(pair)
    return cells


def _days_from_fact(fact, group):
    data = fact.get("data") if isinstance(fact, dict) else None
    if not isinstance(data, dict) or not data:
        return {}
    days = {}
    for key, groups in data.items():
        try:
            day = datetime.fromtimestamp(int(key), TZ).date().isoformat()
        except (ValueError, OverflowError, OSError, TypeError):
            continue
        cells = hours_to_cells(groups.get(group)) if isinstance(groups, dict) else None
        if cells:
            days[day] = cells
    return days


def parse_page(text, group):
    """Страница ДТЕК (HTML с DisconSchedule.fact) ИЛИ JSON набора данных (data/dnipro.json со полем fact).

    -> {'status': 'ok'|'challenge'|'no_table'|'no_group', 'days': {'YYYY-MM-DD': [48 ячеек]},
        'updated': str|None, 'source_updated': ISO|None, 'source_ok': bool|None}
    """
    out = {"status": "no_table", "days": {}, "updated": None, "source_updated": None, "source_ok": None}
    if is_challenge(text):
        out["status"] = "challenge"
        return out
    fact = None
    if (text or "").lstrip().startswith("{"):                       # JSON набора данных
        try:
            obj = json.loads(text)
        except ValueError:
            return out
        fact = obj.get("fact") if isinstance(obj, dict) else None
        lu = obj.get("lastUpdated") if isinstance(obj, dict) else None
        out["source_updated"] = lu[:40] if isinstance(lu, str) else None
        st = obj.get("lastUpdateStatus") if isinstance(obj, dict) else None
        out["source_ok"] = bool(st.get("ok")) if isinstance(st, dict) and "ok" in st else None
    else:                                                            # HTML страницы
        fact = extract_object(text, "fact")
    if not isinstance(fact, dict):
        return out
    out["days"] = _days_from_fact(fact, group)
    upd = fact.get("update")
    out["updated"] = upd[:40] if isinstance(upd, str) else None
    out["status"] = "ok" if out["days"] else ("no_group" if isinstance(fact.get("data"), dict) and fact["data"] else "no_table")
    return out


def is_stale(source_updated, now, max_age=timedelta(hours=12)):
    """Источник не обновлялся слишком давно (или время не разобрать) -> True."""
    try:
        t = datetime.fromisoformat(str(source_updated).replace("Z", "+00:00"))
    except ValueError:
        return True
    return t.tzinfo is None or now - t > max_age


def windows(cells, state=1):
    """Окна подряд идущих ячеек состояния state -> [('04:30', '12:00'), ...]."""
    out, start = [], None
    for i, c in enumerate(list(cells) + [None]):
        if c == state and start is None:
            start = i
        elif c != state and start is not None:
            out.append((_hm(start), _hm(i)))
            start = None
    return out


def _hm(cell):
    minutes = cell * 30
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def outage_hours(cells):
    return sum(1 for c in cells if c == 1) * 0.5


def _slot_start(now, slots):
    """Начало ближайшего прошедшего «окна» запросов (slots — [(час, минута)])."""
    best = None
    for dayshift in (0, -1):
        base = (now + timedelta(days=dayshift)).replace(second=0, microsecond=0)
        for h, m in slots:
            s = base.replace(hour=h, minute=m)
            if s <= now and (best is None or s > best):
                best = s
    return best


def due(now, last_success, last_attempt, failures, challenged_until, slots):
    """Пора ли делать запрос. Не чаще двух удачных запросов в сутки при двух окнах; повторы при сбоях редкие."""
    if challenged_until and now < challenged_until:
        return False
    if last_success is None:                                   # данных ещё нет: пробуем с нарастающей паузой (до 8 ч)
        return last_attempt is None or now - last_attempt >= _backoff(failures)
    start = _slot_start(now, slots)
    if start is None or last_success >= start:
        return False
    in_slot = failures if (last_attempt is not None and last_attempt >= start) else 0
    if in_slot == 0:
        return True
    return in_slot <= MAX_FAILS_PER_SLOT and now - last_attempt >= _backoff(in_slot)


def due_interval(now, last_success, last_attempt, failures, interval_min):
    """Опрос с постоянным интервалом (для набора данных на GitHub): после сбоя пауза нарастает до 8 ч."""
    if last_attempt is None:
        return True
    if last_success is None or last_attempt > last_success:
        return now - last_attempt >= _backoff(failures)
    return now - last_success >= timedelta(minutes=interval_min)


def fallback_needed(now, primary_ok_at, primary_status, has_today):
    """Нужен ли резервный источник: основной давно не отвечает, устарел или не даёт таблицу на сегодня."""
    if primary_status == "stale":
        return True
    if primary_ok_at is None or now - primary_ok_at >= FALLBACK_AFTER:
        return True
    return (not has_today) and now.hour >= 1                 # новые сутки начались, а таблицы на сегодня всё нет


def _backoff(n):
    return timedelta(minutes=BACKOFF_MIN * 2 ** max(0, min(n, 4) - 1))
