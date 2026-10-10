#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「今日のみちよ」欄の自動更新(標準ライブラリのみ・GitHub Actionsで毎朝7:20 JSTに実行)。

各媒体の新着を読んで today/today.json を書く。
  - Ameblo  : RSS(rssblog.ameba.jp)から今日の記事
  - Voicy   : 毎朝7時更新の固定リンク(一覧は自動で読めないため)
  - Substack: RSS(/feed)から直近24時間の記事(弾かれたら前回の内容を残す)
  - YouTube : チャンネルRSS → 各動画ページで「ショート/動画/ライブ(予定・配信中)」を判定

使い方:
  python3 scripts/update_today.py            # 朝の更新(全媒体)
  python3 scripts/update_today.py --live     # ライブ予約の見張りだけ(1時間おき)
終了コード 0=更新あり/変更なしとも正常。致命的な失敗のみ 1。
"""
import json, os, re, sys, time, html, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY_JSON = os.path.join(ROOT, "today", "today.json")

AMEBLO_RSS = "https://rssblog.ameba.jp/michiyo-hikiyose/rss20.xml"
AMEBLO_TOP = "https://ameblo.jp/michiyo-hikiyose/"
VOICY_URL = "https://voicy.jp/channel/1756"
SUBSTACK_FEED = "https://michiyospiritualcounsellor.substack.com/feed"
SUBSTACK_TOP = "https://michiyospiritualcounsellor.substack.com/"
from datetime import date as _date
SERIAL_START = _date(2026, 7, 18)   # 連載 第1回(土)
SERIAL_END = _date(2026, 12, 26)    # 第24回
YT_CHANNEL_ID = "UCM4Cxu05XHKE7H530RbWuYA"
YT_FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_CHANNEL_ID}"
YT_CHANNEL_URL = f"https://www.youtube.com/channel/{YT_CHANNEL_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def log(*a):
    print("[today]", *a, flush=True)


def fetch(url, tries=3, timeout=30):
    last = ""
    for i in range(tries):
        if i:
            time.sleep(10 * i)
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code not in (403, 429, 500, 502, 503, 504):
                break
        except Exception as e:  # URLError, timeout
            last = str(e)
    log(f"取得失敗 {url} ({last})")
    return None


def parse_rfc822(s):
    """RSSのpubDate(RFC822)をJSTのdatetimeに。失敗ならNone"""
    from email.utils import parsedate_to_datetime
    try:
        d = parsedate_to_datetime(s.strip())
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(JST)
    except Exception:
        return None


def parse_iso(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(JST)
    except Exception:
        return None


# ---------------- Ameblo ----------------
def get_ameblo(now):
    raw = fetch(AMEBLO_RSS)
    if not raw:
        return None
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        log("Ameblo RSS が読めませんでした")
        return None
    items = []
    for it in root.findall("./channel/item"):
        title = html.unescape((it.findtext("title") or "").strip())
        link = (it.findtext("link") or "").strip().split("?")[0]
        d = parse_rfc822(it.findtext("pubDate") or "")
        if title and link:
            items.append({"title": title, "url": link, "date": d.isoformat() if d else None})
    today = now.date()
    todays = [x for x in items if x["date"] and parse_iso(x["date"]).date() == today]
    if todays:
        return {"items": todays, "is_today": True}
    if items:  # 今日の記事がまだ無い日は最新1件を「最新」として
        return {"items": items[:1], "is_today": False}
    return None


# ---------------- Substack ----------------
def get_substack(now, hours=26):
    raw = fetch(SUBSTACK_FEED, tries=4, timeout=40)
    if not raw:
        return None  # 弾かれた → 呼び出し側で前回の内容を残す
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    out, week = [], None
    for it in root.findall("./channel/item"):
        title = html.unescape((it.findtext("title") or "").strip())
        link = (it.findtext("link") or "").strip().split("?")[0]
        d = parse_rfc822(it.findtext("pubDate") or "")
        if not (d and title and link):
            continue
        if (now - d) <= timedelta(hours=hours):
            out.append({"title": title, "url": link, "date": d.isoformat()})
        if week is None and (now - d) <= timedelta(days=8):
            week = {"title": title, "url": link, "date": d.isoformat()}  # 「今週のメルマガ」(最新・8日以内)
    return {"items": out, "week": week}


# ---------------- YouTube ----------------
def yt_video_info(video_id):
    """動画ページから種類を判定する。戻り: dict(kind=short|video|live_upcoming|live_now|live_ended, start=iso or None, length=int)"""
    raw = fetch(f"https://www.youtube.com/watch?v={video_id}", tries=2, timeout=30)
    if not raw:
        return None
    s = raw.decode("utf-8", "ignore")
    info = {"kind": "video", "start": None, "length": None}
    m = re.search(r'"lengthSeconds":"(\d+)"', s)
    if m:
        info["length"] = int(m.group(1))
    live_block = re.search(r'"liveBroadcastDetails":\{([^}]*)\}', s)
    is_live_content = '"isLiveContent":true' in s
    if live_block:
        b = live_block.group(1)
        st = re.search(r'"startTimestamp":"([^"]+)"', b)
        en = re.search(r'"endTimestamp":"([^"]+)"', b)
        is_now = '"isLiveNow":true' in b
        if st:
            info["start"] = parse_iso(st.group(1)).isoformat() if parse_iso(st.group(1)) else st.group(1)
        if is_now:
            info["kind"] = "live_now"
        elif en:
            info["kind"] = "live_ended"
        elif st and parse_iso(st.group(1)) and parse_iso(st.group(1)) > datetime.now(JST):
            info["kind"] = "live_upcoming"
        elif is_live_content:
            info["kind"] = "live_ended"
    elif '"isUpcoming":true' in s:
        info["kind"] = "live_upcoming"
    elif is_live_content:
        info["kind"] = "live_ended"
    elif info["length"] is not None and info["length"] <= 60 and info["length"] > 0:
        info["kind"] = "short"
    return info


def get_youtube(now, max_check=8):
    raw = fetch(YT_FEED, tries=3, timeout=30)
    if not raw:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    entries = []
    for e in root.findall("a:entry", ns)[:max_check]:
        vid = e.findtext("yt:videoId", namespaces=ns)
        title = html.unescape((e.findtext("a:title", namespaces=ns) or "").strip())
        pub = parse_iso(e.findtext("a:published", namespaces=ns) or "")
        if not vid:
            continue
        info = yt_video_info(vid) or {"kind": "video", "start": None, "length": None}
        time.sleep(1.5)
        entries.append({
            "id": vid, "title": title, "url": f"https://www.youtube.com/watch?v={vid}",
            "published": pub.isoformat() if pub else None, **info,
        })
    return {"items": entries}


# ---------------- 組み立て ----------------
def load_prev():
    try:
        with open(TODAY_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def build_morning(now):
    prev = load_prev()
    data = {
        "date": now.strftime("%Y-%m-%d"),
        "updated": now.isoformat(timespec="minutes"),
        "blog": {"items": [], "is_today": False, "top": AMEBLO_TOP},
        "voicy": {"url": VOICY_URL, "note": "毎朝7時更新"},
        "substack": {"items": []},
        "youtube": {"videos": [], "live": [], "channel": YT_CHANNEL_URL},
        "notified_live": prev.get("notified_live", []),
    }
    # GitHubの定時実行は遅れるので朝の便は6:50に起動し、今日のブログ(7:00公開)が出るまで最大 WAIT_UNTIL まで粘る
    am = get_ameblo(now)
    deadline = now.replace(hour=7, minute=30, second=0, microsecond=0)
    while (not am or not am.get("is_today")) and datetime.now(JST) < deadline and os.environ.get("TODAY_NO_WAIT") != "1":
        log("今日のブログがまだ無いので2分待つ")
        time.sleep(120)
        am = get_ameblo(datetime.now(JST))
    if am:
        data["blog"].update(am)
    else:
        data["blog"]["items"] = prev.get("blog", {}).get("items", [])
        data["blog"]["is_today"] = False
        data["blog"]["stale"] = True

    # Substack は毎朝8時配信(7:20時点では未公開)なので取りに行かず、曜日ルールで載せる(本人決定 2026-10-10)
    #   土曜 = 連載 第N回(7/18起点・12/26の第24回まで) / 火曜 = 今週のお便り / それ以外 = 行なし
    wd = now.weekday()
    sub_items = []
    if wd == 5 and SERIAL_START <= now.date() <= SERIAL_END:
        n = (now.date() - SERIAL_START).days // 7 + 1
        sub_items = [{"title": f"連載 第{n}回『AIに悩みを話せる時代に、それでも自分と対話する理由』", "url": SUBSTACK_TOP,
                      "date": now.replace(hour=8, minute=0).isoformat(timespec="minutes"), "by_rule": True}]
    elif wd == 1:
        sub_items = [{"title": "今週のお便り", "url": SUBSTACK_TOP,
                      "date": now.replace(hour=8, minute=0).isoformat(timespec="minutes"), "by_rule": True}]
    # 「今週のメルマガ」(/today/ の見出し用)は直近の土曜の連載を8日間残す
    week = None
    days_since_sat = (wd - 5) % 7
    last_sat = now.date() - timedelta(days=days_since_sat)
    if SERIAL_START <= last_sat <= SERIAL_END:
        n = (last_sat - SERIAL_START).days // 7 + 1
        week = {"title": f"連載 第{n}回", "url": SUBSTACK_TOP, "date": last_sat.isoformat()}
    data["substack"] = {"items": sub_items, "week": week}

    yt = get_youtube(now)
    if yt is not None:
        day = timedelta(hours=26)
        for v in yt["items"]:
            pub = parse_iso(v["published"] or "")
            if v["kind"] in ("live_upcoming", "live_now"):
                data["youtube"]["live"].append(v)
            # short は欄に出さない(本人の指示 2026-10-10)
            elif v["kind"] == "video":
                if pub and (now - pub) <= day:
                    data["youtube"]["videos"].append(v)
            # live_ended は欄に出さない
    else:
        data["youtube"] = prev.get("youtube", data["youtube"])
        data["youtube"]["stale"] = True
    return data


def build_live_only(now):
    """1時間おき: YouTubeの予定ライブだけ見直し、today.json の youtube.live を更新する"""
    data = load_prev()
    if not data:
        data = build_morning(now)
        return data, []
    yt = get_youtube(now, max_check=6)
    if yt is None:
        return data, []
    live = [v for v in yt["items"] if v["kind"] in ("live_upcoming", "live_now")]
    data.setdefault("youtube", {})["live"] = live
    data["updated"] = now.isoformat(timespec="minutes")
    notified = set(data.get("notified_live", []))
    fresh = [v for v in live if v["kind"] == "live_upcoming" and v["id"] not in notified]
    return data, fresh


def save(data):
    os.makedirs(os.path.dirname(TODAY_JSON), exist_ok=True)
    with open(TODAY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main():
    now = datetime.now(JST)
    live_mode = "--live" in sys.argv
    if live_mode:
        data, fresh = build_live_only(now)
        # 新しく見つかった予定ライブは line_push.py が通知し、通知後に notified_live に追記する
        with open(os.path.join(ROOT, "today", "fresh_live.json"), "w", encoding="utf-8") as f:
            json.dump(fresh, f, ensure_ascii=False)
        save(data)
        log(f"ライブ見張り: 予定{len(data.get('youtube',{}).get('live',[]))}件・新規{len(fresh)}件")
    else:
        data = build_morning(now)
        save(data)
        b = data["blog"]["items"]
        log("朝の更新:", (b[0]["title"] if b else "ブログなし"),
            f"/ Substack {len(data['substack']['items'])}件 / 動画{len(data['youtube']['videos'])} ライブ{len(data['youtube']['live'])}")


if __name__ == "__main__":
    main()
