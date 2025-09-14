# effects/ocean_reverb.py
import json

def get_html(audio_src: str, beats=None):
    """
    Ocean Reverb visualizer (Futuristic neon 3D music player + multi-sine waves + draggable knobs + keyboard shortcuts).
    """
    if beats is None:
        beats = []
    beats_js = json.dumps(beats)

    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>SonicPlay — Ocean Reverb</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.5.0/p5.min.js"></script>
    <style>
      html,body {{ margin:0; padding:0; overflow:hidden; background:#050305; }}
      #sketch {{ width:100%; height:100%; }}
      #hud {{
        position:absolute; left:12px; top:8px; z-index:9999;
        color:#fff; font-family:Inter, Arial, sans-serif; font-size:13px;
        background:rgba(0,0,0,0.35); padding:6px 10px; border-radius:6px;
      }}
      #shortcuts {{
        position:absolute; left:12px; bottom:12px; z-index:9999;
        color:#fff; font-family:Inter, Arial, sans-serif; font-size:13px;
        background:rgba(0,0,0,0.4); padding:6px 10px; border-radius:6px;
        display:none;
      }}
    </style>
  </head>
  <body>
    <div id="sketch"></div>
    <div id="hud">Ocean Reverb : draggable knobs. Click footswitch to bypass.</div>
    <div id="shortcuts">
      <b>Keyboard Shortcuts:</b><br>
      1️⃣ FX LVL → Rewind/Skip<br>
      2️⃣ TIME → Volume<br>
      3️⃣ TONE → Wave Shape<br>
      4️⃣ MODE → Wave Count<br>
      Space → Toggle Bypass
    </div>
    <audio id="audio" controls src="{audio_src}" style="display:none"></audio>

    <script>
      const BEATS = {beats_js};

      let audio=null, audioCtx=null, sourceNode=null, analyser=null;
      let gainNode=null;
      let freqData=null, timeData=null;
      let knobs=[], bypass=false;
      let waveCount=3, shapeFactor=1.0, volume=1.0, hueShift=0;
      let lastBeatPulse=0, glowPulse=0;

      function initAudio(){{
        audio=document.getElementById('audio');
        if(!audio)return;
        if(audioCtx && audioCtx.state!=='closed')return;
        audioCtx=new (window.AudioContext||window.webkitAudioContext)();
        analyser=audioCtx.createAnalyser();
        analyser.fftSize=1024;
        freqData=new Uint8Array(analyser.frequencyBinCount);
        timeData=new Uint8Array(analyser.frequencyBinCount);
        gainNode=audioCtx.createGain();gainNode.gain.value=1.0;
        try{{sourceNode=audioCtx.createMediaElementSource(audio);}}
        catch(e){{console.warn('MediaElementSource issue:',e);}}
        if(sourceNode){{
          sourceNode.connect(gainNode);
          gainNode.connect(analyser);
          analyser.connect(audioCtx.destination);
        }}
      }}

      class Knob {{
        constructor(x,y,label,param){{this.x=x;this.y=y;this.label=label;this.param=param;this.r=30;this.angle=-PI/2;this.min=-5*PI/6;this.max=5*PI/6;this.dragging=false;}}
        draw(){{
          push();translate(this.x,this.y);
          // knob shadow
          noStroke();fill(0,0,0,120);ellipse(4,6,this.r*2.1,this.r*2.1);
          // base gradient
          for(let i=0;i<this.r;i++) {{
            let t=i/this.r;
            stroke(lerpColor(color(250),color(180),t));
            ellipse(0,0,(this.r*2)-i,(this.r*2)-i);
          }}
          // specular highlight
          noStroke();fill(255,200);ellipse(-this.r/3,-this.r/3,8,8);
          // pointer
          stroke(50,200,255);strokeWeight(3);
          line(0,0,cos(this.angle)*this.r*0.7,sin(this.angle)*this.r*0.7);
          // label
          noStroke();fill(255);textAlign(CENTER);textSize(12);text(this.label,0,this.r+18);
          pop();
        }}
        pressed(mx,my){{if(dist(mx,my,this.x,this.y)<this.r+6){{this.dragging=true;if(audioCtx&&audioCtx.state==='suspended')audioCtx.resume();return true;}}return false;}}
        released(){{this.dragging=false;}}
        update(){{if(this.dragging&&!bypass){{this.angle+=(pmouseY-mouseY)*0.01;this.angle=constrain(this.angle,this.min,this.max);this.apply();}}}}
        norm(){{return (this.angle-this.min)/(this.max-this.min);}}
        apply(){{
          let n=this.norm();
          if(this.param==='fx'&&audio){{audio.currentTime=n*audio.duration;}}
          else if(this.param==='time'&&gainNode){{volume=n*2;gainNode.gain.value=volume;}}
          else if(this.param==='tone'){{shapeFactor=0.5+1.5*n;}}
          else if(this.param==='mode'){{waveCount=int(1+n*5);}}
        }}
      }}

      function setup(){{
        const w=Math.max(600,Math.floor(window.innerWidth*0.75));const h=720;
        let c=createCanvas(w,h);c.parent(document.getElementById('sketch'));
        initAudio();
        const cx=width/2;const py=height*0.60;
        // ⬇️ pushed knobs further down so they sit properly inside
        knobs.push(new Knob(cx-80,py-40,'FX LVL','fx'));
        knobs.push(new Knob(cx+80,py-40,'TIME','time'));
        knobs.push(new Knob(cx-80,py+70,'TONE','tone'));
        knobs.push(new Knob(cx+80,py+70,'MODE','mode'));
      }}

      function windowResized(){{resizeCanvas(Math.max(600,Math.floor(window.innerWidth*0.75)),720);}}

      function draw(){{
        background(15);
        if(!audioCtx)initAudio();
        let now=audio?audio.currentTime:millis()/1000.0;
        let beat=false;
        if(BEATS.length>0){{for(let t of BEATS){{if(abs(t-now)<0.07&&millis()-lastBeatPulse>120){{beat=true;lastBeatPulse=millis();}}}}}}
        analyser&&analyser.getByteFrequencyData(freqData);
        hueShift=(hueShift+0.5)%360;
        if(beat) glowPulse=20;
        glowPulse=max(0,glowPulse-1);
        drawWaves(beat);
        drawPedal(glowPulse);
        knobs.forEach(k=>{{k.update();k.draw();}});
      }}

      function drawWaves(beat){{
        push();translate(width*0.1,height*0.18);
        let w=width*0.8,h=height*0.18;
        noFill();
        for(let i=0;i<waveCount;i++){{
          let hue=(hueShift+i*60)%360;
          stroke(hue,80,100,220);
          strokeWeight(2+(beat?2:0));
          beginShape();
          for(let x=0;x<=w;x+=6){{
            let t=x/w*PI*4;
            let y=h/2+sin(t*shapeFactor+i)*h*0.4*sin(frameCount*0.01+i);
            vertex(x,y+(beat?random(-4,4):0));
          }}
          endShape();
        }}
        pop();
      }}

      function drawPedal(glow){{
        let w=280,h=360,x=width/2-w/2,y=height*0.50;
        push();
        // drop shadow
        noStroke();fill(0,0,0,150);rect(x+12,y+18,w,h,22);
        // radial gradient body
        for(let i=0;i<h;i++){{
          let t=i/h;
          stroke(lerpColor(color(20,20,25),color(40,40,45),t));
          line(x,y+i,x+w,y+i);
        }}
        // neon inner glow
        if(glow>0){{
          noStroke();
          fill(0,255,255,80);
          ellipse(x+w/2,y+h/2,w*0.8+glow,h*0.6+glow);
        }}
        // glossy reflection strip
        noStroke();fill(255,40);rect(x+10,y+8,w-20,12,6);
        // neon border
        noFill();stroke(0,255,255);strokeWeight(3);rect(x,y,w,h,22);
        // logo
        fill(0,255,255);noStroke();textAlign(CENTER);
        textSize(20);text('OCEANS',x+w/2,y+36);
        textSize(14);text('REVERB',x+w/2,y+58);
        // footswitch metallic
        let fx=x+w/2,fy=y+h-46;
        stroke(180);strokeWeight(2);fill(60);ellipse(fx,fy,54);
        fill(bypass?color(0,255,120):color(0,255,255));
        noStroke();ellipse(fx,fy-32,14);
        fill(255);textSize(13);text(bypass?'BYPASS':'ON',fx,fy+28);
        pop();
      }}

      function mousePressed(){{if(audioCtx&&audioCtx.state==='suspended')audioCtx.resume();else initAudio();let used=false;for(let k of knobs)if(k.pressed(mouseX,mouseY))used=true;let w=280,h=360,x=width/2-w/2,y=height*0.50;if(!used&&dist(mouseX,mouseY,x+w/2,y+h-46)<30)toggleBypass();}}
      function mouseReleased(){{knobs.forEach(k=>k.released());}}

      function toggleBypass(){{bypass=!bypass;if(bypass&&gainNode)gainNode.gain.value=1.0;if(bypass&&audio)audio.playbackRate=1.0;}}

      function keyPressed(){{
        if(key===' ')toggleBypass();
        else if(key==='1')knobs[0].apply();
        else if(key==='2')knobs[1].apply();
        else if(key==='3')knobs[2].apply();
        else if(key==='4')knobs[3].apply();
        document.getElementById('shortcuts').style.display='block';
      }}
    </script>
  </body>
</html>
"""