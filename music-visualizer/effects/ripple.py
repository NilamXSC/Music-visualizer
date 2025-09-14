# effects/ripple.py

def render_effect(beats, theme, sensitivity, particle_count, audio_url_data):
    """
    Ripple visualizer effect.
    Returns an HTML string to embed with st.components.v1.html().
    """
    beats_js = str(beats)
    theme_js = theme
    sens_js = float(sensitivity)
    particle_count_js = int(particle_count)

    html_template = r"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.5.0/p5.min.js"></script>
    <style>
      html, body {{ margin:0; padding:0; overflow:hidden; background:#02010a; color:#ddd; }}
      #sketch {{ width:100%; height:100%; position:relative; }}
      #dbg {{ position:absolute; top:6px; right:12px; background:rgba(0,0,0,0.5); color:#fff; padding:6px 10px; border-radius:6px; z-index:9999; font-size:12px; }}
      #errbox {{ position:absolute; bottom:6px; left:12px; background:#330000; color:#ffb3b3; padding:8px 12px; border-radius:6px; z-index:9999; display:none; }}
    </style>
  </head>
  <body>
    <div id="sketch"></div>
    <div id="dbg">Visualizer initializing...</div>
    <div id="errbox"></div>

    <script>
      try {
        console.log("Ripple Visualizer: start");
        document.getElementById('dbg').innerText = "";

        const beats = __BEATS__;
        const THEME = "__THEME__";
        const SENSITIVITY = __SENS__;
        const PARTICLE_COUNT = __PARTICLES__;
        let ripples = [];
        let particles = [];
        let beatIndex = 0;
        let audio = null;
        let audioCtx = null;
        let analyser = null;
        let freqData = null;
        let bassHistory = [];
        let lastAutoRippleTime = 0;

        function initAudio() {
          audio = document.getElementById('audio');
          if (!audio) {
            var auds = document.getElementsByTagName('audio');
            if (auds.length > 0) audio = auds[0];
          }
          if (!audio) {
            console.warn("Ripple: no audio element found.");
            document.getElementById('errbox').innerText = "";
            document.getElementById('errbox').style.display = 'block';
            return;
          }
          try {
            if (!audioCtx || audioCtx.state === 'closed') {
              audioCtx = new (window.AudioContext || window.webkitAudioContext)();
              analyser = audioCtx.createAnalyser();
              analyser.fftSize = 1024;
              const source = audioCtx.createMediaElementSource(audio);
              source.connect(analyser);
              analyser.connect(audioCtx.destination);
              freqData = new Uint8Array(analyser.frequencyBinCount);
              document.getElementById('dbg').innerText = "Visualizer ready — play audio!";
            }
          } catch (e) {
            console.warn("Ripple WebAudio init failed:", e);
            document.getElementById('errbox').innerText = "WebAudio init failed: " + e;
            document.getElementById('errbox').style.display = 'block';
          }
        }

        class Particle {
          constructor() {
            this.x = random(width);
            this.y = random(height);
            this.vx = random(-0.25, 0.25);
            this.vy = random(-0.25, 0.25);
            this.r = random(1, 2.2);
          }
          update() {
            this.x += this.vx; this.y += this.vy;
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;
          }
          show() {
            strokeWeight(1);
            if (THEME === "Neon (dark)") stroke(120,140,180,120);
            else if (THEME === "Light") stroke(60,60,60,110);
            else stroke(130,170,230,120);
            point(this.x, this.y);
          }
        }

        function drawConnections() {
          for (let i = 0; i < particles.length; i++) {
            for (let j = i+1; j < particles.length; j++) {
              const d = dist(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
              if (d < 120) {
                const alpha = map(d, 0, 120, 120, 10);
                if (THEME === "Neon (dark)") stroke(100,120,160,alpha);
                else if (THEME === "Light") stroke(90,90,90,alpha);
                else stroke(110,150,210,alpha);
                strokeWeight(0.9);
                line(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
              }
            }
          }
        }

        function setup() {
          let c = createCanvas(window.innerWidth*0.75, 600);
          c.parent(document.getElementById('sketch'));
          noFill();
          for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle());
          initAudio();
        }

        function windowResized() { resizeCanvas(window.innerWidth*0.75, 600); }

        function draw() {
          background(2,1,10,30);
          for (let p of particles) { p.update(); p.show(); }
          drawConnections();

          if (!audio) initAudio();

          // bass detection
          if (analyser && freqData) {
            analyser.getByteFrequencyData(freqData);
            let bassBins = 12;
            let bassEnergy = 0;
            for (let i = 0; i < Math.min(bassBins, freqData.length); i++) bassEnergy += freqData[i];
            bassEnergy = bassEnergy / bassBins;
            bassHistory.push(bassEnergy);
            if (bassHistory.length > 8) bassHistory.shift();
            const avgBass = bassHistory.reduce((a,b)=>a+b,0)/bassHistory.length;
            const threshold = avgBass * (1.0 + (SENSITIVITY - 1.0) * 0.9);
            const nowT = audio ? audio.currentTime : millis()/1000.0;
            if (bassEnergy > threshold && (nowT - lastAutoRippleTime) > 0.08) {
              const rx = random(width*0.2, width*0.8);
              const ry = random(height*0.2, height*0.8);
              ripples.push(new Ripple(rx, ry, false, 6));
              lastAutoRippleTime = nowT;
            }
          }

          // beat-based ripples
          if (audio && beats && beats.length > 0) {
            const now = audio.currentTime;
            while (beatIndex < beats.length && beats[beatIndex] <= now) {
              const x = random(width*0.12, width*0.88);
              const y = random(height*0.12, height*0.88);
              ripples.push(new Ripple(x, y, false));
              beatIndex++;
            }
          }

          for (let i = ripples.length-1; i >= 0; i--) {
            ripples[i].update(); ripples[i].show();
            if (ripples[i].finished()) ripples.splice(i,1);
          }
        }

        function mousePressed() { ripples.push(new Ripple(mouseX, mouseY, true)); }
        function mouseDragged() { ripples.push(new Ripple(mouseX, mouseY, true, 4)); }

        class Ripple {
          constructor(x,y,interactive=false,startR=6) {
            this.x = x; this.y = y; this.r = startR; this.alpha = 255; this.interactive = interactive;
          }
          update() { this.r += (this.interactive ? 8 : 5); this.alpha -= (this.interactive ? 6 : 3); }
          finished() { return this.alpha < 0 || this.r > max(width, height)*1.5; }
          show() {
            strokeWeight(this.interactive ? 3 : 2);
            if (THEME === "Neon (dark)") stroke(120, 200, 255, this.alpha);
            else if (THEME === "Light") stroke(40,40,40, this.alpha);
            else stroke(80,150,240, this.alpha);
            ellipse(this.x, this.y, this.r*2);
          }
        }

      } catch (err) {
        console.error("Ripple Visualizer error:", err);
        const eb = document.getElementById('errbox');
        eb.innerText = "Visualizer error: " + err;
        eb.style.display = 'block';
      }
    </script>
  </body>
</html>
"""
    return (
        html_template
        .replace("__BEATS__", beats_js)
        .replace("__THEME__", theme_js)
        .replace("__SENS__", str(sens_js))
        .replace("__PARTICLES__", str(particle_count_js))
    )