#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「今週のメルマガ」欄の自動更新。
SubstackのRSS(feed)から最新記事を読み、index.html の const WEEKLY = {...}; を書き換える。
標準ライブラリのみ。失敗したら index.html は触らず、終了コード1で止まる(前回の内容が残る)。
使い方: python3 scripts/update_weekly.py [index.html]
"""
import html, json, re, sys, time, urllib.error, urllib.request, xml.etree.ElementTree as ET

FEED = "https://michiyospiritualcounsellor.substack.com/feed"
INDEX = sys.argv[1] if len(sys.argv) > 1 else "index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

def fetch(url):
    # Substack(Cloudflare)がデータセンターIPを弾くことがあるので、間隔をあけて再試行する
    last = ""
    for i in range(4):
        if i:
            time.sleep(15 * i)
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code not in (403, 429, 500, 502, 503, 504):
                raise
        except urllib.error.URLError as e:
            last = str(e.reason)
    raise SystemExit(f"feedの取得に失敗しました({last})")

def strip_tags(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</p>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return s

def pick_excerpt(body_html, max_chars=170):
    text = strip_tags(body_html)
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    out = []
    for p in paras:
        if p.startswith("前回") or "前回は" in p[:12]:   # 振り返り文は飛ばす
            continue
        if p.startswith("（") and p.endswith("）"):        # 補足のカッコ書きも飛ばす
            continue
        if re.match(r"^[\W_]+$", p):
            continue
        out.append(p)
        if sum(len(x) for x in out) >= max_chars:
            break
    s = "".join(out)[:max_chars + 40]
    if not s.endswith(("。", "」", "）", "！", "？", "!", "?")):   # 文の途中で終わらせない
        cut = max(s.rfind(x) for x in ("。", "」", "！", "？"))
        if cut > 40: s = s[:cut + 1]
    return s

def parse(feed_xml):
    root = ET.fromstring(feed_xml)
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
    items = root.findall("./channel/item")
    if not items:
        raise SystemExit("feedにitemがありません")
    # 連載(タイトルが「第N回」で始まる)を優先。無ければ最新記事
    def ep_of(it):
        t = (it.findtext("title") or "").strip()
        m = re.match(r"第\s*(\d+)\s*回", t)
        return int(m.group(1)) if m else None
    serial = [it for it in items if ep_of(it) is not None]
    it = max(serial, key=ep_of) if serial else items[0]
    title = (it.findtext("title") or "").strip()
    link = (it.findtext("link") or "").strip().split("?")[0]
    body = it.findtext("content:encoded", namespaces=ns) or it.findtext("description") or ""
    m = re.match(r"第\s*(\d+)\s*回\s*(.*)", title)
    ep = f"第{m.group(1)}回" if m else ""
    title_clean = m.group(2).strip() if m else title
    return {"ep": ep, "title": title_clean, "url": link, "excerpt": pick_excerpt(body)}

def render(w):
    j = lambda s: json.dumps(s, ensure_ascii=False)
    return ("const WEEKLY = {\n"
            f"  ep: {j(w['ep'])},\n"
            f"  title: {j(w['title'])},\n"
            f"  url: {j(w['url'])},\n"
            f"  excerpt: {j(w['excerpt'])}\n"
            "};")

def main():
    w = parse(fetch(FEED))
    if not w["title"] or not w["url"] or len(w["excerpt"]) < 20:
        raise SystemExit(f"取得内容が不十分です: {w}")
    src = open(INDEX, encoding="utf-8").read()
    new, n = re.subn(r"const WEEKLY = \{.*?\};", render(w), src, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("index.html に const WEEKLY = {...}; が見つかりません")
    if new == src:
        print("変更なし:", w["ep"], w["title"]); return
    open(INDEX, "w", encoding="utf-8").write(new)
    print("更新:", w["ep"], w["title"], w["url"])

if __name__ == "__main__":
    main()
