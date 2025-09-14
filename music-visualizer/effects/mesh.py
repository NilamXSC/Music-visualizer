# effects/mesh.py
import json

def get_html(audio_src: str, beats=None):
    """
    Mesh visualizer: geometric / polygonal neon web expanded full-screen,
    Perlin-noise warping, beat-reactive shockwaves + bloom, click ripples,
    drag rotation and trance mode for immersion.
    """
    if beats is None:
        beats = []
    beats_js = json.dumps(beats)

    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>SonicPlay — Mesh</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.5.0/p5.min.js"></script>
    <style>
      html,body {{ margin:0; padding:0; overflow:hidden; background:#050305; }}
      #sketch {{ width:100%; height:100%; }}
      #hud {{
        position:absolute; left:12px; top:8px; z-index:9999;
        color:#fff; font-family:Inter, Arial, sans-serif; font-size:13px;
        background:rgba(0,0,0,0.35); padding:6px 10px; border-radius:6px;
      }}
    </style>
  </head>
  <body>
    <div id="sketch"></div>
    <div id="hud">Mesh : Neon Polygonal Web (click to ripple, drag to rotate, space toggles trance)</div>
    <audio id="audio" controls src="{audio_src}" style="display:none"></audio>

    <script>
      const BEATS = {beats_js};
      let audio = null, audioCtx = null, analyser = null, sourceNode = null;
      let freqData = null;
      let trance = false;
      let lastBeatPulse = 0;
      let beatFlash = 0;

      // interaction state
      let rotation = 0;
      let rotationVel = 0;
      let ripples = []; // each: {{ x, y, r, life }}
      let noiseScale = 0.0025;

      function initAudio() {{
        audio = document.getElementById('audio');
        if (!audio) return;
        if (audioCtx && audioCtx.state !== 'closed') return;
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;
        freqData = new Uint8Array(analyser.frequencyBinCount);
        try {{ sourceNode = audioCtx.createMediaElementSource(audio); }} catch (e) {{ console.warn(e); }}
        if (sourceNode) {{
          sourceNode.connect(analyser);
          analyser.connect(audioCtx.destination);
        }}
      }}

      function setup() {{
        let c = createCanvas(window.innerWidth, window.innerHeight);
        c.parent(document.getElementById('sketch'));
        colorMode(HSB, 360, 100, 100, 255);
        noFill();
        strokeCap(ROUND);
        strokeJoin(ROUND);
        initAudio();
        noiseDetail(3, 0.55);
      }}

      function windowResized() {{ resizeCanvas(window.innerWidth, window.innerHeight); }}

      function avg(arr) {{
        if (!arr || arr.length === 0) return 0;
        let s = 0;
        for (let v of arr) s += v;
        return s / arr.length;
      }}

      // fallback beat detection (energy in low bins)
      function detectBeatFromFFT() {{
        if (!freqData) return false;
        let bins = Math.min(48, freqData.length);
        let s = 0;
        for (let i = 0; i < bins; i++) s += freqData[i];
        let avgE = s / bins;
        return avgE > 95;
      }}

      function draw() {{
        // translucent background for trails (longer in trance)
        const trailAlpha = trance ? 6 : 28;
        background(8, 10, 12, trailAlpha);

        if (!audioCtx) initAudio();
        if (analyser) analyser.getByteFrequencyData(freqData);

        let now = audio && audio.currentTime ? audio.currentTime : millis() / 1000.0;
        let beat = false;
        if (BEATS && BEATS.length > 0) {{
          for (let t of BEATS) {{
            if (Math.abs(t - now) < 0.07 && millis() - lastBeatPulse > 120) {{
              beat = true;
              lastBeatPulse = millis();
              beatFlash = 120;
            }}
          }}
        }} else {{
          if (detectBeatFromFFT() && millis() - lastBeatPulse > 150) {{
            beat = true;
            lastBeatPulse = millis();
            beatFlash = 100;
          }}
        }}

        // beat flash / bloom
        if (beatFlash > 0) {{
          push();
          blendMode(ADD);
          noStroke();
          fill((frameCount * 0.9) % 360, 90, 90, 14 + (beatFlash / 8));
          rect(-width / 2, -height / 2, width, height);
          pop();
          beatFlash = max(0, beatFlash - (trance ? 1.2 : 3.6));
        }}

        // center and rotation
        push();
        translate(width / 2, height / 2);
        rotation += rotationVel;
        rotationVel *= 0.92;
        rotate(rotation);

        // bands
        let bass = freqData ? avg(Array.from(freqData).slice(0, Math.min(64, freqData.length))) / 255 : 0;
        let mids = freqData ? avg(Array.from(freqData).slice(Math.floor(freqData.length * 0.12), Math.floor(freqData.length * 0.45))) / 255 : 0;
        let treble = freqData ? avg(Array.from(freqData).slice(Math.floor(freqData.length * 0.45), Math.floor(freqData.length * 0.9))) / 255 : 0;

        // geometric / polygonal core: many-sided polygon warped by Perlin noise
        const rings = 9;
        const maxR = sqrt(sq(width) + sq(height)) * 0.62;
        for (let ring = rings - 1; ring >= 0; ring--) {{
          const ringScale = map(ring, 0, rings - 1, 0.20, 1.05);
          const sides = 6 + ring * 2; // keep polygonal look (hex -> many-sided)
          const points = sides * 6;
          const hueBase = (frameCount * 0.4 + ring * 28) % 360;

          // soft glow pass
          push();
          blendMode(ADD);
          stroke((hueBase + 60) % 360, 90, 92, 32 + bass * 90);
          strokeWeight(10 * ringScale * (0.4 + bass * 0.9));
          beginShape();
          for (let i = 0; i <= points; i++) {{
            let a = TAU * i / points;
            // base polygon radius (angular/polygonal feel)
            let baseR = ringScale * maxR * (0.3 + 0.7 * (i % sides) / sides);
            // perlin warp (gives vein-like distortion)
            let nx = cos(a) * baseR * noiseScale * 1.1 + ring * 0.03;
            let ny = sin(a) * baseR * noiseScale * 0.9 - ring * 0.02;
            let n = noise(nx + frameCount * 0.0014, ny - frameCount * 0.0011);
            let warp = map(n, 0, 1, -60, 60) * (0.4 + mids * 1.7);
            // slight angular jitter to keep polygonal look
            let angJitter = sin(a * (sides / 2) + frameCount * 0.002 * (1 + ring * 0.06)) * (2 + treble * 8);
            // beat punch
            let beatBoost = beat ? (12 + bass * 40) * (1 + ring * 0.06) : 0;
            let r = baseR + warp + angJitter + beatBoost;
            let x = r * cos(a);
            let y = r * sin(a) * 0.72; // elliptical warp to cover screen
            vertex(x, y);
          }}
          endShape(CLOSE);
          pop();

          // crisp filament pass
          push();
          stroke((hueBase + 180) % 360, 92, 96, 220);
          strokeWeight(1.6 + ring * 0.12);
          beginShape();
          for (let i = 0; i <= points; i++) {{
            let a = TAU * i / points;
            let baseR = ringScale * maxR * (0.3 + 0.7 * (i % sides) / sides);
            let nx = cos(a) * baseR * noiseScale * 1.2 - ring * 0.02;
            let ny = sin(a) * baseR * noiseScale * 0.8 + ring * 0.03;
            let n = noise(nx + frameCount * 0.0017, ny - frameCount * 0.0013);
            let warp = map(n, 0, 1, -30, 30) * (0.6 + mids * 1.2);
            let angJitter = sin(a * (sides / 2) + frameCount * 0.004 * (1 + ring * 0.05)) * (1.8 + treble * 6);
            let beatBoost = beat ? (6 + bass * 18) * (1 + ring * 0.04) : 0;
            let r = baseR + warp + angJitter + beatBoost;
            let x = r * cos(a);
            let y = r * sin(a) * 0.72;
            vertex(x, y);
          }}
          endShape(CLOSE);
          pop();
        }}

        // polygonal skeleton grid (radial spokes + warped concentric polygons)
        push();
        strokeWeight(1.2 + bass * 1.6);
        const skeletonLayers = 12;
        for (let sLayer = 0; sLayer < skeletonLayers; sLayer++) {{
          let tRatio = sLayer / (skeletonLayers - 1);
          let rBase = map(tRatio, 0, 1, maxR * 0.08, maxR * 1.02);
          let sides = 8 + Math.floor(tRatio * 24); // angular growth
          let hue = (frameCount * 0.9 + sLayer * 22) % 360;
          stroke(hue, 78, 88, 18 + tRatio * 48 + bass * 24);
          beginShape();
          const pts = sides * 6;
          for (let i = 0; i <= pts; i++) {{
            let a = TAU * i / pts;
            let nx = cos(a) * rBase * noiseScale * 1.4 + sLayer * 0.02;
            let ny = sin(a) * rBase * noiseScale * 1.0 - sLayer * 0.01;
            let n = noise(nx + frameCount * 0.0009, ny - frameCount * 0.0007);
            let warp = map(n, 0, 1, -18, 18) * (0.4 + treble * 1.1);
            let rr = rBase + warp + (beat ? (4 + bass * 16) : 0);
            let x = rr * cos(a);
            let y = rr * sin(a) * 0.72;
            vertex(x, y);
          }}
          endShape(CLOSE);
        }}
        pop();

        // dense neon chords across the canvas for mesh skeleton
        push();
        strokeWeight(0.9 + bass * 1.2);
        for (let i = 0; i < 120; i++) {{
          let a1 = random(TAU);
          let a2 = a1 + random(0.02, TAU * 0.5);
          let r1 = random(maxR * 0.15, maxR * 1.02);
          let r2 = random(maxR * 0.15, maxR * 1.02);
          let x1 = r1 * cos(a1), y1 = r1 * sin(a1) * 0.72;
          let x2 = r2 * cos(a2), y2 = r2 * sin(a2) * 0.72;
          let hue = (frameCount * 1.0 + i * 5) % 360;
          stroke(hue, 86, 94, 36 + (beat ? 80 : 0));
          line(x1, y1, x2, y2);
        }}
        pop();

        // click ripples
        for (let i = ripples.length - 1; i >= 0; i--) {{
          let rp = ripples[i];
          rp.r += (6 + bass * 36);
          rp.life -= (trance ? 0.7 : 1.8);
          push();
          blendMode(ADD);
          stroke((frameCount * 0.6 + rp.r) % 360, 92, 96, 100 * (rp.life / 100));
          strokeWeight(2 + bass * 3);
          ellipse(rp.x, rp.y, rp.r * 2, rp.r * 2);
          pop();
          if (rp.life <= 0) ripples.splice(i, 1);
        }}

        pop(); // center translate
      }}

      function mousePressed() {{
        // resume audio on first gesture
        if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
        else initAudio();
        // add ripple in canvas coordinates relative to center translation later - convert:
        ripples.push({{ x: mouseX - width / 2, y: mouseY - height / 2, r: 8, life: 100 }});
      }}

      function mouseDragged() {{
        // horizontal drag increases rotational velocity (trippy)
        rotationVel += (mouseX - pmouseX) * 0.0009;
      }}

      function keyPressed() {{
        if (key === ' ') {{
          trance = !trance;
        }}
      }}
    </script>
  </body>
</html>
"""