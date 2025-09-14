# effects/beatsaber.py
import json

def get_html(audio_src: str, beats=None):
    """
    BeatSaber-like mini-game: neon gems come at the player synced to beats.
    - audio_src: data URI or URL to audio file
    - beats: optional list of beat times (seconds)
    """
    if beats is None:
        beats = []
    beats_js = json.dumps(beats)

    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>SonicPlay — BeatBlade</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.5.0/p5.min.js"></script>
    <style>
      html,body { margin:0; padding:0; overflow:hidden; background:#050305; }
      #sketch { width:100%; height:100%; }
      #hud {
        position:absolute; left:12px; top:8px; z-index:9999;
        color:#fff; font-family:Inter, Arial, sans-serif; font-size:13px;
        background:rgba(0,0,0,0.35); padding:6px 10px; border-radius:6px;
      }
      #overlay {
        position:absolute; left:0; top:0; width:100%; height:100%;
        display:flex; align-items:center; justify-content:center; z-index:9998;
      }
      .start-card {
        text-align:center; background:rgba(0,0,0,0.45); padding:28px 36px; border-radius:12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6), 0 0 18px rgba(255, 0, 128, 0.08) inset;
        color:white;
      }
      .start-btn {
        background:linear-gradient(90deg,#ff2d95,#ff9a2d);
        border:none; color:#081018; font-weight:700; padding:12px 22px; border-radius:8px;
        font-size:18px; cursor:pointer; margin-top:12px;
        box-shadow:0 8px 30px rgba(255,40,120,0.12);
      }
      .end-btn {
        position:absolute; left:12px; bottom:12px; z-index:9999;
        background:rgba(0,0,0,0.5); color:white; border:none; padding:8px 10px; border-radius:6px;
        cursor:pointer;
      }
      #score {
        position:absolute; right:12px; top:12px; z-index:9999; color:white; font-family:Inter,Arial,sans-serif;
        background:rgba(0,0,0,0.35); padding:8px 12px; border-radius:6px;
      }
      #fullscreenBtn {
        position:absolute; left:12px; top:44px; z-index:9999;
        background:rgba(0,0,0,0.5); color:white; border:none; padding:6px 8px; border-radius:4px;
        cursor:pointer;
      }
      #playPauseBtn {
        position:absolute; left:12px; bottom:48px; z-index:9999;
        background:linear-gradient(90deg,#4facfe,#00f2fe);
        color:#081018; border:none; padding:8px 14px; border-radius:6px;
        font-weight:bold; cursor:pointer;
      }
    </style>
  </head>
  <body>
    <div id="sketch"></div>
    <div id="hud">BeatBlade : Slice the gems! Space toggles trance mode.</div>

    <div id="overlay">
      <div class="start-card" id="startCard">
        <h2 style="margin:0 0 8px 0">BeatBlade</h2>
        <div style="opacity:0.9; margin-bottom:10px">Press Start & begin</div>
        <button class="start-btn" id="startBtn">Start Game</button>
      </div>
    </div>

    <div id="score" style="display:none">Hits: 0 | Misses: 0</div>
    <button id="endBtn" class="end-btn" style="display:none">End Game</button>
    <button id="fullscreenBtn">⛶</button>
    <button id="playPauseBtn">▶ Play</button>

    <audio id="audio" src="__AUDIO_SRC__" style="display:none"></audio>

    <script>
      const BEATS = __BEATS_JS__;

      // Audio / analysis
      let audio = null, audioCtx = null, analyser = null, sourceNode = null;
      let freqData = null;

      // Game state
      let gems = [];
      let particles = [];
      let gameStarted = false;
      let hits = 0, misses = 0;
      let trance = false;
      let beatPulse = 0, lastBeatPulse = 0;
      let lastBeatIdx = 0;

      // Visual params
      let lanes = 3; // lanes [-1,0,1]
      let leadTime = 2.0; // seconds before beat to spawn gem
      let gemSpeed = 600; // approach speed
      let perspectiveDepth = 1200;

      // Sword smoothing
      let sword = { px: 0, py: 0, vx: 0, vy: 0, smoothing: 0.65 };

      function initAudio() {
        audio = document.getElementById('audio');
        if (!audio) return;
        if (audioCtx && audioCtx.state !== 'closed') return;
        try {
          audioCtx = new (window.AudioContext || window.webkitAudioContext)();
          analyser = audioCtx.createAnalyser();
          analyser.fftSize = 1024;
          freqData = new Uint8Array(analyser.frequencyBinCount);
          try {
            sourceNode = audioCtx.createMediaElementSource(audio);
            sourceNode.connect(analyser);
            analyser.connect(audioCtx.destination);
          } catch (e) {
            // createMediaElementSource may fail if used multiple times; still continue
            console.warn('media source create issue:', e);
          }
        } catch (e) {
          console.warn('WebAudio init error', e);
        }
      }

      // ===== Gem class =====
      class Gem {
        constructor(beatTime, lane) {
          this.beatTime = beatTime;
          this.lane = lane; // -1, 0, 1 (or other)
          this.z = perspectiveDepth;
          this.hit = false;
          this.missed = false;
          this.size = 36 + Math.random() * 18;
          this.colorHue = (120 + lane * 60 + Math.random() * 60) % 360;
          this.x = lane * (width * 0.22);
          this.y = -50;
        }
        update(dt) {
          const approach = (gemSpeed * (1 + this.size / 100)) * dt;
          this.z -= approach;
        }
        screenPos() {
          const f = 800;
          let s = f / (f + this.z);
          return {
            sx: width / 2 + this.x * s,
            sy: height / 2 + (this.y + (1 - s) * 200) * s,
            scale: s
          };
        }
        draw() {
          const p = this.screenPos();
          push();
          translate(p.sx, p.sy);
          scale(p.scale);
          strokeWeight(2.0);
          stroke(this.colorHue, 90, 100, 220);
          fill(this.colorHue, 90, 100, 18);
          rotate(frameCount * 0.008 + this.lane);
          beginShape();
          vertex(-this.size / 2, -this.size / 2);
          vertex(this.size / 2, -this.size / 2);
          vertex(this.size / 2, this.size / 2);
          vertex(-this.size / 2, this.size / 2);
          endShape(CLOSE);
          stroke(0, 0, 100, 120);
          strokeWeight(1.2);
          line(-this.size / 3, -this.size / 3, this.size / 3, this.size / 3);
          pop();
        }
      }

      // ===== Particle =====
      class Particle {
        constructor(x, y, hue) {
          this.x = x; this.y = y;
          this.vx = (Math.random() * 2 - 1) * 6;
          this.vy = (Math.random() * 2 - 1) * 6;
          this.life = 60 + Math.random() * 30;
          this.hue = hue;
          this.alpha = 1.0;
        }
        update() {
          this.x += this.vx;
          this.y += this.vy;
          this.vx *= 0.98; this.vy *= 0.98;
          this.life -= 1;
          this.alpha = Math.max(0, this.life / 100);
        }
        draw() {
          noStroke();
          fill(this.hue, 90, 100, this.alpha * 255);
          circle(this.x, this.y, 4 + this.alpha * 6);
        }
      }

      // spawn gem for a given beat time
      function spawnGemForBeat(beatTime) {
        const lane = Math.floor(Math.random() * lanes) - Math.floor(lanes / 2);
        gems.push(new Gem(beatTime, lane));
      }

      function spawnFromBeats(nowTime) {
        while (lastBeatIdx < BEATS.length && (BEATS[lastBeatIdx] - leadTime) <= nowTime + 0.05) {
          spawnGemForBeat(BEATS[lastBeatIdx]);
          lastBeatIdx++;
        }
      }

      // sword: follow mouse with smoothing
      function updateSword() {
        const mx = typeof mouseX !== 'undefined' ? mouseX : width / 2;
        const my = typeof mouseY !== 'undefined' ? mouseY : height / 2;
        sword.vx = mx - sword.px;
        sword.vy = my - sword.py;
        sword.px += sword.vx * (1 - sword.smoothing);
        sword.py += sword.vy * (1 - sword.smoothing);
      }

      function drawSword() {
        push();
        translate(sword.px, sword.py);
        strokeWeight(6); stroke(320, 90, 100, 220); strokeCap(ROUND);
        line(-18, 28, 18, -28);
        strokeWeight(2); stroke(0, 0, 100, 120);
        line(-18, 28, 18, -28);
        noStroke(); fill(320, 90, 100, 180);
        circle(0, 0, 10);
        pop();
      }

      function checkGemHits() {
        for (let i = gems.length - 1; i >= 0; i--) {
          const g = gems[i];
          if (g.hit || g.missed) continue;
          const p = g.screenPos();
          const dx = sword.px - p.sx;
          const dy = sword.py - p.sy;
          const distSq = dx * dx + dy * dy;
          const speed = Math.sqrt(sword.vx * sword.vx + sword.vy * sword.vy);
          if (g.z < 220 && (speed > 6 || mouseIsPressed)) {
            if (distSq < (g.size * g.size * p.scale * 2.0)) {
              g.hit = true;
              hits++;
              for (let k = 0; k < 18; k++) particles.push(new Particle(p.sx, p.sy, g.colorHue));
              beatPulse = 14;
              gems.splice(i, 1);
              continue;
            }
          }
          if (g.z <= 0) {
            if (!g.hit) {
              g.missed = true;
              misses++;
              const p2 = g.screenPos();
              for (let k = 0; k < 8; k++) particles.push(new Particle(p2.sx, p2.sy, (g.colorHue + 180) % 360));
              gems.splice(i, 1);
            }
          }
        }
      }

      // receding grid background
      function drawRecedingGrid(t) {
        push();
        translate(width / 2, height / 2 + 90);
        rotate(t * 0.00022);
        const cols = 12;
        const rows = 18;
        const spacing = 90;
        const f = 900;
        for (let i = 0; i < rows; i++) {
          const depth = i * spacing + (t * 0.25 % spacing);
          const s = f / (f + depth * 6);
          push();
          scale(s);
          noFill();
          stroke((frameCount * 0.6 + i * 6) % 360, 80, 90, 50);
          strokeWeight(2.0 * (1.0 - i / rows));
          rect(-cols * spacing / 2, -rows * spacing / 2, cols * spacing, rows * spacing);
          pop();
        }
        pop();
      }

      function drawShockwave() {
        if (beatPulse > 0) {
          push();
          translate(width / 2, height / 2);
          blendMode(ADD);
          noFill();
          for (let i = 0; i < 3; i++) {
            stroke((frameCount * 1.2 + i * 40) % 360, 90, 90, map(beatPulse, 0, 20, 0, 80));
            strokeWeight(6 - i * 2);
            ellipse(0, 0, (200 + (20 - beatPulse) * 8) + i * 120, (200 + (20 - beatPulse) * 4) + i * 80);
          }
          pop();
        }
      }

      // p5 sketch
      function setup() {
        let c = createCanvas(window.innerWidth, window.innerHeight);
        c.parent(document.getElementById('sketch'));
        colorMode(HSB, 360, 100, 100, 255);
        initAudio();
        frameRate(60);
        sword.px = width / 2; sword.py = height / 2;
        // hide system cursor for game immersion
        document.body.style.cursor = 'none';
      }

      function windowResized() {
        resizeCanvas(window.innerWidth, window.innerHeight);
      }

      function draw() {
        const now = audio && audio.currentTime ? audio.currentTime : millis() / 1000.0;
        const t = millis();

        background(10, 10, 12, trance ? 16 : 24);

        if (analyser) analyser.getByteFrequencyData(freqData);

        drawRecedingGrid(t);

        if (!gameStarted) {
          push(); noStroke(); fill(0, 0, 0, 160); rect(0, 0, width, height); pop();
        }

        if (gameStarted && audio && !audio.paused) {
          spawnFromBeats(now);
        }

        const dt = deltaTime / 1000.0;
        for (let i = gems.length - 1; i >= 0; i--) gems[i].update(dt);

        gems.sort((a, b) => b.z - a.z);
        for (let g of gems) g.draw();

        for (let i = particles.length - 1; i >= 0; i--) {
          const p = particles[i];
          p.update(); p.draw();
          if (p.life <= 0) particles.splice(i, 1);
        }

        updateSword(); drawSword();

        checkGemHits();

        if (beatPulse > 0) {
          drawShockwave();
          beatPulse = Math.max(0, beatPulse - 0.8);
        }

        if (analyser && BEATS.length > 0) {
          const bass = avg(Array.prototype.slice.call(freqData, 0, 40)) / 255;
          if (bass > 0.28 && millis() - lastBeatPulse > 200) {
            beatPulse = 10 + bass * 30;
            lastBeatPulse = millis();
          }
        }

        const scoreEl = document.getElementById('score');
        if (scoreEl) scoreEl.innerText = 'Hits: ' + hits + ' | Misses: ' + misses;

        if (gameStarted && audio && audio.ended) {
          endGame();
        }
      }

      function avg(arr) {
        if (!arr || arr.length === 0) return 0;
        let s = 0;
        for (let v of arr) s += v;
        return s / arr.length;
      }

      // UI wiring
      document.getElementById('startBtn').addEventListener('click', function() {
        initAudio();
        if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
        document.getElementById('startCard').style.display = 'none';
        document.getElementById('overlay').style.display = 'none';
        document.getElementById('score').style.display = 'block';
        document.getElementById('endBtn').style.display = 'block';
        gameStarted = true;
        if (audio) {
          audio.currentTime = Math.max(0, audio.currentTime);
          audio.play();
          document.getElementById('playPauseBtn').innerText = '⏸ Pause';
        }
      });

      document.getElementById('endBtn').addEventListener('click', function() {
        endGame();
      });

      function endGame() {
        if (!gameStarted) return;
        gameStarted = false;
        const overlay = document.getElementById('overlay');
        overlay.style.display = 'flex';
        overlay.innerHTML = '<div class="start-card"><h2>Game Over</h2><div style="margin:8px 0">Hits: <b>' + hits + '</b> &nbsp; Misses: <b>' + misses + '</b></div><button class="start-btn" id="restartBtn">Play Again</button></div>';
        document.getElementById('score').style.display = 'none';
        document.getElementById('endBtn').style.display = 'none';
        if (audio && !audio.paused) audio.pause();
        document.getElementById('restartBtn').addEventListener('click', function() { location.reload(); });
      }

      // Fullscreen toggle
      document.getElementById('fullscreenBtn').addEventListener('click', function() {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(err => console.warn(err));
        } else {
          document.exitFullscreen();
        }
      });

      // Play/Pause button
      const playBtn = document.getElementById('playPauseBtn');
      playBtn.addEventListener('click', function() {
        initAudio();
        if (!audio) return;
        if (audio.paused) {
          audio.play();
          playBtn.innerText = '⏸ Pause';
        } else {
          audio.pause();
          playBtn.innerText = '▶ Play';
        }
      });

      // audio ended -> end game if running
      document.getElementById('audio').addEventListener('ended', function() {
        if (gameStarted) endGame();
        document.getElementById('playPauseBtn').innerText = '▶ Play';
      });

      // mouse drag modifies grid (trippy)
      function mouseDragged() {
        // small interactive nudge (affects rotation indirectly by time)
      }

      // keyboard: space toggles trance mode
      function keyPressed() {
        if (key === ' ') {
          trance = !trance;
          document.getElementById('score').style.opacity = trance ? '0.8' : '1.0';
        }
      }
    </script>
  </body>
</html>
"""
    # Inject beats JSON and audio src safely (avoid f-string brace issues)
    return html.replace("__BEATS_JS__", beats_js).replace("__AUDIO_SRC__", audio_src)
