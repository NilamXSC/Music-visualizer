# effects/resonance.py
import json

def get_html(audio_src: str, beats=None):
    """
    Resonance visualizer: hypnotic neon circular waveform that breathes, rotates,
    and pulses with the music. Includes interactive hypnotic user effects.
    """
    if beats is None:
        beats = []
    beats_js = json.dumps(beats)

    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>SonicPlay — Resonance</title>
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
    <div id="hud">Resonance : Hypnotic Circular Waveform (click, drag, space for trance mode)</div>
    <audio id="audio" controls src="{audio_src}" style="display:none"></audio>

    <script>
      const BEATS = {beats_js};
      let audio=null, audioCtx=null, analyser=null, sourceNode=null;
      let freqData=null, angle=0, trance=false;
      let lastBeatPulse=0, auraPulse=0;
      let trailAlpha = 24;

      // Global effects
      let flashAlpha = 0; 
      let shockwaves = []; // each shockwave: {{ r, life, thickness }}

      function initAudio(){{
        audio = document.getElementById('audio');
        if (!audio) return;
        if (audioCtx && audioCtx.state !== 'closed') return;
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 1024;
        freqData = new Uint8Array(analyser.frequencyBinCount);
        try {{ sourceNode = audioCtx.createMediaElementSource(audio); }} catch (e) {{ console.warn(e); }}
        if (sourceNode) {{
          sourceNode.connect(analyser);
          analyser.connect(audioCtx.destination);
        }}
      }}

      function setup(){{
        let c = createCanvas(window.innerWidth, window.innerHeight);
        c.parent(document.getElementById('sketch'));
        angleMode(RADIANS);
        colorMode(HSB, 360, 100, 100, 255);
        initAudio();
        noFill();
        strokeCap(ROUND);
        strokeJoin(ROUND);
      }}

      function windowResized(){{ resizeCanvas(window.innerWidth, window.innerHeight); }}

      function avg(arr){{
        if (!arr || arr.length === 0) return 0;
        let s = 0;
        for (let v of arr) s += v;
        return s / arr.length;
      }}

      function spawnShockwave(baseR){{
        shockwaves.push({{ r: baseR * 1.1, life: 1.0, thickness: 8 }});
      }}

      function draw(){{
        // translucent trails
        push();
        noStroke();
        fill(5, 10, 15, trailAlpha);
        rect(0, 0, width, height);
        pop();

        if (!audioCtx) initAudio();
        if (analyser) analyser.getByteFrequencyData(freqData);

        let now = audio && audio.currentTime ? audio.currentTime : millis() / 1000.0;
        let beat = false;
        if (BEATS && BEATS.length > 0) {{
          for (let t of BEATS) {{
            if (Math.abs(t - now) < 0.07 && millis() - lastBeatPulse > 120) {{
              beat = true;
              lastBeatPulse = millis();
              auraPulse = 60;
              flashAlpha = 120; // reduced for eye comfort
            }}
          }}
        }} else {{
          if (freqData) {{
            let bass = 0;
            let bins = Math.min(40, freqData.length);
            for (let i = 0; i < bins; i++) bass += freqData[i];
            bass = bass / Math.max(1, bins);
            if (bass > 90 && millis() - lastBeatPulse > 150) {{
              beat = true;
              lastBeatPulse = millis();
              auraPulse = 40;
              flashAlpha = 100; // softer fallback flash
            }}
          }}
        }}

        // center & breathing
        translate(width/2, height/2);
        let bassEnergy = freqData ? avg(Array.from(freqData).slice(0,64)) / 255 : 0;
        let mids = freqData ? avg(Array.from(freqData).slice(Math.floor(freqData.length*0.2), Math.floor(freqData.length*0.5))) / 255 : 0;
        let treble = freqData ? avg(Array.from(freqData).slice(Math.floor(freqData.length*0.5), Math.floor(freqData.length*0.9))) / 255 : 0;

        const minDim = Math.min(width, height);
        let baseRadius = (minDim * 0.22) * (1 + bassEnergy * 0.9);
        let breath = map(Math.sin(frameCount * 0.015), -1, 1, 0.96, 1.06);
        baseRadius *= breath * (trance ? 1.06 : 1);

        // rotation
        angle += 0.002 + (mouseIsPressed ? 0.02 : 0.0) + (treble * 0.005);
        rotate(angle);

        // aura glow
        if (auraPulse > 0) {{
          push();
          blendMode(ADD);
          for (let g = 0; g < 5; g++) {{
            let s = baseRadius * (2 + g * 0.08) + auraPulse * 0.5;
            stroke((frameCount * 0.6 + g * 50) % 360, 90, 100, 60);
            strokeWeight(5 - g);
            noFill();
            ellipse(0, 0, s, s);
          }}
          pop();
          auraPulse = Math.max(0, auraPulse - 1.5);
        }}

        // 3D tilt illusion
        let tilt = map(Math.cos(frameCount * 0.004 + Math.sin(frameCount * 0.001)), -1, 1, 0.88, 1.0);
        scale(1, tilt);

        // On beat spawn shockwaves
        if (beat) {{
          spawnShockwave(baseRadius * 0.98);
          if (random() < 0.55) spawnShockwave(baseRadius * 0.6);
        }}

        // Draw shockwaves
        push();
        blendMode(ADD);
        for (let i = shockwaves.length - 1; i >= 0; i--) {{
          let s = shockwaves[i];
          s.life -= 0.005;
          s.r += 4 + 8 * (0.5 + bassEnergy);
          let alpha = constrain(160 * s.life, 0, 160);
          stroke((frameCount*0.6 + i*40) % 360, 90, 80, alpha);
          strokeWeight(s.thickness * (1 + (1 - s.life) * 1.5));
          noFill();
          ellipse(0, 0, s.r * 2, s.r * 1.6);
          if (s.life <= 0) shockwaves.splice(i, 1);
        }}
        pop();

        // Primary neon ribbons
        const ribbons = 4;
        let points = 320;
        for (let r = 0; r < ribbons; r++) {{
          let hue = (frameCount * 0.6 + r * 90) % 360;
          stroke(hue, 90, 100, 180);
          strokeWeight(2.2 + (beat ? 0.8 : 0));
          noFill();
          beginShape();
          for (let i = 0; i <= points; i++) {{
            let a = TWO_PI * i / points;
            let idx = Math.floor(map(i, 0, points, 0, freqData.length-1));
            let amp = (freqData && freqData[idx]) ? freqData[idx] / 255 : 0;
            let slow = Math.sin(a * 2 + frameCount * 0.01 + r) * (20 + bassEnergy * 40);
            let mid  = Math.sin(a * 6 + frameCount * 0.02 + r * 0.5) * (10 + mids * 30);
            let hi   = Math.sin(a * 14 + frameCount * 0.05 + r) * (4 + treble * 18);
            let deform = slow + mid + hi;
            let radius = baseRadius * (1 + r*0.08) + deform + amp * 90;
            let x = radius * Math.cos(a);
            let y = radius * Math.sin(a);
            vertex(x, y);
          }}
          endShape(CLOSE);
        }}

        scale(1, 1/tilt);

        // Flash Bloom overlay (softer neon, no white)
        if (flashAlpha > 3) {{
          push();
          blendMode(ADD);
          let fh = (frameCount * 1.5 + Math.random()*30) % 360; // hue cycles
          noStroke();
          fill(fh, 90, 70, flashAlpha); // dimmer brightness
          resetMatrix();
          rect(0, 0, width, height);
          pop();
          flashAlpha = Math.max(0, flashAlpha - 3.5); // slower smooth fade
        }}

      }}

      function mouseDragged(){{ angle += (mouseX - pmouseX) * 0.008; }}
      function doubleClicked(){{ auraPulse = Math.max(auraPulse, 120); }}
      function keyPressed(){{ if (key === ' ') {{ trance = !trance; trailAlpha = trance ? 12 : 24; }} }}
    </script>
  </body>
</html>
"""