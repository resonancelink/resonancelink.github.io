#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LINE公式アカウント(Messaging API)への自動配信。標準ライブラリのみ。

  python3 scripts/line_push.py morning   # today/today.json から朝の1通
  python3 scripts/line_push.py live      # today/fresh_live.json の新しい予定ライブを1通ずつ

鍵は環境変数 LINE_CHANNEL_TOKEN(GitHub Secrets に置く)。無ければ「送ったつもり」の文面だけ表示して終わる(ドライラン)。
文面の型は固定: 絵文字なし・「!」なし・講座やイベントの案内は混ぜない。
"""
import json, os, sys, time, uuid, urllib.request, urllib.error
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
        if x.get("by_rule") and x["title"].startswith("連載"):
            lines.append(f"▷メルマガ {x['title']}（8時に配信）")
        elif x.get("by_rule"):
            lines.append(f"▷メルマガ {x['title']}")
        else:
            lines.append(f"▷メルマガ「{x['title']}」")
    for v in data.get("youtube", {}).get("videos", [])[:2]:
        lines.append(f"▷YouTube 新しい動画「{v['title']}」")
    today = data.get("date")
    for v in data.get("youtube", {}).get("live", []):
        st = v.get("start")
        if st and st[:10] == today:
            try:
                d = datetime.fromisoformat(st).astimezone(JST)
                when = "今夜" if d.hour >= 18 else "今日"
                mm = f"{d.minute:02d}分" if d.minute else ""
                lines.append(f"▷{when}{d.hour}時{mm}から YouTubeライブ")
            except Exception:
                lines.append("▷今日 YouTubeライブ")
    lines.append(f"→ {TODAY_URL}")
    return "\n".join(lines)


def live_text(v):
    when = fmt_dt(v.get("start") or "")
    head = f"{when}から、YouTubeライブをします。" if when else "YouTubeライブの予定が入りました。"
    return "\n".join([head, "よかったら、ゆっくりどうぞ。", v["url"]])


def retry_key(seed):
    """同じ内容を二度送らないための鍵(LINEの X-Line-Retry-Key)。
    朝の1通は「その日付」、ライブ通知は「その動画ID」から毎回同じUUIDを作るので、
    通信エラーや再実行で同じ便をもう一度送っても、LINE側で1通にまとめられる。"""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://resonancelink.com/today/line/" + seed))


def broadcast(text, token, key, tries=4):
    """送信。失敗しても諦めずに少し待って再送する(最大 tries 回)。
    戻り: HTTPステータス。409(同じ鍵で送信済み)は「もう届いている」ので成功扱い。"""
    body = json.dumps({"messages": [{"type": "text", "text": text}]}).encode("utf-8")
    last = None
    for i in range(tries):
        if i:
            time.sleep(15 * i)
        req = urllib.request.Request(
            "https://api.line.me/v2/bot/message/broadcast", data=body, method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}",
                     "X-Line-Retry-Key": key})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:300]
            if e.code == 409:
                print(f"[line] 同じ鍵で送信済み(HTTP 409) → 届いているので成功扱い: {detail}")
                return 409
            print(f"[line] 送信失敗 HTTP {e.code} ({i+1}/{tries}): {detail}")
            last = e
            if e.code == 429 and "monthly limit" in detail:
                print("[line] LINE公式アカウントの月間メッセージ上限に到達。再実行しても送れません → プランの確認(LINE Official Account Manager → 設定 → 利用と請求)")
                raise
            if e.code in (400, 401, 403, 404):   # 鍵が無効・文面が不正など、待っても直らないもの
                raise
        except Exception as e:
            print(f"[line] 送信失敗 ({i+1}/{tries}): {e}")
            last = e
    raise last


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    token = os.environ.get("LINE_CHANNEL_TOKEN", "").strip()
    data = load(TODAY_JSON, {})
    if not data:
        print("[line] today.json がありません"); return 0

    if mode == "morning":
        texts = [morning_text(data)]
        ids = []
        keys = [retry_key("morning/" + str(data.get("date", "")))]
    else:
        fresh = load(FRESH_JSON, [])
        texts = [live_text(v) for v in fresh]
        ids = [v["id"] for v in fresh]
        keys = [retry_key("live/" + v["id"]) for v in fresh]
        if not texts:
            print("[line] 新しい予定ライブはありません"); return 0

    sent_ids = []
    for i, text in enumerate(texts):
        print("----- 文面 -----\n" + text + "\n----------------")
        if not token:
            print("[line] LINE_CHANNEL_TOKEN が無いので送信しません(ドライラン)")
            continue
        try:
            st = broadcast(text, token, keys[i])
            print(f"[line] 送信しました (HTTP {st})")
            if ids:
                sent_ids.append(ids[i])
        except Exception as e:
            print(f"[line] 送信を諦めました: {e}")
            return 1

    if mode == "live" and sent_ids:
        data["notified_live"] = sorted(set(data.get("notified_live", [])) | set(sent_ids))
        with open(TODAY_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
