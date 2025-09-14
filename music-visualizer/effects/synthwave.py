import json, base64, os

def get_html(audio_src: str, beats=None, intensity=1.0, grid_speed=0.6, grid_cols=36,
             video_path="static/synthwave_bg.mp4"):
    """
    Synthwave visualizer with looping video background and interactive neon ray trails.
    Video is embedded as base64 so it always loads inside Streamlit iframe.
    """
    if beats is None:
        beats = []
    beats_js = json.dumps(beats)

    # 🔹 Read and encode video as base64
    video_b64 = ""
    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode("utf-8")
    video_url = f"data:video/mp4;base64,{video_b64}" if video_b64 else ""

    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>SonicPlay — Synthwave</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.5.0/p5.min.js"></script>
    <style>
      html,body {{
        margin:0; padding:0; overflow:hidden; background:#000;
        width:100%; height:100%;
      }}
      #bg {{
        position:absolute;
        top:0; left:0;
        width:100%; height:100%;
        object-fit:cover;
        z-index:0;
      }}
      #sketch {{
        position:absolute;
        top:0; left:0;
        width:100%; height:100%;
        z-index:1;
        pointer-events:none;
      }}
      #hud {{
        position:absolute; left:12px; top:8px; z-index:2;
        color:#fff; font-family:Inter, Arial, sans-serif; font-size:13px;
        background:rgba(0,0,0,0.35); padding:6px 10px; border-radius:6px;
      }}
    </style>
  </head>
  <body>
    <!-- 🔹 Base64 video background -->
    <video id="bg" autoplay loop muted playsinline>
      <source src="{video_url}" type="video/mp4">
    </video>

    <!-- 🔹 Overlay for p5 canvas -->
    <div id="sketch"></div>
    <div id="hud">Synthwave : Drag to draw neon sunray trails ☀️</div>
    <audio id="audio" controls src="{audio_src}" style="display:none"></audio>

    <script>
      const BEATS = {beats_js};
      let rays = [];

      function setup() {{
        let c = createCanvas(window.innerWidth, window.innerHeight);
        c.parent(document.getElementById('sketch'));
        colorMode(HSB,360,100,100,255);
        noFill();
        strokeCap(ROUND);
      }}

      function windowResized() {{
        resizeCanvas(window.innerWidth, window.innerHeight);
      }}

      function draw() {{
        clear(); // keep video visible underneath

        // animate rays
        for (let i=rays.length-1;i>=0;i--) {{
          let r = rays[i];
          stroke(r.hue,90,100,r.alpha);
          strokeWeight(r.w);
          line(r.x, r.y, r.x + cos(r.angle)*r.len, r.y + sin(r.angle)*r.len);

          // update
          r.len += 2;
          r.alpha -= 3;
          if (r.alpha<=0) rays.splice(i,1);
        }}
      }}

      function mouseDragged() {{
        let angle = atan2(mouseY-height/2, mouseX-width/2);
        rays.push({{
          x:mouseX, y:mouseY,
          angle:angle,
          len:20,
          hue:(frameCount*2)%360,
          w:2.5,
          alpha:200
        }});
      }}
    </script>
  </body>
</html>
"""