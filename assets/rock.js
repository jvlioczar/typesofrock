(function () {
  'use strict';
  var R = window.ROCK, T = R.t, $ = function (s, r) { return (r || document).querySelector(s); }, $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };
  var byId = {}; R.genres.forEach(function (g) { byId[g.id] = g; });
  function url(id) { return R.base + R.dir + '/' + id + '.html'; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function chip(id) { return '<a href="' + url(id) + '">' + esc(byId[id].name) + '</a>'; }
  function chips(ids) { return ids.length ? '<div class="chips">' + ids.map(chip).join('') + '</div>' : '<p class="none">' + T.none + '</p>'; }

  /* ---------- Sintetizador: um esboço de dois compassos para cada gênero ---------- */
  var KITS = {
    rock:    ['x...x...x...x...', '....x.......x...', 'x.x.x.x.x.x.x.x.'],
    shuffle: ['x.....x.x.....x.', '....x.......x...', 'x.xxx.xxx.xxx.xx'],
    punk:    ['x.x.x.x.x.x.x.x.', '....x.......x...', 'xxxxxxxxxxxxxxxx'],
    gallop:  ['x.xxx.xxx.xxx.xx', '....x.......x...', 'x...x...x...x...'],
    blast:   ['x.x.x.x.x.x.x.x.', '.x.x.x.x.x.x.x.x', 'x.x.x.x.x.x.x.x.'],
    doom:    ['x.......x.......', '........x.......', 'x...x...x...x...'],
    motorik: ['x...x.x.x...x.x.', '....x.......x...', 'x.x.x.x.x.x.x.x.'],
    funk:    ['x..x..x...x..x..', '....x..x.x..x...', 'xxxxxxxxxxxxxxxx'],
    twist:   ['x.....x.x.....x.', '....x.......x...', 'x.x.x.x.x.x.x.x.'],
    soft:    ['x.......x.......', '....x.......x...', '..x...x...x...x.'],
    hiphop:  ['x.....x...x.....', '....x.......x...', 'x.x.x.x.x.x.x.x.'],
    'break': ['x..x..x...x..x..', '....x.......x...', 'x...x...x...x...']
  };
  // [passo, semitons acima da tônica, duração em passos, acorde?]
  var RIFFS = {
    blues: [[0,0,3,0],[3,3,1,0],[4,5,2,0],[6,6,1,0],[7,7,3,0],[10,10,2,0],[12,7,2,0],[14,5,2,0]],
    power: [[0,0,4,1],[4,0,2,1],[6,3,2,1],[8,5,4,1],[12,3,2,1],[14,5,2,1]],
    major: [[0,0,4,1],[4,7,4,1],[8,9,4,1],[12,5,4,1]],
    minor: [[0,0,2,1],[2,0,1,0],[3,3,2,0],[5,0,1,0],[6,5,2,1],[8,3,2,1],[10,0,2,0],[12,-2,4,1]],
    drone: [[0,0,8,1],[8,0,4,1],[12,1,4,1]],
    arp:   [[0,0,2,0],[2,7,2,0],[4,12,2,0],[6,15,2,0],[8,10,2,0],[10,5,1,0],[11,7,2,0],[13,3,3,0]],
    chug:  [[0,0,1,0],[1,0,1,0],[2,0,1,0],[3,1,1,0],[4,0,1,0],[5,0,1,0],[6,3,2,1],[8,0,1,0],[9,0,1,0],[10,0,1,0],[11,6,1,0],[12,0,1,0],[13,0,1,0],[14,5,2,1]],
    djent: [[0,0,2,0],[3,0,1,0],[5,0,2,0],[8,0,1,0],[10,1,2,0],[13,0,1,0],[15,0,1,0]],
    clean: [[0,0,1,0],[2,4,1,0],[4,7,1,0],[6,12,1,0],[8,5,1,0],[10,9,1,0],[12,7,1,0],[14,4,1,0]],
    ska:   [[2,0,1,1],[6,0,1,1],[10,5,1,1],[14,7,1,1]]
  };
  function noiseBuf(ctx, secs) {
    var b = ctx.createBuffer(1, Math.floor(ctx.sampleRate * secs), ctx.sampleRate), d = b.getChannelData(0);
    for (var i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    return b;
  }
  function env(g, t, peak, dur) {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + 0.003);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  }
  // Corda dedilhada (Karplus-Strong): um ruído curto circula num atraso filtrado e decai como uma corda real.
  var plucks = {};
  function pluck(ctx, f, muted) {
    var sr = ctx.sampleRate, key = sr + '|' + f.toFixed(1) + '|' + (muted ? 1 : 0);
    if (plucks[key]) return plucks[key];
    if (Object.keys(plucks).length > 90) plucks = {};
    var N = Math.max(2, Math.round(sr / f)), len = Math.floor(sr * (muted ? 0.32 : 1.5)), b = ctx.createBuffer(1, len, sr), d = b.getChannelData(0);
    var pick = Math.max(1, Math.floor(N * 0.17)), last = 0, i;
    for (i = 0; i < N && i < len; i++) { last = last * (muted ? 0.75 : 0.35) + (Math.random() * 2 - 1); d[i] = last * 0.5; }
    for (i = N - 1; i >= pick; i--) d[i] -= d[i - pick]; // posição da palheta na corda
    var loss = muted ? 0.972 : 0.9978;
    for (i = N + 1; i < len; i++) d[i] = loss * 0.5 * (d[i - N] + d[i - N - 1]);
    return (plucks[key] = { buffer: b, rate: f * (N + 0.5) / sr });
  }
  function curve(drive) {
    var c = new Float32Array(2048), k = drive * drive * 1.1 + 0.5, n = Math.tanh(k);
    for (var i = 0; i < 2048; i++) { var x = i / 1024 - 1; c[i] = Math.tanh(k * (x + 0.04 * x * x)) / n; }
    return c;
  }
  function biquad(ctx, type, f, q, gain) {
    var n = ctx.createBiquadFilter(); n.type = type; n.frequency.value = f;
    if (q) n.Q.value = q;
    if (gain) n.gain.value = gain;
    return n;
  }
  function chainAll(list) { for (var i = 0; i + 1 < list.length; i++) list[i].connect(list[i + 1]); return list[list.length - 1]; }
  // Um amplificador com caixa: corta graves antes da distorção, satura e depois molda como um falante de guitarra.
  function ampChannel(ctx, drive, heavy, pan, room, dry) {
    var input = ctx.createGain(), pre = ctx.createGain(), shaper = ctx.createWaveShaper(), out = ctx.createGain(), panner = ctx.createStereoPanner();
    pre.gain.value = 0.7 + drive * 0.25;
    shaper.curve = curve(drive); shaper.oversample = '4x';
    out.gain.value = (0.34 + (10 - drive) * 0.035) * (drive <= 2 ? 1.7 : 1);
    panner.pan.value = pan;
    chainAll([input, biquad(ctx, 'highpass', drive > 5 ? 130 : 70, 0.7), pre, shaper,
      biquad(ctx, 'highpass', 75, 0.7), biquad(ctx, 'peaking', 110, 1, 2 + heavy * 0.35),
      biquad(ctx, 'peaking', 480, 1, -1 - drive * 0.45), biquad(ctx, 'peaking', 2500, 0.9, 1 + drive * 0.35),
      biquad(ctx, 'lowpass', 3400 + drive * 200, 0.6), biquad(ctx, 'lowpass', 6500, 0.7), out, panner]);
    panner.connect(dry); panner.connect(room);
    return input;
  }
  function makeChain(ctx, dest, genome) {
    var drive = genome[0], heavy = genome[2];
    var master = ctx.createGain(), comp = ctx.createDynamicsCompressor(), dry = ctx.createGain(), room = ctx.createGain(), conv = ctx.createConvolver();
    master.gain.value = 0.5;
    var limit = ctx.createDynamicsCompressor();
    limit.threshold.value = -3; limit.knee.value = 2; limit.ratio.value = 20; limit.attack.value = 0.002; limit.release.value = 0.08;
    comp.threshold.value = -16; comp.ratio.value = 4; comp.attack.value = 0.006; comp.release.value = 0.16;
    // Sala curta: ruído que decai, usado como resposta de impulso.
    var irLen = Math.floor(ctx.sampleRate * 0.55), ir = ctx.createBuffer(2, irLen, ctx.sampleRate);
    for (var c = 0; c < 2; c++) { var d = ir.getChannelData(c); for (var i = 0; i < irLen; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / irLen, 3.2); }
    conv.buffer = ir;
    room.gain.value = 0.1 + genome[7] * 0.016;
    chainAll([dry, comp, master, limit, dest]);
    chainAll([room, conv, biquad(ctx, 'lowpass', 5000, 0.5), comp]);
    var drums = ctx.createGain(), roomSend = ctx.createGain();
    roomSend.gain.value = 0.5;
    drums.connect(dry); drums.connect(roomSend); roomSend.connect(room);
    var bass = ctx.createGain(); bass.gain.value = 0.85; bass.connect(dry);
    return { master: master, drums: drums, bass: bass, noise: noiseBuf(ctx, 1.2), drive: drive, heavy: heavy,
      left: ampChannel(ctx, drive, heavy, -0.62, room, dry), right: ampChannel(ctx, drive, heavy, 0.62, room, dry) };
  }
  function kick(ctx, ch, t, v) {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(50, t + 0.07);
    env(g, t, v, 0.2); o.connect(g); g.connect(ch.drums); o.start(t); o.stop(t + 0.23);
    noise(ctx, ch, t, 'highpass', 3000, v * 0.16, 0.012); // estalo do batedor
  }
  function noise(ctx, ch, t, type, f, peak, dur, q) {
    var s = ctx.createBufferSource(), fl = biquad(ctx, type, f, q), g = ctx.createGain();
    s.buffer = ch.noise; env(g, t, peak, dur);
    s.connect(fl); fl.connect(g); g.connect(ch.drums);
    s.start(t, Math.random() * 0.4, dur + 0.02);
  }
  function snare(ctx, ch, t, v) {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = 'triangle'; o.frequency.setValueAtTime(230, t); o.frequency.exponentialRampToValueAtTime(165, t + 0.06);
    env(g, t, v * 0.5, 0.11); o.connect(g); g.connect(ch.drums); o.start(t); o.stop(t + 0.13);
    noise(ctx, ch, t, 'bandpass', 3200, v * 0.8, 0.17, 0.5);
  }
  function guitarNote(ctx, ch, t, freq, d, muted, strum) {
    [ch.left, ch.right].forEach(function (input, side) {
      var p = pluck(ctx, freq, muted), s = ctx.createBufferSource(), g = ctx.createGain(), at = t + strum + side * 0.007;
      s.buffer = p.buffer; s.playbackRate.value = p.rate * (side ? 1.0025 : 0.9985);
      g.gain.setValueAtTime(1, at); g.gain.setValueAtTime(1, at + d); g.gain.linearRampToValueAtTime(0.0001, at + d + 0.03);
      s.connect(g); g.connect(input); s.start(at); s.stop(at + d + 0.05);
    });
  }
  function scheduleBars(ctx, ch, t0, sound, genome, bars) {
    var bpm = sound[0], step = 60 / bpm / 4, kit = KITS[sound[1]] || KITS.rock, riff = RIFFS[sound[2]] || RIFFS.power;
    var heavy = genome[2], drive = genome[0], palm = sound[2] === 'chug' || sound[2] === 'djent';
    var swing = sound[1] === 'shuffle' ? step * 0.33 : 0;
    var root = 82.41 * Math.pow(2, -Math.round(heavy / 3) / 12);
    function at(n) { return t0 + n * step + (n % 2 ? swing : 0); }
    for (var b = 0; b < bars; b++) {
      if (drive >= 4 && sound[1] !== 'soft') noise(ctx, ch, at(b * 16), 'highpass', 5500, 0.16, 0.8);
      for (var i = 0; i < 16; i++) {
        var n = b * 16 + i, t = at(n), hum = 0.92 + Math.random() * 0.12;
        if (kit[0][i] === 'x') kick(ctx, ch, t, 0.95 * hum);
        if (kit[1][i] === 'x') snare(ctx, ch, t, 0.72 * hum);
        if (kit[2][i] === 'x') noise(ctx, ch, t, 'highpass', 8000, (i % 4 === 0 ? 0.13 : 0.08) * hum, 0.04);
      }
      riff.forEach(function (ev) {
        var t = at(b * 16 + ev[0]), d = Math.max(step * ev[2] * 0.94, 0.05), chord = ev[3];
        var muted = palm && !chord;
        (chord ? [0, 7, 12] : [0]).forEach(function (iv, v) {
          guitarNote(ctx, ch, t, root * Math.pow(2, (ev[1] + iv) / 12) * (chord ? 1 : 2), d, muted, v * 0.004);
        });
        var o = ctx.createOscillator(), lp = biquad(ctx, 'lowpass', 750, 0.8), g = ctx.createGain();
        o.type = 'sawtooth'; o.frequency.value = root / 2 * Math.pow(2, ev[1] / 12);
        g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.42, t + 0.006);
        g.gain.setValueAtTime(0.42, t + Math.max(d - 0.02, 0.01)); g.gain.linearRampToValueAtTime(0.0001, t + d + 0.02);
        o.connect(lp); lp.connect(g); g.connect(ch.bass); o.start(t); o.stop(t + d + 0.03);
      });
    }
    return bars * 16 * step;
  }
  var player = { ctx: null, timer: null, btn: null, master: null };
  function stop() {
    clearTimeout(player.timer);
    if (player.master) { var m = player.master; m.gain.setTargetAtTime(0, player.ctx.currentTime, 0.02); setTimeout(function () { m.disconnect(); }, 200); player.master = null; }
    if (player.btn) { player.btn.setAttribute('aria-pressed', 'false'); player.btn.textContent = player.btn.dataset.label; player.btn = null; }
  }
  function play(sound, genome, btn) {
    var same = btn && player.btn === btn; stop(); if (same) return;
    var C = window.AudioContext || window.webkitAudioContext; if (!C) return;
    player.ctx = player.ctx || new C(); player.ctx.resume();
    var ctx = player.ctx, ch = makeChain(ctx, ctx.destination, genome), master = ch.master;
    player.master = master;
    if (btn) { btn.dataset.label = btn.dataset.label || btn.textContent; btn.setAttribute('aria-pressed', 'true'); btn.textContent = '■ ' + T.stop; player.btn = btn; }
    var t = ctx.currentTime + 0.05, loops = 0;
    (function loop() {
      if (player.master !== master) return;
      var d = scheduleBars(ctx, ch, t, sound, genome, 2); t += d;
      if (++loops >= 6) { player.timer = setTimeout(stop, (t - ctx.currentTime) * 1000); return; }
      player.timer = setTimeout(loop, Math.max(0, (t - ctx.currentTime - 0.3) * 1000));
    })();
  }
  R.renderTest = function (id) { // usado para conferir nível, picos e silêncio de cada esboço
    var g = byId[id], c = new window.OfflineAudioContext(2, 44100 * 5, 44100), ch = makeChain(c, c.destination, g.genome), t0 = performance.now();
    scheduleBars(c, ch, 0, g.sound, g.genome, 2);
    return c.startRendering().then(function (b) {
      var l = b.getChannelData(0), r = b.getChannelData(1), sum = 0, peak = 0, side = 0, end = Math.min(l.length, Math.floor(44100 * 2 * 16 * 60 / g.sound[0] / 4));
      for (var i = 0; i < end; i++) { sum += l[i] * l[i]; side += (l[i] - r[i]) * (l[i] - r[i]); peak = Math.max(peak, Math.abs(l[i]), Math.abs(r[i])); }
      return { rms: Math.sqrt(sum / end), peak: peak, width: Math.sqrt(side / end), ms: Math.round(performance.now() - t0) };
    });
  };
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-play]'); if (!b) return;
    var g = byId[b.dataset.play]; if (g) play(g.sound, g.genome, b);
  });

  /* ---------- Radar ---------- */
  function radarPts(v, r, cx) { return v.map(function (x, i) { var a = -Math.PI / 2 + i * Math.PI / 4, q = r * x / 10; return (cx + q * Math.cos(a)).toFixed(1) + ',' + (cx + q * Math.sin(a)).toFixed(1); }).join(' '); }
  function radarSvg(series) {
    var cx = 160, r = 104, s = '<svg viewBox="-50 0 420 320" id="radarAB" role="img" aria-label="' + esc(T.genome) + '">';
    [2.5, 5, 7.5, 10].forEach(function (l) { s += '<polygon points="' + radarPts([l,l,l,l,l,l,l,l], r, cx) + '" fill="none" stroke="#17161a" opacity=".16"/>'; });
    T.traits.forEach(function (name, i) {
      var a = -Math.PI / 2 + i * Math.PI / 4, x = cx + (r + 10) * Math.cos(a), y = cx + (r + 10) * Math.sin(a), c = Math.cos(a);
      s += '<text x="' + x.toFixed(1) + '" y="' + (y + 4).toFixed(1) + '" font-size="10.5" fill="#47454b" text-anchor="' + (c > .3 ? 'start' : c < -.3 ? 'end' : 'middle') + '">' + esc(name) + '</text>';
    });
    series.forEach(function (x) { s += '<polygon points="' + radarPts(x.v, r, cx) + '" fill="' + x.c + '" fill-opacity=".22" stroke="' + x.c + '" stroke-width="2"/>'; });
    return s + '</svg>';
  }

  /* ---------- Árvore radial ---------- */
  function initTree() {
    var svg = $('#tree'); if (!svg) return;
    var NS = 'http://www.w3.org/2000/svg', VB = 600;
    function rad(y) {
      if (y <= 1950) return 80 + (Math.max(y, 1900) - 1900) * 1.5;
      return 154 + Math.pow(Math.min(y, 2026) - 1950, 0.88) * 8.3;
    }
    var order = R.clades.map(function (c) { return c.id; });
    var list = R.genres.slice().sort(function (a, b) { return order.indexOf(a.clade) - order.indexOf(b.clade) || a.year - b.year; });
    var roots = list.filter(function (g) { return g.clade === 'raizes'; }), rest = list.filter(function (g) { return g.clade !== 'raizes'; });
    var gap = 0.05, unit = (Math.PI * 2 - gap * (order.length - 1)) / rest.length, ang = -Math.PI / 2, last = null;
    function place(g) { g.r = rad(g.year); g.x = g.r * Math.cos(g.a); g.y = g.r * Math.sin(g.a); }
    rest.forEach(function (g) {
      if (last && last !== g.clade) ang += gap;
      last = g.clade; ang += unit; g.a = ang; place(g);
    });
    roots.forEach(function (g, i) { g.a = -Math.PI / 2 + 0.5 + i * Math.PI * 2 / roots.length; place(g); });
    function el(n, at, p) { var e = document.createElementNS(NS, n); for (var k in at) e.setAttribute(k, at[k]); if (p) p.appendChild(e); return e; }
    var world = el('g', {}, svg), rings = el('g', {}, world), edges = el('g', {}, world), nodes = el('g', {}, world);
    [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020].forEach(function (y) {
      el('circle', { 'class': 'ring', r: rad(y) }, rings);
      el('text', { 'class': 'ring-t', x: 0, y: -rad(y) + 4 }, rings).textContent = y;
    });
    var now = el('circle', { 'class': 'ring-now', r: rad(2026) }, rings);
    var yearT = el('text', { 'class': 'center-y', x: 0, y: 0 }, world);
    var edgeEls = [], nodeEls = {};
    function color(g) { return R.cladeColor[g.clade]; }
    R.genres.forEach(function (g) {
      g.parents.forEach(function (pid, i) {
        var p = byId[pid], mid = (p.r + g.r) / 2;
        var d = 'M' + p.x.toFixed(1) + ' ' + p.y.toFixed(1) + 'C' + (mid * Math.cos(p.a)).toFixed(1) + ' ' + (mid * Math.sin(p.a)).toFixed(1) + ' ' + (mid * Math.cos(g.a)).toFixed(1) + ' ' + (mid * Math.sin(g.a)).toFixed(1) + ' ' + g.x.toFixed(1) + ' ' + g.y.toFixed(1);
        var e = el('path', { 'class': 'edge' + (i ? ' second' : ''), d: d, stroke: color(g) }, edges);
        edgeEls.push({ el: e, from: pid, to: g.id });
      });
      var hub = g.children.length >= 3 || g.clade === 'raizes';
      var node = el('g', { 'class': 'node' + (hub ? ' hub' : '') + (g.children.length >= 4 || g.clade === 'raizes' ? ' major' : ''), tabindex: 0, role: 'button', 'aria-label': g.name + ', ' + g.year, transform: 'translate(' + g.x.toFixed(1) + ' ' + g.y.toFixed(1) + ')' }, nodes);
      el('circle', { 'class': 'hit', r: 12 }, node);
      el('circle', { 'class': 'dot', r: Math.min(5 + g.children.length * 0.8, 11), fill: color(g) }, node);
      var deg = g.a * 180 / Math.PI, flip = Math.cos(g.a) < 0, off = Math.min(5 + g.children.length * 0.8, 11) + 5;
      var t = el('text', { dy: '.34em', x: flip ? -off : off, 'text-anchor': flip ? 'end' : 'start', transform: 'rotate(' + (flip ? deg + 180 : deg).toFixed(1) + ')' }, node);
      t.textContent = g.short;
      nodeEls[g.id] = node;
      node.addEventListener('pointerenter', function () { if (!selected) light(g.id); });
      node.addEventListener('pointerleave', function () { if (!selected) light(null); });
      node.addEventListener('focus', function () { if (!selected) light(g.id); });
      node.addEventListener('blur', function () { if (!selected) light(null); });
      node.addEventListener('click', function () { if (!moved) select(g.id); });
      node.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(g.id); } });
    });
    function lineage(id) {
      var up = {}, down = {};
      (function u(i) { byId[i].parents.forEach(function (p) { if (!up[p]) { up[p] = 1; u(p); } }); })(id);
      (function d(i) { byId[i].children.forEach(function (c) { if (!down[c]) { down[c] = 1; d(c); } }); })(id);
      return { up: up, down: down };
    }
    function light(id) {
      svg.classList.toggle('focus', !!id);
      $$('.lit', svg).forEach(function (e) { e.classList.remove('lit'); });
      $$('.me', svg).forEach(function (e) { e.classList.remove('me'); });
      if (!id) return;
      var L = lineage(id);
      nodeEls[id].classList.add('lit', 'me');
      [L.up, L.down].forEach(function (s) { Object.keys(s).forEach(function (k) { nodeEls[k].classList.add('lit'); }); });
      edgeEls.forEach(function (e) {
        var upE = (L.up[e.from] && (L.up[e.to] || e.to === id)), downE = (L.down[e.to] && (L.down[e.from] || e.from === id));
        if (upE || downE) e.el.classList.add('lit');
      });
    }
    function lightClade(c) {
      svg.classList.toggle('focus', !!c);
      $$('.lit', svg).forEach(function (e) { e.classList.remove('lit'); });
      if (!c) return;
      R.genres.forEach(function (g) { if (g.clade === c) nodeEls[g.id].classList.add('lit'); });
      edgeEls.forEach(function (e) { if (byId[e.to].clade === c) e.el.classList.add('lit'); });
    }
    /* Relógio */
    var range = $('#year'), playBtn = $('#playClock'), timer = null;
    function setYear(y) {
      range.value = y; yearT.textContent = y; now.setAttribute('r', rad(y));
      R.genres.forEach(function (g) { nodeEls[g.id].classList.toggle('off', g.year > y); });
      edgeEls.forEach(function (e) { e.el.classList.toggle('off', byId[e.to].year > y); });
      var c = R.genres.filter(function (g) { return g.year <= y; }).length;
      $('#yearCount').textContent = c + ' ' + (c === 1 ? T.species1 : T.species);
    }
    function stopClock() { if (timer) { cancelAnimationFrame(timer); timer = null; } playBtn.textContent = '▶ ' + T.evolve; }
    function startClock() {
      stopClock();
      var from = +range.value >= 2026 ? 1900 : +range.value, start = performance.now(), span = (2026 - from) * 62;
      playBtn.textContent = '■ ' + T.pause;
      (function tick(t) {
        var p = Math.min((t - start) / span, 1), y = Math.round(from + (2026 - from) * p);
        setYear(y);
        timer = p < 1 ? requestAnimationFrame(tick) : null;
        if (p >= 1) stopClock();
      })(start);
    }
    range.addEventListener('input', function () { stopClock(); setYear(+range.value); });
    playBtn.addEventListener('click', function () { timer ? stopClock() : startClock(); });
    /* Painel */
    var panel = $('#panel'), selected = null;
    function select(id) {
      selected = id; light(id); stopClock();
      var g = byId[id];
      if (+range.value < g.year) setYear(2026);
      panel.innerHTML = '<button class="x" aria-label="' + T.close + '">×</button><div class="mono">' + g.year + ' · ' + esc(g.place) + '</div><h2>' + esc(g.name) + '</h2><div class="kind-tag">' + esc(g.kindLine) + '</div>' +
        '<p>' + esc(g.blurb) + '</p><h3>' + T.parents + '</h3>' + chips(g.parents) + '<h3>' + T.children + '</h3>' + chips(g.children) +
        '<h3>' + T.greats + '</h3><p>' + g.artists.slice(0, 6).map(esc).join(', ') + '</p>' +
        '<div class="panel-acts"><a class="btn" href="' + url(id) + '">' + T.open + ' →</a><button class="btn ghost" data-play="' + id + '">▶ ' + T.listen + '</button></div>';
      panel.classList.add('open'); apply();
      $('.x', panel).addEventListener('click', closePanel);
      if (location.hash !== '#' + id) history.replaceState(null, '', '#' + id);
    }
    function closePanel() {
      selected = null; light(null); panel.classList.remove('open'); apply(); stop();
      history.replaceState(null, '', location.pathname);
    }
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && selected) closePanel(); });
    /* Zoom e arraste */
    var view = { x: 0, y: 0, k: 1 }, pts = {}, moved = false, last0 = null, dist0 = 0;
    function fit() {
      var b = svg.getBoundingClientRect(), small = b.width < 720;
      var w = b.width, h = b.height, s = Math.min(w, h) / (VB * (small ? 2.5 : 2));
            return { w: w, h: h, s: s };
    }
    function centerShift(w) { return w < 1000 ? 0 : panel.classList.contains('open') ? -170 : 70; }
    function apply() {
      var f = fit(), s = f.s * view.k;
      svg.setAttribute('viewBox', '0 0 ' + f.w + ' ' + f.h);
      svg.style.setProperty('--lab', (Math.max(11, Math.min(14, 11 + (s - .5) * 6)) / s).toFixed(2) + 'px');
      svg.classList.toggle('sparse', s < .42);
      svg.style.setProperty('--sw', (1 / s).toFixed(3));
      var cx = f.w / 2 + centerShift(f.w) + view.x, cy = f.h / 2 + view.y;
      world.setAttribute('transform', 'translate(' + cx.toFixed(1) + ' ' + cy.toFixed(1) + ') scale(' + s.toFixed(4) + ')');
    }
    function zoomBy(z, px, py) {
      var f = fit(), k2 = Math.max(0.7, Math.min(7, view.k * z)), r = k2 / view.k;
      var cx = f.w / 2 + centerShift(f.w);
      px = px === undefined ? cx : px; py = py === undefined ? f.h / 2 : py;
      view.x = (view.x + cx - px) * r + px - cx; view.y = (view.y + f.h / 2 - py) * r + py - f.h / 2;
      view.k = k2; apply();
    }
    svg.addEventListener('wheel', function (e) { e.preventDefault(); var b = svg.getBoundingClientRect(); zoomBy(e.deltaY < 0 ? 1.15 : 0.87, e.clientX - b.left, e.clientY - b.top); }, { passive: false });
    svg.addEventListener('pointerdown', function (e) { pts[e.pointerId] = [e.clientX, e.clientY]; moved = false; dist0 = 0; });
    window.addEventListener('pointermove', function (e) {
      if (!pts[e.pointerId]) return;
      var ids = Object.keys(pts), p = pts[e.pointerId], dx = e.clientX - p[0], dy = e.clientY - p[1];
      if (Math.abs(dx) + Math.abs(dy) > 3) { moved = true; svg.classList.add('drag'); }
      pts[e.pointerId] = [e.clientX, e.clientY];
      if (ids.length === 1) { if (moved) { view.x += dx; view.y += dy; apply(); } }
      else if (ids.length === 2) {
        var a = pts[ids[0]], c = pts[ids[1]], d = Math.hypot(a[0] - c[0], a[1] - c[1]), b = svg.getBoundingClientRect();
        if (dist0) zoomBy(d / dist0, (a[0] + c[0]) / 2 - b.left, (a[1] + c[1]) / 2 - b.top);
        dist0 = d;
      }
    });
    function up(e) { delete pts[e.pointerId]; dist0 = 0; svg.classList.remove('drag'); }
    window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up);
    svg.addEventListener('click', function (e) { if (!moved && !e.target.closest('.node') && selected) closePanel(); });
    window.addEventListener('resize', apply);
    $('#zin').addEventListener('click', function () { zoomBy(1.35); });
    $('#zout').addEventListener('click', function () { zoomBy(0.74); });
    $('#zfit').addEventListener('click', function () { view = { x: 0, y: 0, k: 1 }; apply(); });
    /* Legenda e busca */
    var pressed = null;
    $$('.legend button').forEach(function (b) {
      var c = b.dataset.clade;
      b.addEventListener('pointerenter', function () { if (!selected && !pressed) lightClade(c); });
      b.addEventListener('pointerleave', function () { if (!selected && !pressed) lightClade(null); });
      b.addEventListener('click', function () {
        pressed = pressed === c ? null : c;
        $$('.legend button').forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.clade === pressed); });
        if (selected) closePanel();
        lightClade(pressed);
      });
    });
    var q = $('#find');
    q.addEventListener('change', function () {
      var v = q.value.trim().toLowerCase(), g = R.genres.filter(function (x) { return x.name.toLowerCase() === v; })[0] || R.genres.filter(function (x) { return x.name.toLowerCase().indexOf(v) >= 0; })[0];
      if (v && g) { setYear(2026); select(g.id); q.value = ''; q.blur(); }
    });
    apply();
    var h = location.hash.slice(1), reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (byId[h]) { setYear(2026); select(h); }
    else if (reduce) setYear(2026);
    else { setYear(1900); startClock(); }
  }

  /* ---------- Índice de gêneros ---------- */
  function initIndex() {
    var box = $('#cards'); if (!box) return;
    var q = $('#q'), sort = $('#sort'), kindSel = $('#kind'), clade = 'all', cards = $$('.card', box);
    function run() {
      var v = q.value.trim().toLowerCase();
      cards.forEach(function (c) { c.hidden = !((clade === 'all' || c.dataset.clade === clade) && (kindSel.value === 'all' || c.dataset.kind === kindSel.value) && c.dataset.search.indexOf(v) >= 0); });
      var key = sort.value;
      cards.slice().sort(function (a, b) {
        if (key === 'name') return a.dataset.name.localeCompare(b.dataset.name);
        if (key === 'kids') return b.dataset.kids - a.dataset.kids || a.dataset.year - b.dataset.year;
        return a.dataset.year - b.dataset.year;
      }).forEach(function (c) { box.appendChild(c); });
      $('#qcount').textContent = cards.filter(function (c) { return !c.hidden; }).length;
    }
    q.addEventListener('input', run); sort.addEventListener('change', run); kindSel.addEventListener('change', run);
    $$('#cladeTabs button').forEach(function (b) {
      b.addEventListener('click', function () {
        clade = b.dataset.clade;
        $$('#cladeTabs button').forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
        run();
      });
    });
    run();
  }

  /* ---------- Canções ---------- */
  function initSongs() {
    var root = $('#decades'); if (!root) return;
    var q = $('#songq'), dec = 'all', items = $$('.songs li', root), secs = $$('.decade', root);
    function run() {
      var v = q.value.trim().toLowerCase(), n = 0;
      secs.forEach(function (s) {
        var show = dec === 'all' || s.dataset.dec === dec, any = 0;
        $$('.songs li', s).forEach(function (li) { var ok = show && li.dataset.s.indexOf(v) >= 0; li.hidden = !ok; if (ok) any++; });
        s.hidden = !any; n += any;
      });
      $('#songcount').textContent = n;
    }
    q.addEventListener('input', run);
    $$('#decTabs button').forEach(function (b) {
      b.addEventListener('click', function () {
        dec = b.dataset.dec;
        $$('#decTabs button').forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
        run();
      });
    });
    $('#jukebox').addEventListener('click', function () {
      var vis = items.filter(function (li) { return !li.hidden; }); if (!vis.length) return;
      $$('.pick', root).forEach(function (e) { e.classList.remove('pick'); });
      var li = vis[Math.floor(Math.random() * vis.length)];
      li.classList.add('pick'); li.scrollIntoView({ block: 'center' }); $('a', li).focus({ preventScroll: true });
    });
    run();
  }

  /* ---------- Bandas ---------- */
  function initBands() {
    var body = $('#bandsBody'); if (!body) return;
    var rows = $$('tr', body), tier = 'all', q = $('#bandq');
    function run() {
      var v = q.value.trim().toLowerCase(), n = 0;
      rows.forEach(function (r) { var ok = (tier === 'all' || r.dataset.tier === tier) && r.dataset.name.indexOf(v) >= 0; r.hidden = !ok; if (ok) n++; });
      $('#bandcount').textContent = n;
    }
    q.addEventListener('input', run);
    $$('#tierTabs button').forEach(function (b) {
      b.addEventListener('click', function () {
        tier = b.dataset.tier;
        $$('#tierTabs button').forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
        run();
      });
    });
    $$('.bands th button').forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.k, th = b.parentNode;
        $$('.bands th').forEach(function (x) { x.removeAttribute('aria-sort'); }); th.setAttribute('aria-sort', 'ascending');
        rows.slice().sort(function (x, y) {
          if (k === 'name') return x.dataset.name.localeCompare(y.dataset.name);
          return (+x.dataset[k] || 9999) - (+y.dataset[k] || 9999);
        }).forEach(function (r) { body.appendChild(r); });
      });
    });
  }

  /* ---------- Laboratório ---------- */
  function initLab() {
    var A = $('#gA'); if (!A) return;
    var B = $('#gB');
    function path(a, b) {
      var prev = {}, q = [a]; prev[a] = a;
      while (q.length) {
        var c = q.shift(); if (c === b) break;
        byId[c].parents.concat(byId[c].children).forEach(function (n) { if (!(n in prev)) { prev[n] = c; q.push(n); } });
      }
      var r = [b]; while (r[0] !== a) r.unshift(prev[r[0]]);
      return r;
    }
    function ancestors(id) { var s = {}; (function u(i) { byId[i].parents.forEach(function (p) { if (!s[p]) { s[p] = 1; u(p); } }); })(id); return s; }
    function sim(x, y) { var d = 0; for (var i = 0; i < 8; i++) d += Math.pow(x[i] - y[i], 2); return Math.round(100 * (1 - Math.sqrt(d) / Math.sqrt(800))); }
    function compare() {
      var a = byId[A.value], b = byId[B.value], p = path(a.id, b.id);
      var ua = ancestors(a.id), ub = ancestors(b.id); ua[a.id] = 1; ub[b.id] = 1;
      var common = Object.keys(ua).filter(function (k) { return ub[k]; }).sort(function (x, y) { return byId[y].year - byId[x].year; });
      var norm = function (s) { return s.toLowerCase().replace(/^the /, ''); };
      var bn = {}; b.artists.forEach(function (n) { bn[norm(n)] = 1; });
      var shared = a.id === b.id ? [] : a.artists.filter(function (n) { return bn[norm(n)]; });
      var ca = R.cladeColor[a.clade], cb = b.clade === a.clade ? '#17161a' : R.cladeColor[b.clade];
      $('#radarBox').innerHTML = radarSvg([{ v: a.genome, c: ca }, { v: b.genome, c: cb }]) + '<div class="legend-inline"><span><i class="swatch" style="background:' + ca + '"></i>' + esc(a.name) + '</span><span><i class="swatch" style="background:' + cb + '"></i>' + esc(b.name) + '</span></div>';
      $('#kin').innerHTML = '<div class="stats"><div><div class="big">' + (p.length - 1) + '</div><div class="mono">' + T.steps + '</div></div><div><div class="big">' + sim(a.genome, b.genome) + '%</div><div class="mono">' + T.simil + '</div></div></div>' +
        '<h3>' + T.route + '</h3><div class="route chips">' + p.map(chip).join('<span aria-hidden="true">→</span>') + '</div>' +
        '<h3 style="margin-top:18px">' + T.mrca + '</h3>' + (common.length ? chips(common.slice(0, 3)) : '<p class="none">' + T.noMrca + '</p>') +
        '<h3 style="margin-top:18px">' + T.shared + '</h3>' + (shared.length ? '<p>' + shared.slice(0, 16).map(esc).join(', ') + '</p>' : '<p class="none">' + T.noShared + '</p>') +
        '<div class="panel-acts"><button class="btn" data-play="' + a.id + '">▶ ' + esc(a.name) + '</button><button class="btn" data-play="' + b.id + '">▶ ' + esc(b.name) + '</button></div>';
    }
    [A, B].forEach(function (s) { s.addEventListener('change', function () { stop(); compare(); }); });
    $('#swap').addEventListener('click', function () { var t = A.value; A.value = B.value; B.value = t; compare(); });
    $('#rand').addEventListener('click', function () {
      var pick = function () { return R.genres[Math.floor(Math.random() * R.genres.length)].id; };
      A.value = pick(); do { B.value = pick(); } while (B.value === A.value);
      stop(); compare();
    });
    compare();
    /* Monte seu som */
    var sliders = $$('#sliders input');
    function match() {
      var v = sliders.map(function (s) { return +s.value; });
      sliders.forEach(function (s) { s.nextElementSibling.textContent = s.value; });
      var ranked = R.genres.map(function (g) { return { g: g, s: sim(v, g.genome) }; }).sort(function (x, y) { return y.s - x.s; });
      var top = ranked[0].g;
      $('#matchOut').innerHTML = '<div class="mono">' + T.nearest + '</div><h3 style="font-size:2.1rem;margin:4px 0 8px"><a href="' + url(top.id) + '">' + esc(top.name) + '</a></h3><p>' + ranked[0].s + '% · ' + esc(top.artists.slice(0, 4).join(', ')) + '</p>' +
        '<div class="mono" style="margin-bottom:6px">' + T.then + '</div><div class="chips">' + ranked.slice(1, 5).map(function (r) { return chip(r.g.id); }).join('') + '</div>' +
        '<div class="panel-acts"><button class="btn pri" data-play="' + top.id + '">▶ ' + T.listen + '</button></div>';
    }
    sliders.forEach(function (s) { s.addEventListener('input', function () { stop(); match(); }); });
    match();
  }

  /* ---------- Anúncio: aparece uma vez, no primeiro acesso ---------- */
  function initPromo() {
    var box = $('#promo'), KEY = 'tr-promo-v2'; if (!box) return;
    try { if (localStorage.getItem(KEY)) return; } catch (e) {}
    function place() { // fica acima do relógio da árvore e da legenda, quando estão na tela
      var gap = 12, b = gap, keep = $$('.clock, .legend').filter(function (x) { return innerWidth <= 960 || x.className === 'clock'; });
      keep.forEach(function (x) { var r = x.getBoundingClientRect(); if (r.bottom > 0 && r.top < innerHeight) b = Math.max(b, innerHeight - r.top + gap); });
      box.style.bottom = b + 'px';
    }
    function close() { box.hidden = true; removeEventListener('scroll', place); removeEventListener('resize', place); }
    $('.promo-x', box).addEventListener('click', close);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !box.hidden && !$('#panel.open')) close(); });
    addEventListener('scroll', place, { passive: true }); addEventListener('resize', place);
    setTimeout(function () {
      box.hidden = false; place();
      try { localStorage.setItem(KEY, '1'); } catch (e) {}
    }, 1200);
  }

  /* ---------- Menu no celular ---------- */
  function initMenu() {
    var btn = $('#menuBtn'), nav = $('#siteNav'); if (!btn) return;
    function set(open) { nav.classList.toggle('open', open); btn.setAttribute('aria-expanded', open); }
    btn.addEventListener('click', function (e) { e.stopPropagation(); set(!nav.classList.contains('open')); });
    document.addEventListener('click', function (e) { if (!nav.contains(e.target)) set(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { set(false); } });
  }

  initMenu(); initPromo(); initTree(); initIndex(); initSongs(); initBands(); initLab();
})();
