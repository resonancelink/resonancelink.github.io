/* =====================================================================
   研究所の共通導線(portal-nav.js)
   各アプリ(今日の１枚・魂診断の家・好き診断)や図鑑ページが、この1ファイルを読むだけで
     1) 最上部の「研究所の帯」(研究所のホームへ戻る+ほかの部屋のメニュー)
     2) 結果画面の下の「研究所のほかの部屋」の案内カード
     3) いちばん下の共通フッター(研究所名・配信リンク・運営法人)
   が入る。部屋が増えたら、下の ROOMS に1行足すだけで全アプリに反映される。

   使い方(各ページの </body> の直前、または <head> に1行):
     <script src="https://resonancelink.com/portal-nav.js" defer
             data-app="oracle"                 ← このページがどの部屋か(ROOMS の id)。自分の部屋は案内から外れる
             data-rooms-target="#result #info" ← 案内カードを差し込む場所(CSSセレクタ)。省略時は #mailinvite の手前
             data-bar="on" data-rooms="on" data-footer="on"  ← 各部品の on/off(省略時 on)
     ></script>
   色はページ側の CSS変数(--ink / --bg)を読んでなじませる。
   ===================================================================== */
(() => {
  const HOME = "https://resonancelink.com/";
  const ROOMS = [
    {id:"oracle",   name:"みちよオラクル 今日の１枚", sub:"77枚から、今日の1枚を引く",       url:"https://resonancelink.com/michiyo_oraclecards/"},
    {id:"tamashii", name:"魂診断の家",               sub:"使命・星・種、あなたの魂の来歴",   url:"https://resonancelink.com/tamashii_shindan/"},
    {id:"suki",     name:"自分の「好き！」診断",      sub:"暮らしに眠る「好き」を見つける",   url:"https://resonancelink.com/suki_shindan/"},
    {id:"zukan",    name:"意識の図鑑",               sub:"似ていて違う言葉を、魂の目線で",   url:"https://resonancelink.com/zukan/"},
    {id:"guidance", name:"みちよのガイダンス",        sub:"迷ったとき、不安なときにひらく",   url:"https://resonancelink.com/guidance/"}
  ];
  const LINKS = [
    {t:"公式サイト", u:"https://angelswayhealing.com/"},
    {t:"Voicy",     u:"https://voicy.jp/channel/1756"},
    {t:"YouTube",   u:"https://www.youtube.com/channel/UCM4Cxu05XHKE7H530RbWuYA"},
    {t:"Ameblo",    u:"https://ameblo.jp/michiyo-hikiyose/"},
    {t:"Substack",  u:"https://michiyospiritualcounsellor.substack.com/"}
  ];
  const SEED = '<svg class="pn-sg" viewBox="0 0 100 100" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="50" cy="50" r="11"/><circle cx="50" cy="61" r="11"/><circle cx="40.5" cy="55.5" r="11"/><circle cx="40.5" cy="44.5" r="11"/><circle cx="50" cy="39" r="11"/><circle cx="59.5" cy="44.5" r="11"/><circle cx="59.5" cy="55.5" r="11"/><circle cx="50" cy="72" r="11"/><circle cx="30.9" cy="61" r="11"/><circle cx="30.9" cy="39" r="11"/><circle cx="50" cy="28" r="11"/><circle cx="69.1" cy="39" r="11"/><circle cx="69.1" cy="61" r="11"/><circle cx="69.1" cy="50" r="11"/><circle cx="59.5" cy="66.5" r="11"/><circle cx="40.5" cy="66.5" r="11"/><circle cx="30.9" cy="50" r="11"/><circle cx="40.5" cy="33.5" r="11"/><circle cx="59.5" cy="33.5" r="11"/><circle cx="50" cy="50" r="33" stroke-width="1.4"/><circle cx="50" cy="50" r="35.5" stroke-width="1"/></g></svg>';

  const me = document.currentScript;
  const D = (me && me.dataset) || {};
  const app = D.app || "";
  const on = k => (D[k] || "on") !== "off";

  const css = `
  .pn-bar{position:fixed;top:0;left:0;right:0;z-index:60;background:rgba(255,255,255,.72);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
    border-bottom:1px solid rgba(0,0,0,.06);font-family:inherit;color:var(--ink,#345f69)}
  .pn-spacer{height:44px}
  .pn-bar .pn-in{max-width:1000px;margin:0 auto;display:flex;align-items:center;gap:12px;padding:0 14px;height:44px}
  .pn-bar a{color:inherit;text-decoration:none}
  .pn-home{display:flex;align-items:center;gap:8px;font-size:11.5px;letter-spacing:.16em;white-space:nowrap;opacity:.9}
  .pn-home:hover{opacity:1}
  .pn-sg{width:20px;height:20px;color:#A8687F;flex-shrink:0}
  .pn-home .pn-long{display:none}.pn-home .pn-short{display:inline}
  @media (min-width:600px){.pn-home .pn-long{display:inline}.pn-home .pn-short{display:none}}
  .pn-menu{margin-left:auto;position:relative}
  .pn-menu > button{font-family:inherit;font-size:12px;letter-spacing:.14em;color:inherit;background:none;border:1px solid rgba(0,0,0,.12);
    border-radius:999px;padding:6px 14px;cursor:pointer;opacity:.85}
  .pn-menu > button:hover{opacity:1;border-color:rgba(0,0,0,.25)}
  .pn-menu > button:focus{outline:none}
  .pn-menu > button:focus-visible{outline:2px solid #A8687F;outline-offset:2px}
  .pn-menu ul{position:absolute;right:0;top:calc(100% + 8px);min-width:240px;list-style:none;margin:0;padding:8px;
    background:rgba(255,255,255,.96);border:1px solid rgba(0,0,0,.08);border-radius:16px;box-shadow:0 14px 40px rgba(0,0,0,.10);
    display:none}
  .pn-menu.open ul{display:block}
  .pn-menu li a{display:block;padding:10px 12px;border-radius:10px;font-size:13px;letter-spacing:.06em;line-height:1.5}
  .pn-menu li a small{display:block;font-size:11px;opacity:.65;letter-spacing:.04em}
  .pn-menu li a:hover{background:rgba(168,104,127,.08)}
  .pn-menu li.pn-here a{opacity:.45;pointer-events:none}
  .pn-menu li.pn-top a{font-weight:600}
  .pn-menu li.pn-sep{height:1px;background:rgba(0,0,0,.07);margin:6px 8px}

  .pn-rooms{margin:34px auto 6px;max-width:560px;text-align:center;font-family:inherit;color:var(--ink,#345f69)}
  .pn-rooms .pn-k{font-size:11px;letter-spacing:.34em;text-indent:.34em;opacity:.75;margin-bottom:12px}
  .pn-rooms .pn-k .pn-sg{width:1.6em;height:1.6em;vertical-align:-.45em;margin-right:.35em}
  .pn-rooms .pn-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;text-align:left}
  .pn-rooms a{display:block;padding:12px 14px;border-radius:14px;color:inherit;text-decoration:none;
    background:rgba(255,255,255,.55);border:1px solid rgba(0,0,0,.07);transition:transform .4s cubic-bezier(.22,1,.36,1),box-shadow .4s}
  .pn-rooms .pn-grid a:hover{transform:translateY(-2px);box-shadow:0 10px 26px rgba(0,0,0,.07)}
  .pn-rooms .pn-more:hover{transform:none;box-shadow:none}
  .pn-rooms a b{display:block;font-size:13.5px;font-weight:600;letter-spacing:.04em;line-height:1.5}
  .pn-rooms a span{display:block;font-size:11.5px;opacity:.7;margin-top:2px;line-height:1.5}
  .pn-rooms .pn-more{display:inline-block;margin-top:14px;font-size:12px;letter-spacing:.16em;opacity:.75;
    background:none;border:0;border-bottom:1px solid currentColor;border-radius:0;padding:0 0 2px;box-shadow:none}
  .pn-rooms .pn-more:hover{opacity:1}
  @media (max-width:420px){.pn-rooms .pn-grid{grid-template-columns:1fr}}

  .pn-foot{margin:36px 0 0;padding:26px 16px 30px;background:var(--bg,transparent);text-align:center;font-family:inherit;color:var(--ink,#345f69);
    border-top:1px solid rgba(0,0,0,.06);font-size:11.5px;letter-spacing:.08em;line-height:2.1;opacity:.85}
  .pn-foot a{color:inherit;text-decoration:none;border-bottom:1px solid rgba(0,0,0,.18);padding-bottom:1px;margin:0 6px}
  .pn-foot a:hover{border-bottom-color:currentColor}
  .pn-foot .pn-name{letter-spacing:.28em;margin-bottom:4px}
  .pn-foot .pn-name a{border:none;margin:0}
  .pn-foot .pn-unei{font-size:10.5px;opacity:.85;margin-top:4px}
  /* スマホでは少し大きく・濃く */
  @media (max-width:640px){
    .pn-home{font-size:12.5px;opacity:1}
    .pn-menu > button{font-size:13px;opacity:1}
    .pn-menu li a{font-size:14px}
    .pn-menu li a small{font-size:12px;opacity:.75}
    .pn-rooms .pn-k{font-size:12px;opacity:.9}
    .pn-rooms a b{font-size:14.5px}
    .pn-rooms a span{font-size:12.5px;opacity:.85}
    .pn-rooms .pn-more{font-size:13px;opacity:.9}
    .pn-foot{font-size:13px;opacity:.95}
    .pn-foot .pn-unei{font-size:12px}
  }
  `;

  function el(tag, cls, html){ const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function roomsHtml(exclude){
    return ROOMS.filter(r => r.id !== exclude).map(r => `<a href="${r.url}"><b>${r.name}</b><span>${r.sub}</span></a>`).join("");
  }

  function run(){
    const style = el("style", null, css); document.head.appendChild(style);

    /* 1) 上の帯 */
    if (on("bar")){
      const bar = el("div", "pn-bar");
      const items = [`<li class="pn-top"><a href="${HOME}">研究所のホーム<small>見えない世界を、やさしく紐解く場所</small></a></li>`, `<li class="pn-sep"></li>`]
        .concat(ROOMS.map(r => `<li class="${r.id === app ? "pn-here" : ""}"><a href="${r.url}">${r.name}${r.id === app ? "（いまここ）" : ""}<small>${r.sub}</small></a></li>`));
      bar.innerHTML = `<div class="pn-in">
        <a class="pn-home" href="${HOME}">${SEED}<span class="pn-long">スピリチュアル・メタサイエンス研究所</span><span class="pn-short">研究所のホーム</span></a>
        <div class="pn-menu"><button type="button" aria-expanded="false" aria-haspopup="true">ほかの部屋 ▾</button><ul>${items.join("")}</ul></div>
      </div>`;
      /* 固定の帯(sticky はアプリ側の overflow 指定で効かないことがあるので fixed+同じ高さの余白) */
      document.body.insertBefore(el("div", "pn-spacer"), document.body.firstChild);
      document.body.insertBefore(bar, document.body.firstChild);
      const menu = bar.querySelector(".pn-menu"), btn = menu.querySelector("button");
      btn.addEventListener("click", e => { e.stopPropagation(); const o = menu.classList.toggle("open"); btn.setAttribute("aria-expanded", o); });
      document.addEventListener("click", () => { menu.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); });
      document.addEventListener("keydown", e => { if (e.key === "Escape"){ menu.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); } });
    }

    /* 2) 結果の下の案内 */
    if (on("rooms")){
      const box = el("div", "pn-rooms", `<p class="pn-k">${SEED}研究所のほかの部屋</p><div class="pn-grid">${roomsHtml(app)}</div><a class="pn-more" href="${HOME}">研究所のホームへ →</a>`);
      let target = D.roomsTarget ? document.querySelector(D.roomsTarget) : null;
      if (target){ target.appendChild(box); }
      else { const mi = document.getElementById("mailinvite"); if (mi) mi.parentNode.insertBefore(box, mi); else document.body.appendChild(box); }
    }

    /* 3) 共通フッター */
    if (on("footer")){
      const f = el("div", "pn-foot", `<p class="pn-name"><a href="${HOME}">スピリチュアル・メタサイエンス研究所</a></p>
        <p><a href="${HOME}">研究所のホーム</a>｜${LINKS.map(l => `<a href="${l.u}" target="_blank" rel="noopener">${l.t}</a>`).join("")}</p>
        <p class="pn-unei">運営: <a href="https://spiritualmetascienceacademy.org/" target="_blank" rel="noopener">一般社団法人スピリチュアル・メタサイエンス・アカデミー</a></p>`);
      document.body.appendChild(f);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
