import streamlit as st
import librosa
import numpy as np
import base64
import tempfile
import os
from pathlib import Path
import requests

# ------------------------
# Page config + Logo / Favicon
# ------------------------
st.set_page_config(page_title="SonicPlay - Music Visualizer", layout="wide")

# Resolve project static directory relative to this file
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")


# ✅ Load logo + favicon (safe: returns empty string on failure)
def load_base64(filename: str) -> str:
    path = os.path.join(STATIC_DIR, filename)
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
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

# ------------------------
# Replace plain title (dynamic)
# ------------------------
logo_img_small = f'<img src="data:image/png;base64,{logo_b64}" width="60" height="60">' if logo_b64 else ""
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:12px;">
      {logo_img_small}
      <h1 style="margin:0;">SonicPlay : Music Visualizer</h1>
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

# ------------------------
# JioSaavn search (saavn.dev API)
# ------------------------
@st.cache_data(ttl=300)
def saavn_search(query: str, n: int = 10):
    """Search JioSaavn songs via saavn.dev API."""
    url = f"https://saavn.dev/api/search/songs?query={query}&limit={n}"
    resp = requests.get(url, timeout=10)
    data = resp.json()
    if not data.get("success"):
        return []
    return data["data"]["results"]

# ------------------------
# Audio state
# ------------------------
audio_url_data = st.session_state.get("audio_url_data", None)
uploaded = None
beats = []
file_duration = 0.0
processing_error = None

# ------------------------
# JioSaavn Integration
# ------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎧 Search JioSaavn")
search_query = st.sidebar.text_input("Search for a song")

if search_query:
    try:
        results = saavn_search(search_query, n=10)
        for idx, song in enumerate(results):
            title = song.get("name")
            artists = ", ".join(a["name"] for a in song["artists"]["primary"]) if song.get("artists") else "Unknown"
            album = song.get("album", {}).get("name", "")
            downloads = song.get("downloadUrl", [])
            media_url = downloads[0]["url"] if downloads else None

            st.sidebar.write(f"🎵 {title} — {artists} ({album})")
            if media_url:
                if st.sidebar.button("▶ Load", key=f"saavn_{idx}"):
                    st.session_state["audio_url_data"] = media_url
                    st.session_state["now_playing"] = f"{title} — {artists}"
                    audio_url_data = media_url
                    st.sidebar.success(f"Loaded {title}")
    except Exception as e:
        st.sidebar.error(f"JioSaavn error: {e}")

# ------------------------
# Upload / Demo fallback
# ------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### Or upload your own")
uploaded = st.sidebar.file_uploader("Upload MP3/WAV", type=["mp3", "wav", "m4a", "flac"])

demo_path = Path(os.path.join(BASE_DIR, "demo_songs"))
demo_files = []
if demo_path.exists() and demo_path.is_dir():
    for p in demo_path.iterdir():
        if p.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac"]:
            demo_files.append(str(p))

selected_demo = None
if demo_files:
    demo_names = [Path(f).name for f in demo_files]
    selected_demo = st.sidebar.selectbox("Or choose demo song", ["-- none --"] + demo_names)

    if selected_demo and selected_demo != "-- none --":
        demo_path_selected = next(f for f in demo_files if Path(f).name == selected_demo)
        with open(demo_path_selected, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            mime = "audio/mpeg" if Path(demo_path_selected).suffix.lower() != ".wav" else "audio/wav"
            st.session_state["audio_url_data"] = f"data:{mime};base64,{b64}"
            st.session_state["now_playing"] = Path(demo_path_selected).name

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
# Helper to write uploaded file to temp
# ------------------------
def write_temp_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix if hasattr(uploaded_file, "name") else ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.read())
    tmp.flush()
    tmp.close()
    return tmp.name


# ------------------------
# Process uploaded audio
# ------------------------
if uploaded and not st.session_state.get("audio_url_data", None):
    try:
        temp_path = write_temp_file(uploaded)
        y, sr = librosa.load(temp_path, sr=None, mono=True)
        file_duration = librosa.get_duration(y=y, sr=sr)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, trim=False)
        beats = librosa.frames_to_time(beat_frames, sr=sr).tolist()

        with open(temp_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            mime = "audio/mpeg" if Path(temp_path).suffix.lower() != ".wav" else "audio/wav"
            st.session_state["audio_url_data"] = f"data:{mime};base64,{b64}"
            st.session_state["now_playing"] = uploaded.name if hasattr(uploaded, "name") else Path(temp_path).name

        st.sidebar.success(f"Detected ~{len(beats)} beats, duration {int(file_duration)}s")
    except Exception as e:
        processing_error = str(e)
        st.sidebar.error(f"Could not analyze audio: {e}")

# ------------------------
# Main UI - Player + Visualizer
# ------------------------
from effects import ripple, synthwave, ocean_reverb, resonance, mesh, beatsaber

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Player")
    current_audio = st.session_state.get("audio_url_data", None)
    now_playing_label = st.session_state.get("now_playing", None)

    if now_playing_label:
        st.markdown(f"**Now Playing:** {now_playing_label}")

    if current_audio:
        try:
            from custom_player import render_custom_player
            render_custom_player(current_audio, logo_b64=logo_b64)
        except Exception as e:
            st.error(f"Could not load custom player: {e}")
            st.audio(current_audio)
    else:
        st.info("Upload or load a song to enable the player.")

    start_clicked = st.button("▶️ Start Visualizer")
    replay_intro = st.button("🔄 Replay Intro")

with col2:
    st.header("Visualizer")
    if replay_intro:
        show_intro()
    elif start_clicked and st.session_state.get("audio_url_data", None):
        audio_for_visual = st.session_state["audio_url_data"]
        if mode == "Ripple":
            html = ripple.render_effect(beats, theme, sensitivity, particle_count, audio_for_visual)
            st.components.v1.html(html, height=680, scrolling=False)
        elif mode == "Synthwave":
            video_path = synthwave_video_path if os.path.exists(synthwave_video_path) else os.path.join("static", "synthwave_bg.mp4")
            html = synthwave.get_html(audio_src=audio_for_visual, beats=beats, intensity=intensity, grid_speed=grid_speed, grid_cols=grid_cols, video_path=video_path)
            st.components.v1.html(html, height=700, scrolling=False)
        elif mode == "Ocean Reverb":
            html = ocean_reverb.get_html(audio_for_visual, beats=beats)
            st.components.v1.html(html, height=700, scrolling=False)
        elif mode == "Resonance":
            html = resonance.get_html(audio_for_visual, beats=beats)
            st.components.v1.html(html, height=720, scrolling=False)
        elif mode == "Mesh":
            html = mesh.get_html(audio_for_visual, beats=beats)
            st.components.v1.html(html, height=720, scrolling=False)
        elif mode == "BeatSaber":
            html = beatsaber.get_html(audio_for_visual, beats=beats)
            st.components.v1.html(html, height=720, scrolling=False)
        elif mode == "Custom Player":
            st.write("🎚 Custom Player is displayed on the left. Use its controls to play, tweak effects, and save presets.")

st.markdown("---")
st.markdown("🎧 **Tip:** For the best immersive experience, use headphones! Song might take some time to load, be patient.", unsafe_allow_html=True)
st.markdown(
    """<div style="text-align:center; margin-top:20px; font-size:14px; color:#ccc; text-shadow:0px 0px 6px rgba(255,255,255,0.3);">
    Created by <b>Nilam Chakraborty</b></div>""",
    unsafe_allow_html=True,
)