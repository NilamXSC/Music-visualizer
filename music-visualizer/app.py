import streamlit as st
import librosa
import numpy as np
import base64
import tempfile
import os
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ------------------------
# Page config + Logo / Favicon
# ------------------------
st.set_page_config(page_title="SonicPlay - Music Visualizer", layout="wide")

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

def load_base64(filename: str) -> str:
    path = os.path.join(STATIC_DIR, filename)
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

favicon_b64 = load_base64("favicon.ico")
logo_b64 = load_base64("logo.png")

synthwave_video_path = os.path.join(STATIC_DIR, "synthwave_bg.mp4")

def show_intro():
    favicon_link = f'<link rel="icon" href="data:image/x-icon;base64,{favicon_b64}">' if favicon_b64 else ""
    logo_img = f'<img src="data:image/png;base64,{logo_b64}" width="180">' if logo_b64 else ""
    st.markdown(
        f"""
        {favicon_link}
        <style>
        @keyframes logoIntroAnim {{
          0%   {{ left:0; top:50%; transform:translateY(-50%) scale(0.2) rotate(0deg); opacity:0; }}
          40%  {{ left:50%; top:50%; transform:translate(-50%,-50%) scale(1.0) rotate(180deg); opacity:1; filter:drop-shadow(0 0 25px #ff2d95); }}
          70%  {{ left:50%; top:50%; transform:translate(-50%,-50%) scale(1.2) rotate(360deg); opacity:1; filter:drop-shadow(0 0 40px #ff9a2d); }}
          100% {{ left:0; top:50%; transform:translateY(-50%) scale(0.2) rotate(-360deg); opacity:0; }}
        }}
        #logoIntro {{
          position:fixed; top:50%; left:0;
          animation: logoIntroAnim 4s ease-in-out forwards;
          z-index:10000; background:transparent !important;
        }}
        </style>
        <div id="logoIntro">{logo_img}</div>
        """,
        unsafe_allow_html=True,
    )

show_intro()

# ------------------------
# Spotify Integration (hardcoded creds)
# ------------------------
SPOTIPY_CLIENT_ID = "083fa034491a43e28929a294097721c5"
SPOTIPY_CLIENT_SECRET = "fe82667d7d374f13af99dc18fd4b7ea6"
SPOTIPY_REDIRECT_URI = "https://music-visualizer-hxuorbfc6jxffrzaujna37.streamlit.app/"

sp = None
spotify_user = None
try:
    auth_manager = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-library-read user-read-private"
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    profile = sp.me()
    spotify_user = profile.get("display_name", "Spotify User")
except Exception as e:
    st.sidebar.warning("⚠ Spotify not configured. Upload local files instead.")

# ------------------------
# Replace title (dynamic)
# ------------------------
logo_img_small = f'<img src="data:image/png;base64,{logo_b64}" width="60" height="60">' if logo_b64 else ""
user_label = f"Welcome {spotify_user}" if spotify_user else "(Guest)"
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:12px;">
      {logo_img_small}
      <h1 style="margin:0;">SonicPlay : Music Visualizer <span style="font-size:14px; color:#aaa;">{user_label}</span></h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------
# Sidebar - Upload / Spotify search
# ------------------------
st.sidebar.header("Welcome")

audio_url_data = None
uploaded = None
beats = []
file_duration = 0.0
processing_error = None

if sp:
    st.sidebar.markdown("### 🎧 Search Spotify")
    query = st.sidebar.text_input("Search for a song")
    if query:
        results = sp.search(q=query, limit=5, type="track")
        for idx, track in enumerate(results["tracks"]["items"]):
            track_name = track["name"]
            artist_name = track["artists"][0]["name"]
            preview_url = track["preview_url"]
            st.sidebar.write(f"{track_name} — {artist_name}")
            if preview_url and st.sidebar.button(f"▶ Play {track_name}", key=f"play_sp_{idx}"):
                audio_url_data = preview_url
                st.sidebar.success(f"Loaded {track_name} from Spotify")

st.sidebar.markdown("### Or upload your own")
uploaded = st.sidebar.file_uploader("Upload MP3/WAV", type=["mp3", "wav", "m4a", "flac"])

demo_path = Path(os.path.join(BASE_DIR, "demo_songs"))
demo_files = [str(p) for p in demo_path.iterdir() if p.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac"]] if demo_path.exists() else []
if demo_files:
    selected_demo = st.sidebar.selectbox("Or choose demo song", ["-- none --"] + demo_files)
    if selected_demo and selected_demo != "-- none --" and not uploaded and not audio_url_data:
        uploaded = open(selected_demo, "rb")

st.sidebar.markdown("---")
st.sidebar.markdown("### Visual settings")
mode = st.sidebar.selectbox("Visualizer Mode", ["Ripple", "Synthwave", "Ocean Reverb", "Resonance", "Mesh", "BeatSaber", "Custom Player"])
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
# Process uploaded audio
# ------------------------
if uploaded and not audio_url_data:
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
            audio_url_data = f"data:{mime};base64,{b64}"

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
    if audio_url_data:
        try:
            from custom_player import render_custom_player
            render_custom_player(audio_url_data, logo_b64=logo_b64)
        except Exception as e:
            st.error(f"Could not load custom player: {e}")
            st.audio(audio_url_data)
    else:
        st.info("Upload or load a song to enable the player.")

    start_clicked = st.button("▶️ Start Visualizer")
    replay_intro = st.button("🔄 Replay Intro")

with col2:
    st.header("Visualizer")
    if replay_intro:
        show_intro()
    elif start_clicked and audio_url_data:
        if mode == "Ripple":
            html = ripple.render_effect(beats, theme, sensitivity, particle_count, audio_url_data)
            st.components.v1.html(html, height=680, scrolling=False)
        elif mode == "Synthwave":
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
st.markdown("🎧 **Tip:** Music will take some time to load. For the best immersive experience, use headphones!", unsafe_allow_html=True)
st.markdown(
    """<div style="text-align:center; margin-top:20px; font-size:14px; color:#ccc; text-shadow:0px 0px 6px rgba(255,255,255,0.3);">
    Created by <b>Nilam Chakraborty</b></div>""",
    unsafe_allow_html=True,
)
