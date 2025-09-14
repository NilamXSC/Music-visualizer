import streamlit as st
import librosa
import numpy as np
import base64
import tempfile
import os
from pathlib import Path

# Import visualizer effects
from effects import ripple, synthwave, ocean_reverb, resonance, mesh, beatsaber

# ------------------------
# Page config + Logo / Favicon
# ------------------------
st.set_page_config(page_title="SonicPlay - Music Visualizer", layout="wide")

# Resolve project static directory relative to this file (robust for deploy)
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ✅ Load logo + favicon as base64 (safe: uses absolute paths)
def load_base64(filename: str) -> str:
    """
    Load a file from the static directory and return a base64 data string.
    Returns an empty string on failure (so app doesn't crash on missing files).
    """
    path = os.path.join(STATIC_DIR, filename)
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        # Don't raise here because missing static files should not break the app
        return ""

favicon_b64 = load_base64("favicon.ico")
logo_b64 = load_base64("logo.png")

# ✅ Synthwave video path (absolute)
synthwave_video_path = os.path.join(STATIC_DIR, "synthwave_bg.mp4")

# ✅ Intro animation (only inject favicon if available)
def show_intro():
    favicon_link = f'<link rel="icon" href="data:image/x-icon;base64,{favicon_b64}">' if favicon_b64 else ""
    logo_img = f'<img src="data:image/png;base64,{logo_b64}" class="transparent-logo" width="180">' if logo_b64 else ""
    st.markdown(
        f"""
        {favicon_link}
        <style>
        @keyframes logoIntroAnim {{
          0%   {{ left:0; top:50%; transform: translateY(-50%) scale(0.2) rotate(0deg); opacity:0; }}
          40%  {{ left:50%; top:50%; transform: translate(-50%,-50%) scale(1.0) rotate(180deg); opacity:1; filter: drop-shadow(0 0 25px #ff2d95); }}
          70%  {{ left:50%; top:50%; transform: translate(-50%,-50%) scale(1.2) rotate(360deg); opacity:1; filter: drop-shadow(0 0 40px #ff9a2d); }}
          100% {{ left:0; top:50%; transform: translateY(-50%) scale(0.2) rotate(-360deg); opacity:0; }}
        }}
        #logoIntro {{
          position:fixed;
          top:50%;
          left:0;
          animation: logoIntroAnim 4s ease-in-out forwards;
          z-index:10000;
          background: transparent !important;
        }}
        img.transparent-logo {{
          background: transparent !important;
          display:block;
        }}
        </style>
        <div id="logoIntro">
          {logo_img}
        </div>
        """,
        unsafe_allow_html=True,
    )

# Show intro on load
show_intro()

# ✅ Replace plain title with logo + text (fallback to text if logo missing)
logo_img_small = f'<img src="data:image/png;base64,{logo_b64}" width="60" height="60">' if logo_b64 else ""
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:12px;">
      {logo_img_small}
      <h1 style="margin:0;">SonicPlay : Music Visualizer (Guest)</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------
# Sidebar - Guest & Upload
# ------------------------
st.sidebar.header("Welcome")
if "guest" not in st.session_state:
    if st.sidebar.button("Continue as Guest"):
        st.session_state["guest"] = True

if "guest" in st.session_state:
    st.sidebar.success("Signed in as **Guest**")
else:
    st.sidebar.info("Click **Continue as Guest** to start.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Choose audio")
uploaded = st.sidebar.file_uploader(
    "Upload an MP3 / WAV file (or choose demo)", type=["mp3", "wav", "m4a", "flac"]
)

# Offer demo file if user added one to demo_songs folder (resolve relative to BASE_DIR)
demo_path = Path(os.path.join(BASE_DIR, "demo_songs"))
demo_files = []
if demo_path.exists() and demo_path.is_dir():
    for p in demo_path.iterdir():
        if p.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac"]:
            demo_files.append(str(p))

selected_demo = None
if demo_files:
    selected_demo = st.sidebar.selectbox("Or choose demo song", ["-- none --"] + demo_files)
    if selected_demo and selected_demo != "-- none --" and not uploaded:
        # open as binary file-like so downstream code works the same
        uploaded = open(selected_demo, "rb")

st.sidebar.markdown("---")
st.sidebar.markdown("### Visual settings")
mode = st.sidebar.selectbox(
    "Visualizer Mode",
    ["Ripple", "Synthwave", "Ocean Reverb", "Resonance", "Mesh", "BeatSaber", "Custom Player"],
)
sensitivity = st.sidebar.slider("Beat sensitivity", 0.3, 2.5, 1.0, step=0.1)
theme = st.sidebar.selectbox("Theme", ["Neon (dark)", "Light", "Blue", "Cyberpunk", "Vaporwave", "Galaxy"])
particle_count = st.sidebar.slider("Background particle count", 20, 120, 55, step=5)

if mode == "Synthwave":
    intensity = st.sidebar.slider("Synthwave Intensity", 0.5, 3.0, 1.0, step=0.1)
    grid_speed = st.sidebar.slider("Synthwave Grid Speed", 0.1, 2.0, 0.6, step=0.1)
    grid_cols = st.sidebar.slider("Synthwave Grid Columns", 12, 60, 36, step=2)

# ------------------------
# Helper
# ------------------------
def write_temp_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix if hasattr(uploaded_file, "name") else ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.read())
    tmp.flush()
    tmp.close()
    return tmp.name

# ------------------------
# Process audio
# ------------------------
beats = []
audio_url_data = None
processing_error = None
file_duration = 0.0

if uploaded:
    try:
        temp_path = write_temp_file(uploaded)
        # load with librosa
        y, sr = librosa.load(temp_path, sr=None, mono=True)
        file_duration = librosa.get_duration(y=y, sr=sr)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, trim=False)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        beats = beat_times.tolist()

        with open(temp_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            mime = "audio/mpeg"
            if Path(temp_path).suffix.lower() == ".wav":
                mime = "audio/wav"
            audio_url_data = f"data:{mime};base64,{b64}"

        st.sidebar.success(f"Detected ~{len(beats)} beats, duration {int(file_duration)}s")
    except Exception as e:
        processing_error = str(e)
        st.sidebar.error(f"Could not analyze audio: {e}")

# ------------------------
# Main UI - Player + Visualizer
# ------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Player")
    if uploaded and audio_url_data:
        # Import the custom player render function here (keeps import errors local)
        try:
            from custom_player import render_custom_player  # type: ignore
            # render with optional logo data if available
            render_custom_player(audio_url_data, logo_b64=logo_b64)
        except Exception as e:
            st.error(f"Could not load custom player: {e}")
            st.write("Fallback basic audio player:")
            st.audio(audio_url_data)
    else:
        st.info("Upload an audio file (mp3/wav) in the sidebar to enable the player.")

    start_clicked = st.button("▶️ Start Visualizer")
    replay_intro = st.button("🔄 Replay Intro")

with col2:
    st.header("Visualizer")
    if replay_intro:
        show_intro()
    elif start_clicked and uploaded and audio_url_data:
        if mode == "Ripple":
            html = ripple.render_effect(beats, theme, sensitivity, particle_count, audio_url_data)
            st.components.v1.html(html, height=680, scrolling=False)
        elif mode == "Synthwave":
            # ensure synthwave video path exists; pass relative fallback if not
            video_path = synthwave_video_path if os.path.exists(synthwave_video_path) else os.path.join("static", "synthwave_bg.mp4")
            html = synthwave.get_html(audio_src=audio_url_data, beats=beats, intensity=intensity, grid_speed=grid_speed, grid_cols=grid_cols, video_path=video_path)
            st.components.v1.html(html, height=700, scrolling=False)
        elif mode == "Ocean Reverb":
            html = ocean_reverb.get_html(audio_url_data, beats=beats)
            st.components.v1.html(html, height=700, scrolling=False)
        elif mode == "Resonance":
            html = resonance.get_html(audio_url_data, beats=beats)
            st.components.v1.html(html, height=720, scrolling=False)
        elif mode == "Mesh":
            html = mesh.get_html(audio_url_data, beats=beats)
            st.components.v1.html(html, height=720, scrolling=False)
        elif mode == "BeatSaber":
            html = beatsaber.get_html(audio_url_data, beats=beats)
            st.components.v1.html(html, height=720, scrolling=False)
        elif mode == "Custom Player":
            st.write("🎚 Custom Player is displayed on the left. Use its controls to play, tweak effects, and save presets.")

st.markdown("---")
st.markdown("🎧 **Tip:** For the best immersive experience, use headphones!", unsafe_allow_html=True)
st.markdown(
    """<div style="text-align:center; margin-top:20px; font-size:14px; color:#ccc; text-shadow:0px 0px 6px rgba(255,255,255,0.3);">
    Created by <b>Nilam Chakraborty</b></div>""",
    unsafe_allow_html=True,
)