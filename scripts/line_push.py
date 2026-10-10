#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LINE公式アカウント(Messaging API)への自動配信。標準ライブラリのみ。

  python3 scripts/line_push.py morning   # today/today.json から朝の1通
  python3 scripts/line_push.py live      # today/fresh_live.json の新しい予定ライブを1通ずつ

鍵は環境変数 LINE_CHANNEL_TOKEN(GitHub Secrets に置く)。無ければ「送ったつもり」の文面だけ表示して終わる(ドライラン)。
文面の型は固定: 絵文字なし・「!」なし・講座やイベントの案内は混ぜない。
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY_JSON = os.path.join(ROOT, "today", "today.json")
FRESH_JSON = os.path.join(ROOT, "today", "fresh_live.json")
TODAY_URL = "https://resonancelink.com/today/"
WEEKDAYS = "月火水木金土日"


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def fmt_dt(iso):
    try:
        d = datetime.fromisoformat(iso).astimezone(JST)
        return f"{d.month}月{d.day}日({WEEKDAYS[d.weekday()]}) {d.hour}時" + (f"{d.minute:02d}分" if d.minute else "")
    except Exception:
        return ""


def morning_text(data):
    lines = ["おはようございます。今日のみちよです。"]
    blog = data.get("blog", {})
    if blog.get("items"):
        t = blog["items"][0]["title"]
        lines.append(f"▷ブログ「{t}」" + ("" if blog.get("is_today") else "（最新）"))
    lines.append("▷Voicy 朝7時の放送")
    for x in data.get("substack", {}).get("items", [])[:2]:
        lines.append(f"▷メルマガ「{x['title']}」")
    for v in data.get("youtube", {}).get("videos", [])[:2]:
        lines.append(f"▷YouTube 新しい動画「{v['title']}」")
    today = data.get("date")
    for v in data.get("youtube", {}).get("live", []):
        st = v.get("start")
        if st and st[:10] == today:
            try:
                d = datetime.fromisoformat(st).astimezone(JST)
                lines.append(f"▷今夜{d.hour}時から YouTubeライブ")
            except Exception:
                lines.append("▷今日 YouTubeライブ")
    lines.append(f"→ {TODAY_URL}")
    return "\n".join(lines)


def live_text(v):
    when = fmt_dt(v.get("start") or "")
    head = f"{when}から、YouTubeライブをします。" if when else "YouTubeライブの予定が入りました。"
    return "\n".join([head, "よかったら、ゆっくりどうぞ。", v["url"]])


def broadcast(text, token):
    body = json.dumps({"messages": [{"type": "text", "text": text}]}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/broadcast", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    token = os.environ.get("LINE_CHANNEL_TOKEN", "").strip()
    data = load(TODAY_JSON, {})
    if not data:
        print("[line] today.json がありません"); return 0

    if mode == "morning":
        texts = [morning_text(data)]
        ids = []
    else:
        fresh = load(FRESH_JSON, [])
        texts = [live_text(v) for v in fresh]
        ids = [v["id"] for v in fresh]
        if not texts:
            print("[line] 新しい予定ライブはありません"); return 0

    sent_ids = []
    for i, text in enumerate(texts):
        print("----- 文面 -----\n" + text + "\n----------------")
        if not token:
            print("[line] LINE_CHANNEL_TOKEN が無いので送信しません(ドライラン)")
            continue
        try:
            st = broadcast(text, token)
            print(f"[line] 送信しました (HTTP {st})")
            if ids:
                sent_ids.append(ids[i])
        except urllib.error.HTTPError as e:
            print(f"[line] 送信失敗 HTTP {e.code}: {e.read().decode('utf-8','ignore')[:300]}")
            return 1
        except Exception as e:
            print(f"[line] 送信失敗: {e}")
            return 1

    if mode == "live" and sent_ids:
        data["notified_live"] = sorted(set(data.get("notified_live", [])) | set(sent_ids))
        with open(TODAY_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
