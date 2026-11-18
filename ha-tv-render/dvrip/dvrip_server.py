#!/usr/bin/env python3
"""Minimal DVR-IP / NETIP / Sofia "camera" server.

Presents an RTSP stream as an XM/Xiongmai NETIP camera on TCP :34567 so an
XM/Sofia DVR (that only supports NETIP digital channels) can add it.

Verified against a real XM camera (login/claim/start handshake, FC/FD media
frames, 4-byte start codes, 8192-byte packet chunking, per-packet seq, canned
config replies).  The DVR uses TWO connections: a control connection (login +
OPMonitor Start + config queries) and a media connection (OPMonitor Claim only) -
so the stream is started on the Claim connection, not on Start.
"""
import json, os, socket, struct, subprocess, threading, time
import queue as _queue

PORT      = int(os.environ.get("PORT", "34567"))
RTSP_URL  = os.environ.get("RTSP_URL", "rtsp://127.0.0.1:8554/tv")
FPS       = int(os.environ.get("FPS", "4"))
WIDTH     = int(os.environ.get("WIDTH", "1280"))
HEIGHT    = int(os.environ.get("HEIGHT", "720"))
DEBUG     = os.environ.get("DEBUG") == "1"

LOGIN, LOGIN_R          = 1000, 1001
KEEPALIVE, KEEPALIVE_R  = 1006, 1007
OPMON_CLAIM, OPMON_CLAIM_R = 1413, 1414
OPMON_START, OPMON_START_R = 1410, 1411
MEDIA_MSG = 1412

# Canned config responses captured from a real XM camera (192.168.2.25) that this
# DVR streams fine.  The DVR queries these on the monitor connection *while*
# receiving media; without real data (esp. Simplify.Encode -> "720P") it shows
# "resolution Unknown / NoConnect" and never displays the picture.
CANNED = {}
for _p in ("/canned.json", os.path.join(os.path.dirname(__file__), "canned.json")):
    try:
        with open(_p) as _f:
            CANNED = json.load(_f)
        break
    except Exception:
        pass

def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)

def pack_dt(t=None):
    t = time.localtime(t or time.time())
    return (t.tm_sec | (t.tm_min << 6) | (t.tm_hour << 12) |
            (t.tm_mday << 17) | (t.tm_mon << 22) | ((t.tm_year - 2000) << 26))

VER = int(os.environ.get("VER", "1"))

def _xm(v):
    # exact wire format of real XM devices: spaces around every : and inside every
    # { } and [ ] , keys sorted.
    if isinstance(v, dict):
        if not v:
            return "{ }"
        return "{ " + ", ".join('"%s" : %s' % (k, _xm(v[k])) for k in sorted(v)) + " }"
    if isinstance(v, (list, tuple)):
        if not v:
            return "[ ]"
        return "[ " + ", ".join(_xm(x) for x in v) + " ]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, str):
        return json.dumps(v)
    return json.dumps(v)

def xm_json(obj):
    return (_xm(obj) + "\n").encode() + b"\x00"

def build_ctrl(session, seq, msgid, obj):
    body = xm_json(obj)
    return struct.pack("<BBxxIIBBHI", 255, VER, session & 0xFFFFFFFF, seq & 0xFFFFFFFF,
                       0, 0, msgid, len(body)) + body

MTU = 8192  # verified against real XM .25: each media frame (FC/FD hdr + h264) is
            # split into <=8192-byte DVR-IP packets, and the packet sequence number
            # increments PER PACKET (not per frame), starting from 0 at stream start.

def build_media(session, seq0, payload):
    """Return (bytes, next_seq). seq0 = sequence number of the first packet."""
    out = b""
    seq = seq0
    for i in range(0, len(payload), MTU):
        chunk = payload[i:i + MTU]
        out += struct.pack("<BBxxIIBBHI", 255, VER, session & 0xFFFFFFFF,
                           seq & 0xFFFFFFFF, 0, 0, MEDIA_MSG, len(chunk)) + chunk
        seq = (seq + 1) & 0xFFFFFFFF
    return out, seq

def media_iframe(h264):
    hdr = struct.pack(">I", 0x000001FC) + struct.pack("<BBBBII",
        2, FPS, WIDTH // 8, HEIGHT // 8, pack_dt(), len(h264))
    return hdr + h264

def media_pframe(h264):
    return struct.pack(">I", 0x000001FD) + struct.pack("<I", len(h264)) + h264


SC = b"\x00\x00\x00\x01"   # XM decoders want 4-byte Annex-B start codes

def iter_nals(stdout):
    """Yield raw NAL bodies (no start code) from an Annex-B H.264 stream."""
    fd = stdout.fileno()
    buf = b""
    while True:
        chunk = os.read(fd, 262144)   # returns whatever is available, never blocks for a full buffer
        if not chunk:
            return
        buf += chunk
        # normalise: find start codes (3 or 4 byte)
        while True:
            i = buf.find(b"\x00\x00\x01")
            if i < 0:
                buf = buf[-3:]
                break
            j = buf.find(b"\x00\x00\x01", i + 3)
            if j < 0:
                buf = buf[i:]
                break
            body = buf[i + 3:j]
            # trailing 0x00 belongs to the next start code (4-byte)
            if body.endswith(b"\x00"):
                body = body[:-1]
            if body:
                yield body
            buf = buf[j:]


# Real XM camera (192.168.2.25) sends a proprietary type-229 SEI on every I-frame;
# its NVR appears to need that XM signature to lock onto the stream.  We keep our
# own libx264 SPS/PPS (replacing them would break slice parsing - different
# pic_order_cnt_type) but add the SEI and clear the constraint_set1 flag so the
# SPS profile byte matches (0x4d 0x00 like the real camera, not 0x4d 0x40).
XM_SEI = bytes.fromhex("06e5010080")
USE_XM_SPS = os.environ.get("XM_SPS", "1") == "1"

def _fix_sps(sps):
    if USE_XM_SPS and len(sps) > 2 and sps[0] == 0x67:
        sps = sps[:2] + b"\x00" + sps[3:]   # constraint flags -> 0x00
    return sps


def iter_access_units(stdout):
    """Yield (is_keyframe, annexb_bytes) access units (4-byte start codes)."""
    sps = pps = b""
    au = b""
    au_key = False
    have_au = False
    pending_aud = b""
    for body in iter_nals(stdout):
        ntype = body[0] & 0x1F
        if ntype == 7:
            sps = body; continue
        if ntype == 8:
            pps = body; continue
        if ntype == 9:        # AUD: delimits a new access unit, must come first
            if have_au and au:
                yield au_key, au
            au = b""
            have_au = False
            pending_aud = body
            continue
        if ntype == 6:        # SEI -> attach to current au
            au += SC + body
            continue
        if ntype in (1, 5):   # VCL: start of a coded picture
            if have_au and au:
                yield au_key, au
                au = b""
            au_key = (ntype == 5)
            have_au = True
            if pending_aud:
                au += SC + pending_aud; pending_aud = b""
            if au_key:
                if sps: au += SC + _fix_sps(sps)
                if pps: au += SC + pps
                if USE_XM_SPS: au += SC + XM_SEI
            if USE_XM_SPS and (body[0] & 0x60) != 0x60:
                # real XM P/I slices use nal_ref_idc=3 (0x61/0x65); libx264 emits
                # 0x41 for P slices -> some XM decoders reject the lower priority.
                body = bytes([(body[0] & 0x1F) | 0x60]) + body[1:]
            au += SC + body
        else:
            au += SC + body
    if have_au and au:
        yield au_key, au


class StreamHub:
    """One persistent ffmpeg reader for the RTSP stream.  Keeps the current GOP
    (capped) and fans out live access units to every connected DVR session, so a
    freshly (re)connected DVR gets a decodable picture immediately."""

    def __init__(self, name):
        self.name = name
        self.subs = set()
        self.lock = threading.Lock()
        self.gop = []                 # current GOP: [keyframe_au, p_au, p_au, ...]
        threading.Thread(target=self._run, daemon=True).start()

    def subscribe(self):
        q = _queue.Queue(maxsize=240)
        with self.lock:
            self.subs.add(q)
            backlog = list(self.gop)  # replay current GOP -> instant, gap-free picture
        return q, backlog

    def unsubscribe(self, q):
        with self.lock:
            self.subs.discard(q)

    def _run(self):
        src_file = os.environ.get("SRC_FILE")   # debug: feed a raw .h264 file instead of RTSP
        out = ["-an", "-c:v", "copy", "-f", "h264", "pipe:1"]
        while True:
            if src_file:
                cmd = ["ffmpeg", "-loglevel", "warning", "-nostdin", "-re",
                       "-r", str(FPS), "-i", src_file] + out
            else:
                cmd = ["ffmpeg", "-loglevel", "warning", "-nostdin",
                       "-fflags", "nobuffer", "-flags", "low_delay",
                       "-rtsp_transport", "tcp", "-i", RTSP_URL] + out
            ff = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=0)
            log("hub[%s] ffmpeg started pid %d%s" % (self.name, ff.pid, " (FILE)" if src_file else ""))
            try:
                for is_key, au in iter_access_units(ff.stdout):
                    with self.lock:
                        if is_key:
                            self.gop = [au]
                        elif self.gop:
                            self.gop.append(au)
                            if len(self.gop) > 20:   # ~1 GOP; keep the replay burst small
                                self.gop = self.gop[-20:]
                        dead = []
                        for q in self.subs:
                            try:
                                q.put_nowait((is_key, au))
                            except _queue.Full:
                                dead.append(q)
                        for q in dead:
                            # subscriber too slow: drop it, its pump will resync
                            self.subs.discard(q)
                            try: q.put_nowait(None)
                            except _queue.Full: pass
            except Exception as e:
                log("hub[%s] error %r" % (self.name, e))
            try: ff.kill(); ff.wait(timeout=3)
            except Exception: pass
            log("hub[%s] ffmpeg ended, restart in 2s" % self.name)
            time.sleep(2)


HUB = None   # the single StreamHub - created in main()


class Session(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__(daemon=True)
        self.conn = conn; self.addr = addr
        self.session = 0x00000004
        self.streaming = False
        self.stream_type = "Main"
        self.lock = threading.Lock()

    def send(self, data):
        with self.lock:
            try:
                self.conn.sendall(data)
            except OSError as e:
                if self.streaming:
                    log("send failed, stopping:", repr(e))
                self.streaming = False
                try: self.conn.close()
                except OSError: pass

    def read_frame(self):
        hdr = self._recvn(20)
        if not hdr or hdr[0] != 255:
            return None, None, 0
        session, seq = struct.unpack("<II", hdr[4:12])
        msgid, length = struct.unpack("<HI", hdr[14:20])
        body = self._recvn(length) if length else b""
        # adopt the session id the DVR uses on this connection (0 = not set yet)
        if session and session != self.session:
            log("adopt session %#x (was %#x) seq=%d" % (session, self.session, seq))
            self.session = session
        return msgid, body, seq

    def _recvn(self, n):
        out = b""
        while len(out) < n:
            try:
                b = self.conn.recv(n - len(out))
            except socket.timeout:
                # The DVR sends NOTHING on the media connection after Claim - it
                # just reads the stream.  A read timeout here is normal; keep the
                # connection alive as long as we are streaming (a dead peer is
                # caught by the send-side SO_SNDTIMEO instead).
                if self.streaming:
                    continue
                return None
            except OSError:
                return None
            if not b:
                return None
            out += b
        return out

    def run(self):
        log("connect", self.addr)
        self.conn.settimeout(45)
        # a blocked send to a vanished DVR must fail fast, not hang for the TCP RTO
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack("ll", 10, 0))
        try:
            while True:
                msgid, body, rseq = self.read_frame()
                if msgid is None:
                    break
                try:
                    obj = json.loads(body.rstrip(b"\x00\x0a") or b"{}")
                except Exception:
                    obj = {}
                name = obj.get("Name", "")
                try:
                    st = obj["OPMonitor"]["Parameter"].get("StreamType")
                    if st: self.stream_type = st
                except Exception:
                    pass
                if DEBUG:
                    log("  <- msgid=%d seq=%d name=%r %s" % (msgid, rseq, name, json.dumps(obj, ensure_ascii=False)[:160]))
                sid = "0x%08X" % self.session

                if msgid == LOGIN:
                    log("login user=%s" % obj.get("UserName"))
                    self.send(build_ctrl(self.session, 0, LOGIN_R, {
                        "AliveInterval": 20, "ChannelNum": 1, "DeviceType ": "IPC",
                        "ExtraChannel": 0, "Ret": 100, "SessionID": sid}))
                elif msgid == KEEPALIVE or name == "KeepAlive":
                    self.send(build_ctrl(self.session, rseq, KEEPALIVE_R, {
                        "Name": "KeepAlive", "Ret": 100, "SessionID": sid}))
                elif msgid == OPMON_CLAIM:
                    self.send(build_ctrl(self.session, rseq + 1, OPMON_CLAIM_R, {
                        "Name": "OPMonitor", "Ret": 100, "SessionID": sid}))
                    # Real XM: the DVR opens a dedicated MEDIA connection that sends
                    # only Claim (Start + config queries go on a SEPARATE control
                    # connection).  So the stream must start on the Claim connection.
                    a = (obj.get("OPMonitor") or {}).get("Action")
                    if a in (None, "Claim"):
                        self.start_stream()
                elif msgid == OPMON_START:
                    a = (obj.get("OPMonitor") or {}).get("Action")
                    # real XM camera replies 1411 to Start (on the control conn);
                    # it does NOT stream media there.
                    self.send(build_ctrl(self.session, rseq + 1, OPMON_START_R, {
                        "Name": "OPMonitor", "Ret": 100, "SessionID": sid}))
                    if a == "Stop":
                        self.stop_stream()
                elif name in CANNED:
                    resp = dict(CANNED[name])
                    resp["SessionID"] = sid
                    resp.setdefault("Name", name)
                    resp.setdefault("Ret", 100)
                    self.send(build_ctrl(self.session, rseq, msgid + 1, resp))
                elif name in ("OPMonitor",):
                    self.send(build_ctrl(self.session, rseq, msgid + 1, {
                        "Name": name, "Ret": 100, "SessionID": sid}))
                else:
                    # generic OK for capability / probe commands
                    self.send(build_ctrl(self.session, rseq, msgid + 1, {
                        "Name": name, "Ret": 100, "SessionID": sid}))
        except Exception as e:
            log("session error", e)
        finally:
            self.stop_stream()
            try: self.conn.close()
            except OSError: pass
            log("disconnect", self.addr)

    def start_stream(self):
        if self.streaming:
            return
        self.streaming = True
        threading.Thread(target=self._pump, daemon=True).start()
        log("monitor start ->", RTSP_URL)

    def stop_stream(self):
        self.streaming = False

    def _pump(self):
        # The same 720p stream is served on every StreamType (Main + Extra1) - a
        # separate down-scaled sub-stream disagreed with the config the DVR had
        # already read and broke the channel.
        log("pump [%s] start" % self.stream_type)
        q, backlog = HUB.subscribe()
        n_i = n_p = 0
        mseq = 0   # real XM: media packet seq starts at 0 and increments PER PACKET

        def emit(is_key, au):
            nonlocal n_i, n_p, mseq
            frame = media_iframe(au) if is_key else media_pframe(au)
            data, mseq = build_media(self.session, mseq, frame)
            self.send(data)
            if is_key: n_i += 1
            else: n_p += 1

        try:
            # Replay the current GOP (capped, in order -> no frame_num gap) so the
            # DVR re-acquires a picture instantly after its periodic reconnect.
            waiting_key = True
            if backlog and backlog[0][:4] == SC and (backlog[0][4] & 0x1F) in (5, 7):
                for j, au in enumerate(backlog):
                    emit(j == 0, au)
                waiting_key = False
            while self.streaming:
                try:
                    item = q.get(timeout=10)
                except _queue.Empty:
                    log("pump: no frames for 10s"); break
                if item is None:
                    log("pump: dropped by hub (too slow)"); break
                is_key, au = item
                if waiting_key:
                    if not is_key:
                        continue
                    waiting_key = False
                emit(is_key, au)
                if (n_i + n_p) % 600 == 0:
                    log("streamed[%s] I=%d P=%d seq=%d" % (self.stream_type, n_i, n_p, mseq))
        except Exception as e:
            log("pump error", repr(e))
        finally:
            HUB.unsubscribe(q)
            self.streaming = False
            log("pump end [%s] I=%d P=%d" % (self.stream_type, n_i, n_p))


def main():
    global HUB
    HUB = StreamHub("main")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(8)
    log(f"DVR-IP camera server on :{PORT}  src={RTSP_URL}  {WIDTH}x{HEIGHT}@{FPS}")
    while True:
        conn, addr = srv.accept()
        Session(conn, addr).start()

if __name__ == "__main__":
    main()
