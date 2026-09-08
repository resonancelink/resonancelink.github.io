/* 水面シミュレーション(トップページ index.html 内のものと同じ計算)。
   図鑑ページなど、トップ以外のページから <script src="../water.js"> で使う。
   使い方: createWater(canvasElement, {image:"../water.jpg", flakes:true/false, hover:65, click:420, ambient:true})
   ※ トップページは1ファイル完結のため、同じ関数を index.html の中に持っている(直すときは両方) */
function createWater(canvas, opts){
  const HERO_IMG = opts.image;
  const ctx = canvas.getContext('2d');
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const SIM_W = 420; let SIM_H = 236;
  let cur, prev, simCanvas, simCtx, srcData, outData, img = new Image();

  let ready = false;   /* 写真が読み込めてから true。それまでは何も描かない(黒い水面が出ないように) */
  function fit(){
    /* iPhoneは読み込み直後に resize が飛んでくる。写真が届く前に呼ばれると真っ黒な水面を作ってしまうので、その時は何もしない */
    if (!img.complete || !img.naturalWidth) return;
    canvas.width  = canvas.clientWidth  = canvas.parentElement.clientWidth;
    canvas.height = canvas.clientHeight = canvas.parentElement.clientHeight;
    SIM_H = Math.max(90, Math.round(SIM_W * canvas.height / canvas.width));
    cur  = new Float32Array(SIM_W * SIM_H);
    prev = new Float32Array(SIM_W * SIM_H);
    simCanvas = document.createElement('canvas');
    simCanvas.width = SIM_W; simCanvas.height = SIM_H;
    simCtx = simCanvas.getContext('2d');
    const s = Math.max(SIM_W / img.width, SIM_H / img.height);
    const dw = img.width * s, dh = img.height * s;
    simCtx.drawImage(img, (SIM_W - dw) / 2, (SIM_H - dh) / 2, dw, dh);
    srcData = simCtx.getImageData(0, 0, SIM_W, SIM_H);
    outData = simCtx.createImageData(SIM_W, SIM_H);
  }

  function drop(nx, ny, strength = 260, radius = 2){
    const cx = Math.round(nx * SIM_W), cy = Math.round(ny * SIM_H);
    for (let y = cy - radius; y <= cy + radius; y++)
      for (let x = cx - radius; x <= cx + radius; x++)
        if (x > 1 && x < SIM_W - 1 && y > 1 && y < SIM_H - 1)
          prev[y * SIM_W + x] -= strength;
  }

  function step(){
    for (let y = 1; y < SIM_H - 1; y++){
      const row = y * SIM_W;
      for (let x = 1; x < SIM_W - 1; x++){
        const i = row + x;
        cur[i] = ((prev[i-1] + prev[i+1] + prev[i-SIM_W] + prev[i+SIM_W]) / 2 - cur[i]) * 0.972;
      }
    }
    [cur, prev] = [prev, cur];
  }

  function render(){
    const s = srcData.data, o = outData.data;
    for (let y = 1; y < SIM_H - 1; y++){
      for (let x = 1; x < SIM_W - 1; x++){
        const i = y * SIM_W + x;
        const dx = (prev[i-1] - prev[i+1]) * 0.012;
        const dy = (prev[i-SIM_W] - prev[i+SIM_W]) * 0.012;
        let sx = Math.min(SIM_W - 1, Math.max(0, x + dx | 0));
        let sy = Math.min(SIM_H - 1, Math.max(0, y + dy | 0));
        const si = (sy * SIM_W + sx) * 4, oi = i * 4;
        const light = prev[i] * 0.045;
        o[oi]   = s[si]   + light;
        o[oi+1] = s[si+1] + light;
        o[oi+2] = s[si+2] + light;
        o[oi+3] = 255;
      }
    }
    simCtx.putImageData(outData, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(simCanvas, 0, 0, canvas.width, canvas.height);
  }

  const flakes = [];
  function spawnFlake(){
    flakes.push({
      x: 0.15 + Math.random() * 0.7,
      y: -0.02,
      vy: 0.00045 + Math.random() * 0.0004,
      drift: (Math.random() - 0.5) * 0.0004,
      size: 1.6 + Math.random() * 2.2,
      end: 0.55 + Math.random() * 0.22
    });
  }
  function drawFlakes(){
    ctx.save();
    for (let i = flakes.length - 1; i >= 0; i--){
      const f = flakes[i];
      f.y += f.vy; f.x += f.drift;
      const px = f.x * canvas.width, py = f.y * canvas.height;
      const fade = Math.max(0, Math.min(1, (f.end - f.y) / 0.05));
      ctx.globalAlpha = 0.75 * Math.min(1, fade + 0.15);
      ctx.fillStyle = '#ffffff';
      ctx.shadowColor = '#ffffff'; ctx.shadowBlur = 6;
      ctx.beginPath(); ctx.arc(px, py, f.size * fade + 0.4, 0, Math.PI * 2); ctx.fill();
      if (f.y >= f.end){ drop(f.x, f.y, 140, 1); flakes.splice(i, 1); }
    }
    ctx.restore();
  }

  let last = 0;
  canvas.parentElement.addEventListener('pointermove', e => {
    if (reduceMotion) return;
    const now = performance.now();
    if (now - last < 110) return;
    last = now;
    const r = canvas.getBoundingClientRect();
    drop((e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height, opts.hover, 1);
  });
  canvas.parentElement.addEventListener('pointerdown', e => {
    const r = canvas.getBoundingClientRect();
    drop((e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height, opts.click, 3);
  });
  document.querySelectorAll(opts.circles || '.__none__').forEach(card => {
    card.addEventListener('pointerenter', () => {
      const r = canvas.getBoundingClientRect(), c = card.getBoundingClientRect();
      drop((c.left + c.width / 2 - r.left) / r.width,
           (c.top + c.height / 2 - r.top) / r.height, 520, 3);
    });
  });

  let flakeTimer = 0, frame = 0, visible = true, running = false;
  /* HEROが画面外なら止める(電池・発熱の配慮)。ループは常に1本だけ(2本走ると水面が2倍速になる) */
  if ('IntersectionObserver' in window){
    new IntersectionObserver(es => {
      visible = es[0].isIntersecting;
      if (visible && !running && ready) requestAnimationFrame(loop);
    }, {threshold:0}).observe(canvas.parentElement);
  }
  let ambientTimer = 120;
  function loop(){
    if (!visible){ running = false; return; }
    running = true;
    if (frame++ % 5 === 0) step();
    if (opts.ambient && !reduceMotion && --ambientTimer <= 0){   /* ときどき、ひとりでに小さな波紋 */
      drop(0.1 + Math.random() * 0.8, 0.2 + Math.random() * 0.6, 170, 2);
      ambientTimer = 150 + Math.random() * 220;
    }
    render();
    if (!reduceMotion && opts.flakes){
      drawFlakes();
      if (--flakeTimer <= 0){ spawnFlake(); flakeTimer = 140 + Math.random() * 200; }
    }
    requestAnimationFrame(loop);
  }

  /* 開いた瞬間から動いているように: 雪を数片あらかじめ降らせ、最初の波紋を1つ落とす */
  function warmStart(){
    if (reduceMotion || !opts.flakes) return;
    for (let k = 0; k < 4; k++){ spawnFlake(); const f = flakes[flakes.length - 1]; f.y = 0.08 + Math.random() * 0.45; }
    flakeTimer = 60 + Math.random() * 80;
    setTimeout(() => drop(0.5 + (Math.random() - .5) * 0.3, 0.68, 260, 2), 350);
  }
  img.onload = () => { fit(); ready = true; warmStart(); loop(); };
  img.src = HERO_IMG;
  addEventListener('resize', fit);
}
