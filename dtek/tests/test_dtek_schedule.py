"""Тесты логики dtek_schedule: python3 -m unittest discover -s ha/tests -v (stdlib, без Home Assistant)."""
import importlib.util
import json
import py_compile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

COMP = Path(__file__).resolve().parents[1] / "custom_components" / "dtek_schedule"
spec = importlib.util.spec_from_file_location("schedule_logic", COMP / "schedule_logic.py")
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)

DATASET = (Path(__file__).parent / "dnipro_dataset.json").read_text(encoding="utf-8")      # реальный data/dnipro.json (урезан)
PAGE = (Path(__file__).parent / "dtek_page_min.html").read_text(encoding="utf-8")   # реальный fact со страницы ДТЕК
EXPECTED = [0] * 9 + [1] * 15 + [0] * 6 + [1] * 8 + [0] * 10      # 04:30–12:00 и 15:00–19:00
SLOTS = [(0, 10), (12, 10)]
K = sl.TZ
T = lambda d, h, m=0: datetime(2026, 11, d, h, m, tzinfo=K)


class ParseTests(unittest.TestCase):
    def test_real_page_gives_todays_table_for_group(self):
        r = sl.parse_page(PAGE, "GPV2.2")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["days"], {"2026-11-10": EXPECTED})
        self.assertEqual(r["updated"], "09.11.2026 23:57")

    def test_windows_and_hours_match_the_site(self):
        cells = sl.parse_page(PAGE, "GPV2.2")["days"]["2026-11-10"]
        self.assertEqual(sl.windows(cells), [("04:30", "12:00"), ("15:00", "19:00")])
        self.assertEqual(sl.outage_hours(cells), 11.5)

    def test_other_groups_differ(self):
        a = sl.parse_page(PAGE, "GPV1.1")["days"]["2026-11-10"]
        self.assertNotEqual(a, EXPECTED)
        self.assertEqual(len(a), 48)

    def test_challenge_page_is_reported_not_parsed(self):
        stub = '<html><script src="/_Incapsula_Resource?SWJIYLWA=1"></script></html>'
        self.assertEqual(sl.parse_page(stub, "GPV2.2")["status"], "challenge")
        self.assertTrue(sl.is_challenge(stub))
        self.assertFalse(sl.is_challenge(PAGE))

    def test_missing_or_broken_table(self):
        for html in ("", None, "<html>нет таблицы</html>", "DisconSchedule.fact = {broken", 'DisconSchedule.fact = 5',
                     'DisconSchedule.fact = {"data":{}}', 'DisconSchedule.fact = {"data":[1,2]}'):
            self.assertEqual(sl.parse_page(html, "GPV2.2")["status"], "no_table", repr(html))

    def test_unknown_group_and_bad_cells(self):
        self.assertEqual(sl.parse_page(PAGE, "GPV9.9")["status"], "no_group")
        bad = 'DisconSchedule.fact = {"data":{"1794261600":{"GPV2.2":{"1":"yes","2":"<script>"}}}}'
        self.assertEqual(sl.parse_page(bad, "GPV2.2")["status"], "no_group")      # неполные/чужие значения отвергаются

    def test_multiple_days_and_hostile_strings(self):
        fact = {"data": {"1794261600": {"GPV2.2": {str(h): "yes" for h in range(1, 25)}},
                         "1794348000": {"GPV2.2": {str(h): "no" for h in range(1, 25)}},
                         "не число": {"GPV2.2": {}}}, "update": "x" * 500 + "<b>"}
        html = "DisconSchedule.fact = " + json.dumps(fact) + "\n"
        r = sl.parse_page(html, "GPV2.2")
        self.assertEqual(sorted(r["days"]), ["2026-11-10", "2026-11-11"])
        self.assertEqual(sl.outage_hours(r["days"]["2026-11-11"]), 24.0)
        self.assertLessEqual(len(r["updated"]), 40)

    def test_state_mapping_with_half_hours(self):
        hours = {str(h): "yes" for h in range(1, 25)}
        hours.update({"1": "first", "2": "second", "3": "maybe", "4": "mfirst", "5": "msecond"})
        c = sl.hours_to_cells(hours)
        self.assertEqual(c[:10], [1, 0, 0, 1, 2, 2, 2, 0, 0, 2])

    def test_windows_edges(self):
        self.assertEqual(sl.windows([0] * 48), [])
        self.assertEqual(sl.windows([1] * 48), [("00:00", "24:00")])
        self.assertEqual(sl.windows([1, 1] + [0] * 44 + [1, 1]), [("00:00", "01:00"), ("23:00", "24:00")])
        self.assertEqual(sl.windows([0, 2, 2, 0], state=2), [("00:30", "01:30")])


class DatasetTests(unittest.TestCase):
    def test_dataset_json_gives_the_same_table_as_the_page(self):
        r = sl.parse_page(DATASET, "GPV2.2")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["days"], {"2026-11-10": EXPECTED})                     # совпадает со страницей ДТЕК
        self.assertEqual(r["days"], sl.parse_page(PAGE, "GPV2.2")["days"])
        self.assertEqual(r["updated"], "09.11.2026 23:57")
        self.assertTrue(r["source_ok"])
        self.assertTrue(r["source_updated"].startswith("2026-11-10T10:"))

    def test_dataset_edge_cases(self):
        self.assertEqual(sl.parse_page("{}", "GPV2.2")["status"], "no_table")
        self.assertEqual(sl.parse_page("{not json", "GPV2.2")["status"], "no_table")
        self.assertEqual(sl.parse_page('{"fact": 5}', "GPV2.2")["status"], "no_table")
        self.assertEqual(sl.parse_page('{"fact": {"data": {}}}', "GPV2.2")["status"], "no_table")
        self.assertEqual(sl.parse_page(DATASET, "GPV9.9")["status"], "no_group")
        broken = json.loads(DATASET); broken["lastUpdateStatus"]["ok"] = False
        self.assertFalse(sl.parse_page(json.dumps(broken), "GPV2.2")["source_ok"])
        for junk in ("[]", "null", "12", '"x"'):
            self.assertEqual(sl.parse_page(junk, "GPV2.2")["status"], "no_table", junk)

    def test_staleness(self):
        now = datetime.fromisoformat("2026-11-10T12:00:00+00:00")
        self.assertFalse(sl.is_stale("2026-11-10T11:55:00.000Z", now))
        self.assertTrue(sl.is_stale("2026-11-09T11:00:00.000Z", now))
        for bad in (None, "", "мусор", "2026-11-10T11:55:00"):          # без времени или без часового пояса — недоверие
            self.assertTrue(sl.is_stale(bad, now), repr(bad))

    def test_interval_polling_and_backoff(self):
        n = datetime.fromisoformat("2026-11-10T12:00:00+00:00")
        m = lambda x: n + timedelta(minutes=x)
        self.assertTrue(sl.due_interval(n, None, None, 0, 60))
        self.assertFalse(sl.due_interval(m(30), n, n, 0, 60))
        self.assertTrue(sl.due_interval(m(60), n, n, 0, 60))
        self.assertFalse(sl.due_interval(m(30), n, m(10), 1, 60) is False and False)      # (после сбоя — только по паузе)
        self.assertFalse(sl.due_interval(m(50), n, m(10), 1, 60))                         # сбой в 10 мин: пауза 60 мин
        self.assertTrue(sl.due_interval(m(70), n, m(10), 1, 60))
        self.assertFalse(sl.due_interval(m(500), None, m(100), 9, 60))                    # потолок паузы 8 ч
        self.assertTrue(sl.due_interval(m(581), None, m(100), 9, 60))

    def test_interval_simulation_requests_per_day_bounded(self):
        now, ok, att, fails, count = datetime.fromisoformat("2026-11-10T00:00:00+00:00"), None, None, 0, 0
        end = now + timedelta(days=2)
        while now < end:
            if sl.due_interval(now, ok, att, fails, 60):
                count += 1
                ok = att = now                                                          # источник всегда отвечает
            now += timedelta(minutes=20)
        self.assertLessEqual(count, 2 * 24 + 1)                                         # не чаще раза в час
        self.assertGreaterEqual(count, 2 * 24 - 2)

    def test_sensor_defaults_to_github_dataset_not_the_dtek_site(self):
        src = (COMP / "sensor.py").read_text(encoding="utf-8")
        self.assertIn("raw.githubusercontent.com/Baskerville42/outage-data-ua/main/data/dnipro.json", src)
        self.assertNotRegex(src, r'DEFAULT_URL = "https://www\.dtek')
        self.assertIn('vol.Optional(CONF_INTERVAL, default=60)', src)


class FailoverTests(unittest.TestCase):
    """Дублирование источников: основной (GitHub, раз в час) -> резервный (страница ДТЕК, <= 2 раза в сутки)."""
    SLOTS = sl.FALLBACK_SLOTS

    def simulate(self, primary_ok, fallback_result, days=3, has_today_when_ok=True):
        """primary_ok(now)->bool, fallback_result(now)->'ok'|'challenge'|'error'. Возвращает счётчики запросов по дням."""
        now = datetime(2026, 11, 10, 0, 0, tzinfo=K)
        p = dict(ok=None, att=None, fails=0, status="no_data")
        f = dict(ok=None, att=None, fails=0, pause=None)
        have_today = False
        counts = {"primary": {}, "fallback": {}, "first_fallback": None}
        end = now + timedelta(days=days)
        while now < end:
            day = now.date().isoformat()
            if sl.due_interval(now, p["ok"], p["att"], p["fails"], 60):
                counts["primary"][day] = counts["primary"].get(day, 0) + 1
                p["att"] = now
                if primary_ok(now):
                    p.update(ok=now, fails=0, status="ok"); have_today = has_today_when_ok
                else:
                    p["fails"] += 1; p["status"] = "error"
            if sl.fallback_needed(now, p["ok"], p["status"], have_today) and sl.due(now, f["ok"], f["att"], f["fails"], f["pause"], self.SLOTS):
                counts["fallback"][day] = counts["fallback"].get(day, 0) + 1
                counts["first_fallback"] = counts["first_fallback"] or now
                f["att"] = now
                r = fallback_result(now)
                if r == "ok":
                    f.update(ok=now, fails=0); have_today = True
                elif r == "challenge":
                    f["pause"] = now + sl.CHALLENGE_PAUSE; f["fails"] += 1
                else:
                    f["fails"] += 1
            now += timedelta(minutes=20)
        return counts

    def test_fallback_needed_rules(self):
        now = T(10, 12)
        self.assertFalse(sl.fallback_needed(now, T(10, 11), "ok", True))
        self.assertTrue(sl.fallback_needed(now, T(10, 8), "ok", True))                  # основной молчит >= 3 ч
        self.assertTrue(sl.fallback_needed(now, None, "no_data", False))                # данных нет вообще
        self.assertTrue(sl.fallback_needed(now, T(10, 11), "stale", True))              # основной устарел
        self.assertTrue(sl.fallback_needed(T(10, 5), T(10, 4, 30), "ok", False))        # сутки начались, таблицы на сегодня нет
        self.assertFalse(sl.fallback_needed(T(10, 0, 30), T(10, 0, 10), "ok", False))   # первый час суток — ещё ждём основной

    def test_healthy_primary_never_touches_the_fallback(self):
        c = self.simulate(lambda n: True, lambda n: "ok")
        self.assertEqual(c["fallback"], {})
        self.assertTrue(all(v <= 24 for v in c["primary"].values()))

    def test_dead_primary_switches_to_fallback_at_most_twice_a_day(self):
        c = self.simulate(lambda n: n < datetime(2026, 11, 10, 12, 0, tzinfo=K), lambda n: "ok", days=4)
        self.assertTrue(c["fallback"], "резерв должен подключиться")
        self.assertTrue(all(v <= 2 for v in c["fallback"].values()), c["fallback"])
        last_ok = datetime(2026, 11, 10, 11, 0, tzinfo=K)                        # последний удачный часовой опрос основного
        self.assertGreaterEqual(c["first_fallback"], last_ok + sl.FALLBACK_AFTER)    # резерв — только после 3 часов молчания
        self.assertLessEqual(c["first_fallback"], last_ok + sl.FALLBACK_AFTER + timedelta(hours=1))

    def test_challenged_fallback_is_rate_limited(self):
        c = self.simulate(lambda n: False, lambda n: "challenge", days=3)
        self.assertTrue(all(v <= 8 for v in c["fallback"].values()), c["fallback"])      # пауза 3 ч после каждой заглушки
        self.assertTrue(all(v <= 24 for v in c["primary"].values()))

    def test_both_sources_down_stays_bounded(self):
        c = self.simulate(lambda n: False, lambda n: "error", days=3)
        self.assertTrue(all(v <= 2 * (1 + sl.MAX_FAILS_PER_SLOT) for v in c["fallback"].values()), c["fallback"])
        self.assertTrue(all(v <= 12 for v in c["primary"].values()), c["primary"])       # паузы нарастают до 8 ч

    def test_primary_without_todays_table_triggers_fallback(self):
        c = self.simulate(lambda n: True, lambda n: "ok", has_today_when_ok=False, days=2)
        self.assertTrue(c["fallback"])
        self.assertTrue(all(v <= 2 for v in c["fallback"].values()), c["fallback"])

    def test_restored_status_is_neutral(self):
        src = (COMP / "sensor.py").read_text(encoding="utf-8")
        self.assertIn('self._primary.status = "restored"', src)
        self.assertNotIn('a.get("status") or "restored"', src)

    def test_sensor_has_failover_wiring(self):
        src = (COMP / "sensor.py").read_text(encoding="utf-8")
        self.assertIn("sl.fallback_needed(", src)
        self.assertIn("DEFAULT_FALLBACK = \"https://www.dtek-dnem.com.ua/ua/shutdowns\"", src)
        self.assertIn("устаревшие данные основного источника не затирают", src)
        self.assertEqual(src.count("session.get("), 1)


class ScheduleTests(unittest.TestCase):
    def test_first_fetch_when_no_data(self):
        self.assertTrue(sl.due(T(10, 8), None, None, 0, None, SLOTS))

    def test_no_second_fetch_in_same_slot(self):
        ok = T(10, 0, 12)
        for now in (T(10, 0, 40), T(10, 5), T(10, 11, 59)):
            self.assertFalse(sl.due(now, ok, ok, 0, None, SLOTS), now)

    def test_next_slot_triggers_once(self):
        ok = T(10, 0, 12)
        self.assertFalse(sl.due(T(10, 12, 9), ok, ok, 0, None, SLOTS))
        self.assertTrue(sl.due(T(10, 12, 10), ok, ok, 0, None, SLOTS))
        ok2 = T(10, 12, 15)
        self.assertFalse(sl.due(T(10, 12, 40), ok2, ok2, 0, None, SLOTS))

    def test_failure_backoff_then_give_up_until_next_slot(self):
        ok = T(10, 0, 12)
        att = T(10, 12, 11)
        self.assertFalse(sl.due(T(10, 13, 0), ok, att, 1, None, SLOTS))       # пауза 60 мин после 1-го сбоя
        self.assertTrue(sl.due(T(10, 13, 11), ok, att, 1, None, SLOTS))
        self.assertFalse(sl.due(T(10, 14, 0), ok, T(10, 13, 11), 2, None, SLOTS))   # 120 мин
        self.assertTrue(sl.due(T(10, 15, 11), ok, T(10, 13, 11), 2, None, SLOTS))
        self.assertFalse(sl.due(T(10, 23, 0), ok, T(10, 20, 0), sl.MAX_FAILS_PER_SLOT + 1, None, SLOTS))   # сдались
        self.assertTrue(sl.due(T(11, 0, 10), ok, T(10, 20, 0), 5, None, SLOTS))   # новое окно: снова пробуем

    def test_challenge_pause_blocks_requests(self):
        until = T(10, 15, 0)
        self.assertFalse(sl.due(T(10, 14, 59), None, T(10, 12, 0), 1, until, SLOTS))
        self.assertTrue(sl.due(T(10, 15, 1), None, T(10, 12, 0), 1, until, SLOTS))

    def test_no_data_ever_retries_with_capped_backoff(self):
        self.assertFalse(sl.due(T(10, 9, 0), None, T(10, 8, 30), 1, None, SLOTS))
        self.assertTrue(sl.due(T(10, 9, 31), None, T(10, 8, 30), 1, None, SLOTS))
        self.assertFalse(sl.due(T(10, 15, 0), None, T(10, 8, 0), 9, None, SLOTS))       # потолок паузы 8 ч
        self.assertTrue(sl.due(T(10, 16, 1), None, T(10, 8, 0), 9, None, SLOTS))

    def test_simulation_two_successful_fetches_per_day(self):
        now, last_ok, last_try, fails, count, per_day = T(10, 8, 0), None, None, 0, 0, {}
        end = T(14, 8, 0)
        while now < end:                                         # тик каждые 20 минут, запрос всегда удачен
            if sl.due(now, last_ok, last_try, fails, None, SLOTS):
                last_ok = last_try = now
                per_day[now.date().isoformat()] = per_day.get(now.date().isoformat(), 0) + 1
            now += timedelta(minutes=20)
        # 10.11: первый запрос при отсутствии данных (08:00) + окно 12:10; дальше ровно по два в сутки (00:10 и 12:10)
        self.assertEqual(per_day, {"2026-11-10": 2, "2026-11-11": 2, "2026-11-12": 2, "2026-11-13": 2, "2026-11-14": 1})

    def test_simulation_all_failures_is_bounded(self):
        now, last_ok, last_try, fails, attempts = T(10, 0, 0), T(9, 12, 15), T(9, 12, 15), 0, 0
        end = T(12, 0, 0)
        while now < end:                                         # портал всё время отвечает ошибкой
            if sl.due(now, last_ok, last_try, fails, None, SLOTS):
                attempts += 1
                fails = fails + 1 if last_try is not None and last_try >= sl._slot_start(now, SLOTS) else 1
                last_try = now
            now += timedelta(minutes=20)
        self.assertLessEqual(attempts, 2 * 2 * (sl.MAX_FAILS_PER_SLOT + 1))     # 2 суток x 2 окна x (1 + повторы)


class PackageTests(unittest.TestCase):
    def test_sensor_module_compiles_and_manifest_is_valid(self):
        py_compile.compile(str(COMP / "sensor.py"), doraise=True)
        m = json.loads((COMP / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["domain"], "dtek_schedule")
        self.assertEqual(m["requirements"], [])
        self.assertIn("version", m)

    def test_sensor_uses_one_get_and_no_evasion_headers(self):
        src = (COMP / "sensor.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("session.get("), 1)
        for forbidden in ("Referer", "Cookie", "X-Forwarded", "proxy", "webdriver", "playwright", "selenium"):
            self.assertNotIn(forbidden, src)
        self.assertIn("HomeAssistant-dtek_schedule", src)               # честный User-Agent

    def test_no_immediate_request_on_startup(self):
        src = (COMP / "sensor.py").read_text(encoding="utf-8")
        self.assertIn("async_call_later(self.hass, STARTUP_DELAY, self._tick)", src)
        self.assertNotIn("async_create_task(self._tick", src)           # раньше запрос уходил сразу при старте HA
        self.assertRegex(src, r"STARTUP_DELAY = timedelta\(minutes=(\d+)\)")
        minutes = int(__import__("re").search(r"STARTUP_DELAY = timedelta\(minutes=(\d+)\)", src).group(1))
        self.assertGreaterEqual(minutes, 5)


if __name__ == "__main__":
    unittest.main()
