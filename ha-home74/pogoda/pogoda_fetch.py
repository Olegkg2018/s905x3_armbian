#!/usr/bin/env python3
"""Забирает pogoda.co.il и оставляет только блок от заголовка
«Украина / ... / Кривой Рог — Погода сейчас» до абзаца «Следите за изменениями…».
Результат — /local/pogoda.html с прозрачным фоном (iframe карточка вида pogoda3)."""
import os
import re
import sys
import urllib.request

URL = "https://pogoda.co.il/ukraine/kryvyy_rih"
OUT = os.environ.get("OUT", "/config/www/pogoda.html")

START = '<div class="center_block">'
END_MARK = "Следите за изменениями"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

i = html.find(START)
j = html.find(END_MARK)
if i < 0 or j < 0 or j < i:
    sys.exit("pogoda_fetch: разметка сайта изменилась (нет границ), файл не обновлён")
j = html.rfind("<p", i, j)  # начало абзаца с «Следите…»

frag = html[i + len(START):j]
# реклама и скрипты внутри блока не нужны
frag = re.sub(r"<script\b.*?</script>", "", frag, flags=re.S | re.I)
frag = re.sub(r"<ins\b.*?</ins>", "", frag, flags=re.S | re.I)
frag = re.sub(r"<iframe\b.*?</iframe>", "", frag, flags=re.S | re.I)

page = f"""<!doctype html>
<html lang="ru" translate="no"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="https://pogoda.co.il/" target="_blank">
<link rel="stylesheet" href="/style/styleNew.css">
<style>
html,body{{background:transparent!important;margin:0;padding:0}}
.center_block{{width:100%!important;float:none!important;padding:0 8px!important;box-sizing:border-box}}
body,body *{{color:var(--pt,#e1e1e1)!important;background-color:transparent!important;border-color:rgba(128,128,128,.4)!important}}
a{{color:var(--pa,#8ab4f8)!important}}
.hour_block th,.hour_block td,i,.dashed span{{opacity:.85}}
</style>
<script>
try{{var s=getComputedStyle(parent.document.documentElement),r=document.documentElement.style;
var t=s.getPropertyValue('--primary-text-color').trim(),a=s.getPropertyValue('--primary-color').trim();
if(t)r.setProperty('--pt',t);if(a)r.setProperty('--pa',a);}}catch(e){{}}
</script></head><body>
<div class="center_block">{frag}</div>
</body></html>
"""

tmp = OUT + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(page)
os.replace(tmp, OUT)
