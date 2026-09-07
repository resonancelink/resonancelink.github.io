# スピリチュアル・メタサイエンス研究所 — 公開用一式

resonancelink.com として GitHub Pages で公開するためのファイル一式です。

## 中身
- `index.html` … ポータル本体(1ファイル完結・画像内蔵)
- `og.jpg` … シェア時の画像(OGP)
- `guidance/index.html` … みちよのガイダンス
- `CNAME` … 独自ドメイン(resonancelink.com)の設定ファイル。消さない
- `.nojekyll` … GitHub Pagesにそのまま配信させる印
- `.github/workflows/weekly-substack.yml` + `scripts/update_weekly.py` … 毎週土曜に「今週のメルマガ」欄を自動更新

## 公開手順(1回だけ)
1. GitHub(アカウント resonancelink)で新しいリポジトリ「resonancelink.github.io」を Public で作る
2. この一式のファイルをすべてアップロードする(ファイルだけでなく `.github` と `guidance` のフォルダ構成ごと)
3. Settings → Pages: Source = Deploy from a branch / Branch = main / (root) → Save
4. 同じ画面の Custom domain に `resonancelink.com` を入れて Save。「Enforce HTTPS」は反映後にオンにする
5. お名前.com の DNS設定で resonancelink.com に次を入れる
   - A レコード(4つ): 185.199.108.153 / 185.199.109.153 / 185.199.110.153 / 185.199.111.153
   - CNAME: www → resonancelink.github.io
6. 反映(数分〜数時間)後、https://resonancelink.com/ で表示を確認。
   既存アプリも https://resonancelink.com/michiyo_oraclecards/ などで開けるようになる

## 自動更新の確認
Actions タブ → 「今週のメルマガ欄を更新(Substack)」→ Run workflow で手動実行できる。
成功すると index.html の WEEKLY が最新記事に書き換わり、数分で公開に反映される。

## 手で直すとき
`index.html` の `const WEEKLY = {...};` の4行(ep/title/url/excerpt)を書き換えるだけ。
「意識の図鑑」の追加は `const BREAKDOWN = [...]` に1項目足す。
