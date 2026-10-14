#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LINE公式アカウントの「今月の残り通数」を確認して today/today.json に書き残す。標準ライブラリのみ。

  python3 scripts/line_quota.py

背景: 2026-10-15、無料プラン(月200通)の上限に達して朝の1通が送れなくなった(HTTP 429 "monthly limit")。
GitHubを何度起動しても直らない種類の失敗なので、毎回の便で残り通数を確認し、
「このペースだと月末まで足りない」と分かった時点で知らせる(通知そのものは Claude の保険①が today.json を読んで行う)。

LINE Messaging API:
  GET /v2/bot/message/quota              → {"type":"limited","value":5000}  (無制限なら {"type":"none"})
  GET /v2/bot/message/quota/consumption  → {"totalUsage": 1234}            (今月すでに使った通数。月初に0に戻る)

today.json に書くもの(line_quota):
  limit / used / remaining  今月の上限・使用済み・残り(通)
  daily_est                 1日あたりの消費の見込み(直近の記録から)。1回の配信 = 友だち数分の通数
  days_left                 今日を含む月末までの日数
  need_est                  月末まで同じペースで送るのに必要な通数
  status                    ok / warn(足りない見込み・残り1週間分未満) / stop(残り0) / unknown(確認できず)
  message                   人が読める一行
  history                   {日付: その日に確認した使用済み通数}(直近14日分)
鍵は環境変数 LINE_CHANNEL_TOKEN。無ければ何も書かずに終わる。失敗しても便は止めない(常に終了コード0)。
"""
import calendar, json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY_JSON = os.path.join(ROOT, "today", "today.json")
API = "https://api.line.me/v2/bot/message/quota"
HISTORY_DAYS = 14
WARN_DAYS = 7          # 残りが「1週間分」を切ったら warn


def get_json(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_quota(token):
    q = get_json(API, token)
    c = get_json(API + "/consumption", token)
    limit = q.get("value") if q.get("type") == "limited" else None
    return limit, int(c.get("totalUsage", 0))


def estimate(history, today, used, day):
    """直近の記録から1日あたりの消費を見積もる。記録が1日分しか無ければ 使用済み÷経過日数。"""
    pts = sorted((d, u) for d, u in history.items() if d[:7] == today[:7] and d <= today)
    deltas = []
    for (d0, u0), (d1, u1) in zip(pts, pts[1:]):
        gap = (datetime.fromisoformat(d1) - datetime.fromisoformat(d0)).days
        if gap > 0 and u1 >= u0:
            deltas.append((u1 - u0) / gap)
    if deltas:
        return round(sum(deltas[-7:]) / len(deltas[-7:]), 1)
    if day > 1 and used > 0:
        return round(used / (day - 1), 1)
    return None


def assess(limit, used, data, now):
    today = now.strftime("%Y-%m-%d")
    day = now.day
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_left = days_in_month - day + 1                      # 今日を含む
    sent_today = data.get("date") == today                   # 朝の1通が今日の分まで済んでいるか
    q = dict(data.get("line_quota") or {})
    history = {d: u for d, u in (q.get("history") or {}).items() if d[:7] == today[:7]}
    history[today] = used
    history = dict(sorted(history.items())[-HISTORY_DAYS:])

    out = {"checked": now.isoformat(timespec="minutes"), "limit": limit, "used": used,
           "history": history}
    if limit is None:
        out.update(remaining=None, daily_est=None, days_left=days_left, need_est=None,
                   status="ok", message="このアカウントは月間の通数上限なし")
        return out

    remaining = max(limit - used, 0)
    daily = estimate(history, today, used, day)
    send_days = days_left - (1 if sent_today else 0)          # これから送る回数(今日の分が済んでいれば今日は数えない)
    need = round(daily * send_days) if daily is not None else None
    out.update(remaining=remaining, daily_est=daily, days_left=days_left, need_est=need)

    base = f"LINE残り {remaining:,}通 / {limit:,}通(使用 {used:,})"
    if remaining <= 0:
        status, msg = "stop", base + "。上限に到達。今月はこれ以上送れません(プラン変更か月初のリセット待ち)"
    elif daily is None:
        status = "warn" if remaining < limit * 0.2 else "ok"
        msg = base + "。消費ペースはまだ計算できません(記録が1日分)"
    else:
        pace = f"1日約{daily:,.0f}通×あと{send_days}回≒{need:,}通必要"
        if remaining < need:
            short = need - remaining
            status, msg = "warn", base + f"。{pace} → 約{short:,}通足りない見込み。プランの見直しが必要"
        elif remaining < daily * WARN_DAYS:
            status, msg = "warn", base + f"。{pace} → 残りが1週間分を切りました"
        else:
            status, msg = "ok", base + f"。{pace} → 足りる見込み"
    out.update(status=status, message=msg)
    return out


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    token = os.environ.get("LINE_CHANNEL_TOKEN", "").strip()
    if not token:
        print("[quota] LINE_CHANNEL_TOKEN が無いので残り通数は確認しません"); return 0
    data = load(TODAY_JSON, {})
    if not data:
        print("[quota] today.json がありません"); return 0
    now = datetime.now(JST)
    try:
        limit, used = fetch_quota(token)
        q = assess(limit, used, data, now)
    except Exception as e:
        q = dict(data.get("line_quota") or {})
        q.update(checked=now.isoformat(timespec="minutes"), status="unknown",
                 message=f"残り通数を確認できませんでした: {str(e)[:120]}")
        print(f"[quota] 確認失敗: {e}")
    data["line_quota"] = q
    with open(TODAY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write("\n")
    print(f"[quota] {q['status']}: {q['message']}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"- LINE残り通数: **{q['status']}** — {q['message']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
