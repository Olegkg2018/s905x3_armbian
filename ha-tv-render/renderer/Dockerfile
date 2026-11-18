FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium xvfb x11-utils x11-xserver-utils ffmpeg ca-certificates curl tini procps \
      fonts-noto-core fonts-noto-cjk fonts-noto-color-emoji fonts-liberation2 \
      python3 python3-websocket \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY run.py /run.py
ENV HA_URL=http://192.168.2.14:8123 \
    DASH_PATH=/dashboard-tv/0?kiosk \
    RTSP_URL=rtsp://192.168.2.14:8554/tv \
    WIDTH=1280 HEIGHT=720 FPS=4 BITRATE=900k
ENTRYPOINT ["/usr/bin/tini","--","python3","-u","/run.py"]
