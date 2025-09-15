import streamlit as st

def render_custom_player(audio_url_data: str, logo_b64: str = "", height: int = 900):
    """
    Render the custom cyber player UI into Streamlit.
    - audio_url_data: data:... base64 audio src (same as in your app)
    - logo_b64: optional base64 string for the logo to show in the header (dynamic).
    - height: iframe height passed to st.components.v1.html
    """
    # NOTE: We keep all JS/audio/preset/visualizer logic unchanged from your working file.
    # Only update the HTML/CSS wrapper, select styling, logo injection, and some minor layout fixes.
    custom_player_template = r'''
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
    /* Reset box-sizing for player scope to avoid unexpected overflow */
    #playerRoot, #playerRoot * { box-sizing: border-box; }

    /* Root variables (player-only scope via #playerRoot) */
    #playerRoot {
      --bg: #070816;
      --panel: rgba(10,10,16,0.88);
      --accent-1: #ff2d95;
      --accent-2: #ff9a2d;
      --muted: #bfc7d6;
      --glass: rgba(255,255,255,0.03);
      --radius: 16px;
      --btn-radius: 12px;
      --soft-shadow: 0 12px 40px rgba(0,0,0,0.6);
      font-family: Inter, "Orbitron", sans-serif;
      color: #fff;
      display:block;
      /* ensure player always fits the iframe width with a small inner margin */
      padding: 8px;
    }

    /* basic layout */
    .player-container {
      width:100%;
      max-width: calc(100% - 24px); /* always fit within iframe, avoid right edge cutoff */
      background: var(--panel);
      border-radius: var(--radius);
      padding:18px;
      color:inherit;
      position:relative;
      overflow:visible;
      box-shadow: var(--soft-shadow);
      transition: box-shadow 200ms ease;
      border: 1px solid rgba(255,255,255,0.03);
      margin: 0 auto;
    }
    /* Remove whole-player pop on hover; only buttons will pop */
    .player-container:hover { box-shadow: 0 18px 48px rgba(0,0,0,0.7); }

    .player-header { display:flex; align-items:center; justify-content:space-between; gap:12px; z-index:3; position:relative; }
    .player-title { display:flex; gap:12px; align-items:center; min-width:0; }
    .logo-mini {
      width:48px;
      height:48px;
      border-radius:12px;
      background: linear-gradient(90deg,var(--accent-1),var(--accent-2));
      display:flex; align-items:center; justify-content:center;
      font-weight:800; color:#071018;
      box-shadow: 0 6px 18px rgba(0,0,0,0.45);
      flex: 0 0 auto;
      overflow: hidden;
      position: relative;
    }
    /* hide stray green/colored marker - ensure no background stripe shows */
    .logo-mini:before { content: ""; position:absolute; inset:0; background:transparent; pointer-events:none; }

    .logo-mini img { width:100%; height:100%; object-fit:cover; display:block; border-radius:10px; }

    .muted { color:var(--muted); font-size:13px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

    /* controls grid */
    .controls-grid { display:grid; grid-template-columns: 1fr; gap:14px; margin-top:12px; z-index:3; }
    .controls {
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      padding:14px;
      border-radius:12px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.03);
    }

    /* Buttons */
    .btn {
      background: linear-gradient(90deg,var(--accent-1),var(--accent-2));
      border:none;
      padding:10px 16px;
      border-radius: var(--btn-radius);
      color:#071018;
      font-weight:800;
      cursor:pointer;
      display:inline-flex;
      align-items:center;
      gap:8px;
      transition: transform 120ms ease, box-shadow 120ms ease;
      box-shadow: 0 8px 20px rgba(0,0,0,0.45);
      user-select:none;
    }
    /* Button hover pop only (not entire player) */
    .btn:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(0,0,0,0.5); }

    .btn-ghost {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.06);
      color:var(--muted);
      padding:10px 14px;
      border-radius: var(--btn-radius);
      cursor:pointer;
      transition: background 140ms ease, color 140ms ease;
    }
    .btn-ghost:hover { background: rgba(255,255,255,0.02); color: #fff; }

    /* sliders & inputs */
    label.small { font-size:12px; color:var(--muted); display:block; margin-bottom:8px; }
    input[type="range"].slider { width:100%; height:8px; -webkit-appearance:none; background: linear-gradient(90deg,#0b0b12,#252533); border-radius:10px; outline:none; }
    input[type="range"].slider::-webkit-slider-thumb { -webkit-appearance:none; width:16px; height:16px; border-radius:50%; background: radial-gradient(circle,var(--accent-2),var(--accent-1)); border:2px solid rgba(0,0,0,0.35); box-shadow: 0 4px 14px rgba(0,0,0,0.4); cursor:pointer; }
    .small-input { width:100%; padding:8px 10px; border-radius:10px; background:transparent; border:1px solid rgba(255,255,255,0.04); color:#fff; }

    .small-input, select.small-input {
      /* ensure dropdown inherits dark background */
      background: rgba(0,0,0,0.18);
      color: #fff;
      -webkit-appearance: none;
      -moz-appearance: none;
      appearance: none;
      padding-right: 28px;
    }

    /* style the select arrow and dropdown background via native appearance fallback */
    select.small-input {
      background-image: linear-gradient(45deg, transparent 50%, rgba(255,255,255,0.12) 50%),
                        linear-gradient(135deg, rgba(255,255,255,0.12) 50%, transparent 50%),
                        linear-gradient(to right, rgba(255,255,255,0.02), rgba(255,255,255,0.02));
      background-position: calc(100% - 18px) calc(1em + 2px), calc(100% - 13px) calc(1em + 2px), calc(100% - 2.5em) 0.5em;
      background-size: 5px 5px, 5px 5px, 1px 1.5em;
      background-repeat: no-repeat;
      border-radius: 10px;
    }

    /* option styling - note: some browsers don't style option backgrounds */
    select.small-input option { background: rgba(0,0,0,0.9); color: #fff; }

    .flex-between { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
    .row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }

    /* preset list */
    .preset-list { max-height:160px; overflow:auto; margin-top:8px; padding:8px; border-radius:10px; background: rgba(0,0,0,0.03); border:1px solid rgba(255,255,255,0.02); }

    /* visual stage */
    .vis-stage { position:relative; margin-top:12px; border-radius:12px; overflow:hidden; }
    #visCanvasLarge {
      width:100%;
      height:320px;
      display:block;
      background:transparent;
      border-radius:10px;
      /* subtle inner border to match screenshots */
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
    }

    /* player glow (muted) - subtle boundary glow */
    .player-glow {
      position:absolute;
      left:50%;
      top:50%;
      transform:translate(-50%,-50%);
      width:900px;
      height:900px;
      filter: blur(80px);
      opacity:0.06;
      pointer-events:none;
      z-index:0;
      mix-blend-mode:screen;
    }

    /* player boundary glow ring (keeps flowing) */
    .player-container::after {
      content: "";
      position: absolute;
      inset: -2px;
      border-radius: calc(var(--radius) + 2px);
      pointer-events: none;
      background: linear-gradient(90deg, rgba(255,45,149,0.02), rgba(127,92,255,0.02), rgba(0,255,213,0.01));
      filter: blur(8px);
      z-index: -1;
    }

    /* themes (player-only) */
    #playerRoot.theme-neon { --panel: rgba(10,10,20,0.95); --accent-1:#ff2d95; --accent-2:#ff9a2d; --muted:#c6cbe0; }
    #playerRoot.theme-cyberpunk { --panel: linear-gradient(180deg, rgba(7,2,18,0.95), rgba(10,4,26,0.95)); --accent-1:#00fff0; --accent-2:#ff00c8; --muted:#b9dff3; }
    #playerRoot.theme-vaporwave { --panel: linear-gradient(180deg, rgba(28,8,88,0.95), rgba(255,145,170,0.06)); --accent-1:#ff9a9e; --accent-2:#a1c4fd; --muted:#ffe9f2; }
    #playerRoot.theme-galaxy { --panel: linear-gradient(180deg, rgba(2,8,20,0.96), rgba(6,10,28,0.96)); --accent-1:#7f5cff; --accent-2:#00ffd5; --muted:#c8eaff; }

    /* "vibrant" animated rainbow theme: JS will animate --accent colors */
    #playerRoot.theme-vibrant { --panel: rgba(6,6,12,0.9); --accent-1:#ff2d95; --accent-2:#ff9a2d; --muted:#e6e6e6; transition: background-color 300ms linear; }

    /* small responsive tweaks */
    @media (max-width:640px) {
      .player-container { padding:12px; }
      .logo-mini { width:40px; height:40px; border-radius:10px; }
      #visCanvasLarge { height:220px; }
      select.small-input { width: 140px; }
    }
    </style>

    <div id="playerRoot" class="player-root theme-neon" role="region" aria-label="SonicPlay custom player">
      <div class="player-container" id="playerContainer">
        <div class="player-header" role="banner">
          <div class="player-title">
            <div class="logo-mini" id="logoMini"><i class="fa-solid fa-music"></i></div>
            <div style="min-width:0;">
              <div style="font-size:16px; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">SonicPlay</div>
              <div class="muted" style="margin-top:6px;">Enjoy !</div>
            </div>
          </div>

          <div style="display:flex; gap:8px; align-items:center;">
            <select id="playerThemeSelect" class="small-input" style="width:180px;">
              <option value="theme-neon">Neon (dark)</option>
              <option value="theme-cyberpunk">Cyberpunk</option>
              <option value="theme-vaporwave">Vaporwave</option>
              <option value="theme-galaxy">Galaxy</option>
              <option value="theme-vibrant">Vibrant (animated)</option>
            </select>
          </div>
        </div>

        <div class="controls-grid">
          <div class="controls" role="region" aria-label="player controls">
            <audio id="audioEl" crossorigin="anonymous" src="__AUDIO_SRC__"></audio>

            <div class="flex-between" style="margin-top:6px;">
              <div class="row">
                <button id="playBtn" class="btn">▶ Play</button>
                <button id="pauseBtn" class="btn btn-ghost">⏸ Pause</button>
                <button id="stopBtn" class="btn btn-ghost">■ Stop</button>
              </div>
              <div style="text-align:right;">
                <div id="recStatus" class="muted">Not recording</div>
                <a id="downloadLink" style="display:none; color:#fff; font-size:13px;"></a>
              </div>
            </div>
            
            <div class="vis-stage" style="margin-top:16px;">
              <div class="player-glow" id="playerGlow"></div>
              <canvas id="visCanvasLarge" aria-hidden="true"></canvas>
              <div style="position:absolute; left:12px; top:12px; z-index:4;">
                <div class="muted"></div>
              </div>
            </div>  

            <div style="margin-top:12px;">
              <label class="small">Seek</label>
              <input id="seekSlider" type="range" class="slider" min="0" max="100" value="0">
              <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--muted); margin-top:8px;">
                <div id="timeCurrent">0:00</div>
                <div id="timeTotal">0:00</div>
              </div>
            </div>

            <div style="display:flex; gap:12px; margin-top:12px; flex-wrap:wrap;">
              <div style="flex:1; min-width:160px;">
                <label class="small">Volume</label>
                <input id="volume" class="slider" type="range" min="0" max="1" step="0.01" value="1">
              </div>
              <div style="width:160px;">
                <label class="small">Pan</label>
                <input id="pan" class="slider" type="range" min="-1" max="1" step="0.01" value="0">
              </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px;">
              <div>
                <label class="small">Bass (Lowshelf) 0 → +20 dB</label>
                <input id="bass" class="slider" type="range" min="0" max="20" step="0.5" value="0">
              </div>
              <div>
                <label class="small">Treble (High shelf) -10 → +10 dB</label>
                <input id="treble" class="slider" type="range" min="-10" max="10" step="0.5" value="0">
              </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px;">
              <div>
                <label class="small">Delay Time (ms)</label>
                <input id="delayTime" class="slider" type="range" min="0" max="1200" step="5" value="0">
              </div>
              <div>
                <label class="small">Delay Feedback</label>
                <input id="delayFeedback" class="slider" type="range" min="0" max="0.95" step="0.01" value="0.25">
              </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px;">
              <div>
                <label class="small">Reverb Wet/Dry</label>
                <input id="reverbWet" class="slider" type="range" min="0" max="1" step="0.01" value="0.25">
              </div>
              <div>
                <label class="small">Pitch Shift (playbackRate)</label>
                <input id="playbackRate" class="slider" type="range" min="0.5" max="1.6" step="0.01" value="1.0">
              </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px;">
              <div>
                <label class="small">DJ Sweep (LP cutoff)</label>
                <input id="sweep" class="slider" type="range" min="60" max="12000" step="10" value="12000">
              </div>
              <div style="display:flex;align-items:center; gap:10px;">
                <div>
                  <label class="small">Robotic (distortion)</label><br>
                  <input id="robot" type="checkbox" style="transform:scale(1.25); margin-top:6px;">
                </div>
                <div style="margin-left:auto; min-width:120px;">
                  <label class="small">Presets</label>
                  <div style="display:flex; gap:8px;">
                    <select id="presetSelect" class="small-input" style="width:100%;">
                      <option value="">-- Choose preset --</option>
                    </select>
                    <input id="presetName" class="small-input" placeholder="Name" style="width:140px;">
                    <button id="savePresetBtn" class="btn btn-ghost" style="padding:8px 10px;">Save</button>
                  </div>
                  <div style="display:flex; gap:8px; margin-top:8px;">
                    <button id="delPresetBtn" class="btn btn-ghost" style="padding:8px 10px;">Delete</button>
                    <div id="presetMsg" class="muted" style="align-self:center;"></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="preset-list" id="presetList" aria-live="polite" style="margin-top:12px;"></div>
          </div>
        </div>
      </div>
    </div>

    <script>
    (function(){
      // Element refs
      const audioEl = document.getElementById('audioEl');
      const playBtn = document.getElementById('playBtn');
      const pauseBtn = document.getElementById('pauseBtn');
      const stopBtn = document.getElementById('stopBtn');
      const recordBtn = document.getElementById('recordBtn');
      const recStatus = document.getElementById('recStatus');
      const downloadLink = document.getElementById('downloadLink');

      const seekSlider = document.getElementById('seekSlider');
      const timeCurrent = document.getElementById('timeCurrent');
      const timeTotal = document.getElementById('timeTotal');
      const volume = document.getElementById('volume');
      const pan = document.getElementById('pan');
      const bass = document.getElementById('bass');
      const treble = document.getElementById('treble');
      const delayTime = document.getElementById('delayTime');
      const delayFeedback = document.getElementById('delayFeedback');
      const reverbWet = document.getElementById('reverbWet');
      const playbackRate = document.getElementById('playbackRate');
      const sweep = document.getElementById('sweep');
      const robot = document.getElementById('robot');

      const presetSelect = document.getElementById('presetSelect');
      const presetName = document.getElementById('presetName');
      const savePresetBtn = document.getElementById('savePresetBtn');
      const delPresetBtn = document.getElementById('delPresetBtn');
      const presetList = document.getElementById('presetList');
      const presetMsg = document.getElementById('presetMsg');

      const themeSelect = document.getElementById('playerThemeSelect');
      const playerRoot = document.getElementById('playerRoot');
      const playerGlow = document.getElementById('playerGlow');

      const canvas = document.getElementById('visCanvasLarge');
      const ctx = canvas.getContext('2d');

      // HiDPI canvas resize
      function resizeCanvas(){
        const rect = canvas.getBoundingClientRect();
        const ratio = window.devicePixelRatio || 1;
        canvas.width = Math.floor(rect.width * ratio);
        canvas.height = Math.floor(rect.height * ratio);
        canvas.style.width = rect.width + "px";
        canvas.style.height = rect.height + "px";
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      }
      window.addEventListener('resize', resizeCanvas);
      setTimeout(resizeCanvas, 120);

      // audio context & nodes
      let audioCtx = null;
      let source = null;
      let analyser = null;
      let gainNode = null;
      let lowShelf = null;
      let highShelf = null;
      let delayNode = null;
      let delayGain = null;
      let sweepFilter = null;
      let panner = null;
      let distortion = null;
      let convolver = null;
      let dryGain = null;
      let wetGain = null;
      let mediaDest = null;
      let mediaStream = null;
      let mediaRecorder = null;
      let recordedChunks = [];
      let rafId = null;
      let particles = [];

      // preset storage key
      const PRESET_KEY = "sonicplay_presets_v2";

      // Utility
      function fmt(t){
        if (!isFinite(t)) return "0:00";
        const m = Math.floor(t/60);
        const s = Math.floor(t%60).toString().padStart(2,'0');
        return `${m}:${s}`;
      }

      // Impulse response for reverb
      function createImpulseResponse(ctx, duration=2.0, decay=2.0){
        const sr = ctx.sampleRate;
        const length = sr * duration;
        const impulse = ctx.createBuffer(2, length, sr);
        for (let c=0; c<2; c++){
          const channel = impulse.getChannelData(c);
          for (let i=0;i<length;i++){
            channel[i] = (Math.random()*2-1) * Math.pow(1 - i/length, decay);
          }
        }
        return impulse;
      }

      function makeDistortionCurve(amount){
        const k = typeof amount === 'number' ? amount : 50;
        const n = 44100;
        const curve = new Float32Array(n);
        const deg = Math.PI/180;
        for (let i=0;i<n;i++){
          const x = (i*2)/n - 1;
          curve[i] = ((3 + k) * x * 20 * deg) / (Math.PI + k * Math.abs(x));
        }
        return curve;
      }

      // init audio graph
      function initAudioCtx(){
        if (audioCtx) return;
        if (!window.AudioContext && !window.webkitAudioContext) {
          console.warn("No AudioContext");
          return;
        }
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        source = audioCtx.createMediaElementSource(audioEl);

        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.85;

        gainNode = audioCtx.createGain();

        lowShelf = audioCtx.createBiquadFilter();
        lowShelf.type = 'lowshelf';
        lowShelf.frequency.value = 200;

        highShelf = audioCtx.createBiquadFilter();
        highShelf.type = 'highshelf';
        highShelf.frequency.value = 4000;

        delayNode = audioCtx.createDelay(5.0);
        delayGain = audioCtx.createGain();

        sweepFilter = audioCtx.createBiquadFilter();
        sweepFilter.type = 'lowpass';
        sweepFilter.Q.value = 1.2;

        panner = audioCtx.createStereoPanner();

        distortion = audioCtx.createWaveShaper();
        distortion.curve = makeDistortionCurve(0);

        convolver = audioCtx.createConvolver();
        convolver.buffer = createImpulseResponse(audioCtx, 2.5, 3.0);

        dryGain = audioCtx.createGain();
        wetGain = audioCtx.createGain();

        // connect graph:
        // source -> lowShelf -> highShelf -> sweep -> (dry -> distortion) -> gain -> panner -> analyser -> destination
        source.connect(lowShelf);
        lowShelf.connect(highShelf);
        highShelf.connect(sweepFilter);

        sweepFilter.connect(dryGain);
        dryGain.connect(distortion);

        sweepFilter.connect(convolver);
        convolver.connect(wetGain);
        wetGain.connect(distortion);

        sweepFilter.connect(delayNode);
        delayNode.connect(delayGain);
        delayGain.connect(delayNode);
        delayNode.connect(distortion);

        distortion.connect(gainNode);
        gainNode.connect(panner);
        panner.connect(analyser);
        analyser.connect(audioCtx.destination);

        // for recording
        if (audioCtx.createMediaStreamDestination) {
          mediaDest = audioCtx.createMediaStreamDestination();
          panner.connect(mediaDest);
        }

        // initial connect values
        gainNode.gain.value = parseFloat(volume.value);
        delayGain.gain.value = parseFloat(delayFeedback.value);
        delayNode.delayTime.value = Math.max(0, parseFloat(delayTime.value)/1000);
        sweepFilter.frequency.value = parseFloat(sweep.value);
        wetGain.gain.value = parseFloat(reverbWet.value);
        dryGain.gain.value = Math.max(0, 1 - wetGain.gain.value);
        lowShelf.gain.value = parseFloat(bass.value);
        highShelf.gain.value = parseFloat(treble.value);
      }

      function connectChain(){
        if (!audioCtx) return;
        lowShelf.gain.value = parseFloat(bass.value);
        highShelf.gain.value = parseFloat(treble.value);
        delayNode.delayTime.value = Math.max(0, parseFloat(delayTime.value)/1000.0);
        delayGain.gain.value = parseFloat(delayFeedback.value);
        panner.pan.value = parseFloat(pan.value);
        sweepFilter.frequency.value = parseFloat(sweep.value);
        distortion.curve = robot.checked ? makeDistortionCurve(400) : makeDistortionCurve(0);
        wetGain.gain.value = parseFloat(reverbWet.value);
        dryGain.gain.value = Math.max(0, 1 - wetGain.gain.value);
        gainNode.gain.value = parseFloat(volume.value);
      }

      // playback controls
      playBtn.addEventListener('click', async () => {
        if (!audioCtx) initAudioCtx();
        connectChain();
        // resume context if suspended
        if (audioCtx && audioCtx.state === 'suspended') {
          try { await audioCtx.resume(); } catch(e){}
        }
        try { await audioEl.play(); } catch(e) { console.warn("play error", e); }
        startVisualLoop();
      });

      pauseBtn.addEventListener('click', () => { audioEl.pause(); });

      stopBtn.addEventListener('click', () => {
        audioEl.pause();
        audioEl.currentTime = 0;
        seekSlider.value = 0;
        stopVisualLoop();
      });

      // seeking/time updates
      audioEl.addEventListener('loadedmetadata', () => {
        timeTotal.innerText = fmt(audioEl.duration || 0);
      });
      audioEl.addEventListener('timeupdate', () => {
        if (isFinite(audioEl.duration) && audioEl.duration > 0) {
          seekSlider.value = (audioEl.currentTime / audioEl.duration) * 100;
        }
        timeCurrent.innerText = fmt(audioEl.currentTime);
      });
      seekSlider.addEventListener('input', () => {
        if (isFinite(audioEl.duration) && audioEl.duration > 0) {
          audioEl.currentTime = (seekSlider.value / 100) * audioEl.duration;
        }
      });

      // volume & playbackRate
      volume.addEventListener('input', () => {
        if (gainNode) gainNode.gain.value = parseFloat(volume.value);
        audioEl.volume = parseFloat(volume.value);
      });
      playbackRate.addEventListener('input', () => { audioEl.playbackRate = parseFloat(playbackRate.value); });

      // other controls -> update chain
      [bass, treble, delayTime, delayFeedback, pan, sweep, robot, reverbWet].forEach(el => {
        el.addEventListener('input', connectChain);
        el.addEventListener('change', connectChain);
      });

      // THEMES: only affect the playerRoot
      function applyTheme(themeClass){
        playerRoot.classList.remove('theme-neon','theme-cyberpunk','theme-vaporwave','theme-galaxy','theme-vibrant');
        playerRoot.classList.add(themeClass);
        // if vibrant, start animation, else stop
        if (themeClass === 'theme-vibrant') startVibrant(); else stopVibrant();
      }
      themeSelect.addEventListener('change', (e) => { applyTheme(e.target.value); });
      applyTheme(themeSelect.value);

      // Vibrant theme animation (animates accent colors)
      let vibrantInterval = null;
      function startVibrant(){
        if (vibrantInterval) return;
        let t = 0;
        vibrantInterval = setInterval(()=>{
          t += 0.015;
          const r = Math.floor(128 + 127*Math.sin(t));
          const g = Math.floor(128 + 127*Math.sin(t + 2));
          const b = Math.floor(128 + 127*Math.sin(t + 4));
          const r2 = Math.floor(128 + 127*Math.sin(t + 1.2));
          const g2 = Math.floor(128 + 127*Math.sin(t + 3.2));
          const b2 = Math.floor(128 + 127*Math.sin(t + 5.2));
          const c1 = `rgb(${r},${g},${b})`;
          const c2 = `rgb(${r2},${g2},${b2})`;
          playerRoot.style.setProperty('--accent-1', c1);
          playerRoot.style.setProperty('--accent-2', c2);
        }, 60);
      }
      function stopVibrant(){
        if (vibrantInterval) { clearInterval(vibrantInterval); vibrantInterval = null; }
        // reset to default neon
        playerRoot.style.removeProperty('--accent-1');
        playerRoot.style.removeProperty('--accent-2');
      }

      // PRESETS: store/load simple presets in localStorage
      const defaultPresets = {
        "Club": {volume:1, bass:8, treble:2, delayTime:120, delayFeedback:0.35, reverbWet:0.2, playbackRate:1.0, pan:0, sweep:8000, robot:false},
        "Vocal Boost": {volume:1, bass:2, treble:6, delayTime:40, delayFeedback:0.12, reverbWet:0.05, playbackRate:1.0, pan:0, sweep:9000, robot:false},
        "Chillout": {volume:0.9, bass:4, treble:-2, delayTime:400, delayFeedback:0.45, reverbWet:0.45, playbackRate:0.95, pan:0, sweep:6000, robot:false}
      };

      function loadPresetsFromStorage(){
        try {
          const raw = localStorage.getItem(PRESET_KEY);
          if (!raw) {
            localStorage.setItem(PRESET_KEY, JSON.stringify(defaultPresets));
            return JSON.parse(JSON.stringify(defaultPresets));
          }
          return JSON.parse(raw);
        } catch(e) {
          console.warn("presets read err", e);
          localStorage.setItem(PRESET_KEY, JSON.stringify(defaultPresets));
          return JSON.parse(JSON.stringify(defaultPresets));
        }
      }
      function savePresetsToStorage(obj){
        try { localStorage.setItem(PRESET_KEY, JSON.stringify(obj)); } catch(e){ console.warn("presets save err", e); }
      }

      function refreshPresetUI(){
        const presets = loadPresetsFromStorage();
        presetSelect.innerHTML = '<option value="">-- Choose preset --</option>';
        presetList.innerHTML = '';
        Object.keys(presets).forEach(k=>{
          const opt = document.createElement('option'); opt.value = k; opt.innerText = k; presetSelect.appendChild(opt);
          const div = document.createElement('div'); div.className = 'muted';
          div.style.marginBottom = '6px';
          div.innerText = `${k} — ${Object.keys(presets[k]).map(key=>`${key}:${presets[k][key]}`).join(', ')}`;
          presetList.appendChild(div);
        });
      }
      refreshPresetUI();

      presetSelect.addEventListener('change', ()=>{
        const val = presetSelect.value;
        if (!val) return;
        const presets = loadPresetsFromStorage();
        const p = presets[val];
        if (!p) return;
        volume.value = p.volume;
        bass.value = p.bass;
        treble.value = p.treble;
        delayTime.value = p.delayTime;
        delayFeedback.value = p.delayFeedback;
        reverbWet.value = p.reverbWet;
        playbackRate.value = p.playbackRate;
        pan.value = p.pan;
        sweep.value = p.sweep;
        robot.checked = !!p.robot;
        audioEl.volume = parseFloat(volume.value);
        audioEl.playbackRate = parseFloat(playbackRate.value);
        connectChain();
      });

      savePresetBtn.addEventListener('click', ()=>{
        const name = (presetName.value || '').trim();
        if (!name) {
          presetMsg.innerText = 'Enter name';
          setTimeout(()=>presetMsg.innerText='', 1500);
          return;
        }
        const presets = loadPresetsFromStorage();
        presets[name] = {
          volume: parseFloat(volume.value),
          bass: parseFloat(bass.value),
          treble: parseFloat(treble.value),
          delayTime: parseFloat(delayTime.value),
          delayFeedback: parseFloat(delayFeedback.value),
          reverbWet: parseFloat(reverbWet.value),
          playbackRate: parseFloat(playbackRate.value),
          pan: parseFloat(pan.value),
          sweep: parseFloat(sweep.value),
          robot: !!robot.checked
        };
        savePresetsToStorage(presets);
        refreshPresetUI();
        presetName.value = '';
        presetMsg.innerText = 'Saved';
        setTimeout(()=>presetMsg.innerText='', 1200);
      });

      delPresetBtn.addEventListener('click', ()=>{
        const name = presetSelect.value;
        if (!name) {
          presetMsg.innerText = 'Select preset';
          setTimeout(()=>presetMsg.innerText='', 1400);
          return;
        }
        const presets = loadPresetsFromStorage();
        if (presets[name]) delete presets[name];
        savePresetsToStorage(presets);
        refreshPresetUI();
        presetMsg.innerText = 'Deleted';
        setTimeout(()=>presetMsg.innerText='', 1200);
      });

      // RECORDING
      let recording = false;
      function startRecording(){
        if (recording) return;
        recordedChunks = [];
        if (audioEl.captureStream) {
          try { mediaStream = audioEl.captureStream(); } catch(e){ console.warn("captureStream failed", e); }
        }
        if (!mediaStream && mediaDest) mediaStream = mediaDest.stream;
        if (!mediaStream) {
          alert("Recording not supported in this browser");
          return;
        }
        mediaRecorder = new MediaRecorder(mediaStream);
        mediaRecorder.ondataavailable = (e)=> { if (e.data && e.data.size) recordedChunks.push(e.data); };
        mediaRecorder.onstop = ()=>{
          const blob = new Blob(recordedChunks, { type: 'audio/webm' });
          const url = URL.createObjectURL(blob);
          downloadLink.href = url;
          downloadLink.download = 'sonicplay_recording.webm';
          downloadLink.style.display = 'inline';
          downloadLink.innerText = 'Download Recording';
          recStatus.innerText = 'Recording stopped';
        };
        mediaRecorder.start();
        recording = true;
        recStatus.innerText = 'Recording...';
        recordBtn.innerText = '■ Stop';
        downloadLink.style.display = 'none';
      }
      function stopRecording(){
        if (!recording || !mediaRecorder) return;
        mediaRecorder.stop();
        recording = false;
        recStatus.innerText = 'Finalizing...';
        recordBtn.innerText = '● Record';
      }
      recordBtn.addEventListener('click', ()=>{
        if (!audioCtx) initAudioCtx();
        if (!mediaStream && mediaDest && audioCtx) mediaStream = mediaDest.stream;
        if (!recording) startRecording(); else stopRecording();
      });

      // VISUALIZER
      function spawnParticle(x,y,vx,vy,size,hue,life){ particles.push({x,y,vx,vy,size,hue,life}); }
      function drawParticles(freqData, trebleEnergy, intensityFactor){
        const w = canvas.clientWidth, h = canvas.clientHeight;
        const spawns = Math.floor(1 + Math.min(6, trebleEnergy/30) * intensityFactor);
        for (let i=0;i<spawns;i++){
          const x = Math.random()*w;
          const y = h - Math.random()*30;
          spawnParticle(x, y, (Math.random()-0.5)*2.4, -2 - Math.random()*3, 2 + Math.random()*6, Math.floor(360*Math.random()), 40 + Math.random()*40);
        }
        for (let i=particles.length-1;i>=0;i--){
          const p = particles[i];
          p.x += p.vx; p.y += p.vy; p.vy += 0.08; p.life -= 1;
          const alpha = Math.max(0, p.life/60);
          ctx.beginPath();
          ctx.fillStyle = `hsla(${p.hue},80%,60%,${alpha})`;
          ctx.arc(p.x, p.y, p.size, 0, Math.PI*2);
          ctx.fill();
          if (p.life <= 0 || p.y > h + 50) particles.splice(i,1);
        }
      }

      function draw3DBars(freqData, intensityFactor){
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        const bars = 64;
        const step = Math.max(1, Math.floor(freqData.length / bars));
        const barWidth = (w / bars) * 0.9;
        const baseY = h * 0.8;
        ctx.save();
        for (let i=0;i<bars;i++){
          const idx = i*step;
          const v = freqData[idx] / 255;
          const height = v * (h*0.6) * (0.6 + (i/bars));
          const px = (i*(barWidth+2));
          const hue = Math.floor(200 + (i/bars)*160 + (v*60));
          ctx.fillStyle = `hsl(${hue},80%,55%)`;
          const topWidth = barWidth * (0.7 + (i/bars)*0.6);
          const x = px + (w - bars*(barWidth+2)) / 2;
          ctx.beginPath();
          ctx.moveTo(x, baseY);
          ctx.lineTo(x + barWidth, baseY);
          ctx.lineTo(x + (barWidth - topWidth)/2 + topWidth, baseY - height);
          ctx.lineTo(x + (barWidth - topWidth)/2, baseY - height);
          ctx.closePath();
          ctx.fill();
        }
        ctx.restore();
      }

      function startVisualLoop(){
        if (!analyser) {
          // fallback simple ambient render
          function simpleRender(){
            ctx.clearRect(0,0,canvas.clientWidth,canvas.clientHeight);
            ctx.fillStyle = 'rgba(255,255,255,0.01)';
            ctx.fillRect(0,0,canvas.clientWidth,canvas.clientHeight);
            rafId = requestAnimationFrame(simpleRender);
          }
          if (!rafId) simpleRender();
          return;
        }
        analyser.fftSize = 2048;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function render(){
          analyser.getByteFrequencyData(dataArray);
          ctx.clearRect(0,0,canvas.clientWidth,canvas.clientHeight);

          let bassEnergy = 0, trebleEnergy = 0;
          const bassCut = Math.floor(bufferLength * 0.15);
          const trebleStart = Math.floor(bufferLength * 0.65);
          for (let i=0;i<bufferLength;i++){
            const v = dataArray[i];
            if (i < bassCut) bassEnergy += v;
            if (i >= trebleStart) trebleEnergy += v;
          }
          bassEnergy = bassEnergy / (bassCut || 1);
          trebleEnergy = trebleEnergy / (bufferLength - trebleStart || 1);

          // background hue shift
          const hue = Math.min(360, Math.max(0, 220 + (trebleEnergy - bassEnergy) * 0.6));
          const lightness = Math.min(60, 30 + (bassEnergy/255) * 25);
          playerRoot.style.background = `linear-gradient(180deg, hsl(${hue} 60% ${lightness}%), rgba(0,0,0,0))`;

          const glow = Math.min(1, bassEnergy/120) * (1 + (Math.abs(parseFloat(playbackRate.value) - 1) * 0.8));
          playerGlow.style.opacity = 0.02 + glow*0.3;

          const intensityFactor = 1 + parseFloat(reverbWet.value) * 1.2 + Math.abs(parseFloat(playbackRate.value)-1) * 1.1;
          draw3DBars(dataArray, intensityFactor);
          drawParticles(dataArray, trebleEnergy, intensityFactor);

          rafId = requestAnimationFrame(render);
        }
        if (!rafId) render();
      }

      function stopVisualLoop(){
        if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      }

      audioEl.addEventListener('play', () => {
        if (!audioCtx) initAudioCtx();
        connectChain();
        startVisualLoop();
      });

      audioEl.addEventListener('pause', () => {
        // keep visuals running for ambient effect
      });

      // initialize
      audioEl.volume = parseFloat(volume.value);
      audioEl.playbackRate = parseFloat(playbackRate.value);
      try { initAudioCtx(); connectChain(); } catch(e) { console.warn("audio init err", e); }
      setTimeout(()=>resizeCanvas(), 200);

      // Expose a small cleanup when parent removes iframe (not always available)
      window.addEventListener('beforeunload', ()=>{
        stopVisualLoop();
        stopRecording();
        if (audioCtx && audioCtx.state !== 'closed') try { audioCtx.close(); } catch(e){}
      });

    })();
    </script>
    '''

    # Insert the logo image into the logo slot. If logo_b64 is empty, keep SP text fallback.
    if logo_b64:
        logo_html = f'<img alt="logo" src="data:image/png;base64,{logo_b64}" />'
    else:
        logo_html = '<div style="font-weight:900; font-size:18px; color:#071018; display:flex; align-items:center; justify-content:center; width:100%; height:100%;">SP</div>'

    if audio_url_data and not audio_url_data.startswith("data:"):
        audio_src = audio_url_data  # Spotify URL (preview)
    else:
        audio_src = audio_url_data or ""
    
    # Replace placeholders
    html = custom_player_template.replace("__AUDIO_SRC__", audio_src)
    html = html.replace("__LOGO_SLOT__", logo_html)

    # Embed the HTML
    st.components.v1.html(html, height=height, scrolling=False)
    # small spacer (keeps streamlit layout stable)
    st.components.v1.html("<div style='height:20px;'></div>", height=20)
