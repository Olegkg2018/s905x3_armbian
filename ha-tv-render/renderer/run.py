#!/usr/bin/env python3
"""HA dashboard -> RTSP renderer.

Runs Xvfb + Chromium (kiosk) showing an HA Lovelace dashboard, injects a
Bearer session for a dedicated non-admin HA user via localStorage, then
publishes an x11grab H.264 stream to an RTSP server (MediaMTX).
"""
import json, os, signal, subprocess, sys, time, urllib.parse, urllib.request
import siren
from websocket import create_connection

HA_URL   = os.environ["HA_URL"].rstrip("/")
HA_USER  = os.environ["HA_USER"]
HA_PASS  = os.environ["HA_PASS"]
DASH     = os.environ.get("DASH_PATH", "/lovelace/0")
RTSP_URL = os.environ["RTSP_URL"]
W        = int(os.environ.get("WIDTH", "1280"))
H        = int(os.environ.get("HEIGHT", "720"))
FPS      = int(os.environ.get("FPS", "4"))
BR       = os.environ.get("BITRATE", "900k")
DISPLAY  = ":99"
CLIENT_ID = HA_URL + "/"
PROFILE  = "/data/profile"
ALERT_REGION = siren.validate_region(os.environ.get("ALERT_REGION", siren.DEFAULT_REGION))
ALERT_EVERY  = 60      # c: опрос siren.pp.ua (лимит сервиса 200 запросов / 5 мин)

procs = {}

def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)

def http_json(path, data=None, form=False):
    url = HA_URL + path
    if form:
        body = urllib.parse.urlencode(data).encode()
        hdr = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        body = json.dumps(data).encode() if data is not None else None
        hdr = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=body, headers=hdr, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def get_tokens():
    """3-step HA OAuth with username/password -> token set."""
    s1 = http_json("/auth/login_flow", {
        "client_id": CLIENT_ID, "handler": ["homeassistant", None], "redirect_uri": CLIENT_ID})
    flow = s1["flow_id"]
    s2 = http_json(f"/auth/login_flow/{flow}", {
        "client_id": CLIENT_ID, "username": HA_USER, "password": HA_PASS})
    if s2.get("type") != "create_entry":
        raise RuntimeError(f"login failed: {s2}")
    code = s2["result"]
    tok = http_json("/auth/token", {
        "grant_type": "authorization_code", "code": code, "client_id": CLIENT_ID}, form=True)
    tok["hassUrl"] = HA_URL
    tok["clientId"] = CLIENT_ID
    tok["expires"] = int(time.time() * 1000) + int(tok["expires_in"]) * 1000
    return tok

# ---- CDP helpers ----
class CDP:
    def __init__(self, port=9222):
        self.port = port; self.ws = None; self._id = 0
    def connect(self):
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=2))
                page = next((t for t in tabs if t["type"] == "page"), None)
                if page:
                    self.ws = create_connection(page["webSocketDebuggerUrl"], timeout=10)
                    return
            except Exception:
                pass
            time.sleep(1)
        raise RuntimeError("CDP not reachable")
    def send(self, method, **params):
        self._id += 1; mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == mid:
                if "error" in m:
                    raise RuntimeError(m["error"])
                return m.get("result", {})
    def navigate(self, url):
        self.send("Page.navigate", url=url)
    def eval(self, expr):
        r = self.send("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        return r.get("result", {}).get("value")

def start_xvfb():
    # clean stale state from a previous crashed run (container fs survives restarts)
    subprocess.run(["pkill", "-9", "-f", "Xvfb"], capture_output=True)
    subprocess.run(["pkill", "-9", "-x", "chromium"], capture_output=True)
    time.sleep(1)
    for f in ("/tmp/.X99-lock", "/tmp/.X11-unix/X99"):
        try:
            os.remove(f)
        except OSError:
            pass
    p = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp", "-dpi", "96"])
    procs["xvfb"] = p
    for _ in range(30):
        if subprocess.run(["xdpyinfo", "-display", DISPLAY], capture_output=True).returncode == 0:
            log("Xvfb up"); return
        time.sleep(0.5)
    raise RuntimeError("Xvfb failed")

def start_chromium():
    for f in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        try:
            os.remove(os.path.join(PROFILE, f))
        except OSError:
            pass
    env = dict(os.environ, DISPLAY=DISPLAY)
    args = [
        "chromium",
        "--user-data-dir=" + PROFILE,
        "--remote-debugging-port=9222", "--remote-allow-origins=*",
        "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
        "--no-first-run", "--no-default-browser-check", "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-features=Translate,TranslateUI,MediaRouter,OptimizationHints",
        "--lang=ru-RU", "--accept-lang=ru-RU,ru", "--disable-translate",
        "--disable-component-update", "--check-for-update-interval=31536000",
        "--disable-pinch", "--overscroll-history-navigation=0", "--hide-scrollbars",
        "--autoplay-policy=no-user-gesture-required",
        "--force-device-scale-factor=1", f"--window-size={W},{H}", "--window-position=0,0",
        "--kiosk", "--start-fullscreen",
        "about:blank",
    ]
    p = subprocess.Popen(args, env=env)
    procs["chromium"] = p
    log("chromium started pid", p.pid)

def seed_session(cdp, tok):
    payload = json.dumps({k: tok[k] for k in
        ("access_token", "token_type", "expires_in", "hassUrl", "clientId", "expires", "refresh_token")})
    cdp.navigate(HA_URL + "/")
    time.sleep(3)
    cdp.eval(f"localStorage.setItem('hassUrl', {json.dumps(HA_URL)});"
             f"localStorage.setItem('hassTokens', {json.dumps(payload)}); true")
    cdp.navigate(HA_URL + DASH)
    log("session seeded, dashboard loading")

def start_ffmpeg():
    g = str(max(2, FPS * 2))   # ~2s GOP (like the real XM camera); DVR rarely reconnects now
    level = "4.1" if W * H > 1280 * 720 else "3.1"
    audio = os.environ.get("AUDIO", "1") == "1"            # silent track: many XM/Sofia DVRs need it
    profile = os.environ.get("H264_PROFILE", "main")       # real XM .25 uses Main (profile_idc 77)
    args = ["ffmpeg", "-loglevel", "warning", "-nostdin",
            "-f", "x11grab", "-draw_mouse", "0", "-framerate", str(FPS),
            "-video_size", f"{W}x{H}", "-i", DISPLAY]
    if audio:
        args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=16000"]
    # main profile needs CABAC (heavier preset); baseline can use ultrafast.
    main = profile == "main"
    preset = os.environ.get("X264_PRESET", "superfast" if main else "ultrafast")
    xp = ("cabac=1:" if main else "cabac=0:") + \
         "ref=1:bframes=0:scenecut=0:slices=1:sliced-threads=0:repeat-headers=1:keyint=%s:min-keyint=%s" % (g, g)
    args += [
        "-vf", "format=yuv420p",
        "-c:v", "libx264", "-preset", preset, "-tune", "zerolatency",
        "-profile:v", profile, "-level", level,
        "-threads", "2",
        "-x264-params", xp,
        "-g", g, "-keyint_min", g, "-sc_threshold", "0",
        "-b:v", BR, "-maxrate", BR, "-bufsize", str(int(BR.rstrip('k')) * 2) + "k",
    ]
    args += (["-c:a", "aac", "-b:a", "16k", "-ar", "16000", "-ac", "1"] if audio else ["-an"])
    args += ["-f", "rtsp", "-rtsp_transport", "tcp", "-pkt_size", "1316", RTSP_URL]
    p = subprocess.Popen(args)
    procs["ffmpeg"] = p
    log("ffmpeg publishing to", RTSP_URL, "profile=%s audio=%s fps=%s" % (profile, audio, FPS))

def push_alert(cdp):
    """Уровень воздушной тревоги -> localStorage.alertState страницы (tv.html показывает слово ТРЕВОГА).
    При сбое источника ничего не пишем: tv.html сам перестанет показывать данные старше 5 минут."""
    try:
        lvl = siren.fetch_level(ALERT_REGION)
    except siren.SirenError as e:
        log("siren:", e)
        return
    state = json.dumps({"lvl": lvl, "ts": int(time.time() * 1000)})
    cdp.eval("localStorage.setItem('alertState', %s); true" % json.dumps(state))

def cleanup(*_):
    for name, p in procs.items():
        try: p.terminate()
        except Exception: pass
    time.sleep(2)
    for name, p in procs.items():
        try: p.kill()
        except Exception: pass
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

def main():
    os.makedirs(PROFILE, exist_ok=True)
    log("fetching HA token for user", HA_USER)
    tok = get_tokens()
    log("token ok, expires_in", tok["expires_in"])
    start_xvfb()
    start_chromium()
    cdp = CDP(); cdp.connect(); log("CDP connected")
    seed_session(cdp, tok)
    time.sleep(12)              # let the dashboard fully render
    start_ffmpeg()

    last_refresh = time.time()
    last_alert = 0.0
    while True:
        time.sleep(15)
        if time.time() - last_alert >= ALERT_EVERY:
            last_alert = time.time()
            try:
                push_alert(cdp)
            except Exception as e:       # CDP мог отвалиться — не мешаем надзору за ffmpeg/chromium
                log("alert push failed:", e)
        # restart ffmpeg if it died
        if procs["ffmpeg"].poll() is not None:
            log("ffmpeg exited", procs["ffmpeg"].returncode, "- restarting")
            time.sleep(2); start_ffmpeg()
        # restart chromium if it died
        if procs["chromium"].poll() is not None:
            log("chromium exited - restarting")
            start_chromium()
            cdp = CDP(); cdp.connect()
            tok = get_tokens(); seed_session(cdp, tok); last_refresh = time.time()
            time.sleep(12)
        # refresh the access token every 20 min so it never lapses.  tv.html
        # re-reads localStorage.hassTokens on every poll, so just update it in
        # place (no navigate = no reload flash).  A real HA Lovelace dashboard
        # reads the token only at load, so it still needs the navigate.
        if time.time() - last_refresh > 1200:
            try:
                tok = get_tokens()
                cdp.eval("localStorage.setItem('hassTokens', %s); true" % json.dumps(json.dumps(
                    {k: tok[k] for k in ("access_token","token_type","expires_in","hassUrl","clientId","expires","refresh_token")})))
                if "tv.html" not in DASH:
                    cdp.navigate(HA_URL + DASH)
                last_refresh = time.time()
                log("token refreshed")
            except Exception as e:
                log("refresh failed:", e)

if __name__ == "__main__":
    main()
