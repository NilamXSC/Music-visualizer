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


# ------------------------
# Spotify OAuth flow handling (in-app)
# ------------------------
SPOTIPY_CLIENT_ID = "083fa034491a43e28929a294097721c5"
SPOTIPY_CLIENT_SECRET = "fe82667d7d374f13af99dc18fd4b7ea6"
SPOTIPY_REDIRECT_URI = "https://music-visualizer-hxuorbfc6jxffrzaujna37.streamlit.app/"

SPOTIFY_SCOPE = "user-library-read user-read-private"

auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    cache_path=".spotify_token_cache",
)

spotify_token_info = st.session_state.get("spotify_token_info", None)
sp = None
spotify_user_display = None

# ✅ FIX: Only use st.query_params (new API)
params = st.query_params
if "code" in params and not spotify_token_info:
    code = params["code"]
    try:
        token_info = auth_manager.get_access_token(code)
        spotify_token_info = token_info
        st.session_state["spotify_token_info"] = spotify_token_info
        # clear ?code= from URL
        st.query_params.clear()
    except Exception as e:
        st.sidebar.error(f"Spotify auth failed: {e}")
        spotify_token_info = None
        if "spotify_token_info" in st.session_state:
            del st.session_state["spotify_token_info"]

if spotify_token_info:
    access_token = spotify_token_info.get("access_token") if isinstance(spotify_token_info, dict) else spotify_token_info
    try:
        sp = spotipy.Spotify(auth=access_token)
        profile = sp.me()
        spotify_user_display = profile.get("display_name") or profile.get("id")
    except Exception:
        try:
            refresh_token = spotify_token_info.get("refresh_token") if isinstance(spotify_token_info, dict) else None
            if refresh_token:
                new_token = auth_manager.refresh_access_token(refresh_token)
                st.session_state["spotify_token_info"] = new_token
                access_token = new_token.get("access_token")
                sp = spotipy.Spotify(auth=access_token)
                profile = sp.me()
                spotify_user_display = profile.get("display_name") or profile.get("id")
        except Exception:
            sp = None
            spotify_user_display = None

# ------------------------
# Show header
# ------------------------
user_label = f"Welcome {spotify_user_display}" if spotify_user_display else "(Guest)"
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:12px;">
      {logo_img_small}
      <h1 style="margin:0;">SonicPlay : Music Visualizer <span style="font-size:14px; color:#aaa;">{user_label}</span></h1>
    </div>
    """,
    unsafe_allow_html=True,
)

if not sp:
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Spotify")
    st.sidebar.write("Sign in with Spotify to browse your library and play previews.")
    auth_url = auth_manager.get_authorize_url()
    st.sidebar.markdown(
        f'<a href="{auth_url}" target="_blank"><button style="padding:8px 12px; border-radius:8px;">Login with Spotify</button></a>',
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
# Spotify library (scrollable, hoverable cards)
# ------------------------
# Always pull from session_state
audio_url_data = st.session_state.get("audio_url_data", None)
uploaded = None
beats = []
file_duration = 0.0
processing_error = None

if sp:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎧 Spotify Library")

    try:
        search_query = st.sidebar.text_input("Search Spotify")
        if search_query:
            res = sp.search(q=search_query, limit=20, type="track")
            items = res.get("tracks", {}).get("items", [])
        else:
            saved = sp.current_user_saved_tracks(limit=20)
            items = [s["track"] for s in saved.get("items", [])]

        # scrollable container
        st.sidebar.markdown(
            """
            <style>
            .scroll-box {
                max-height: 260px;
                overflow-y: auto;
                padding-right: 8px;
            }
            .track-card {
                padding: 6px;
                margin-bottom: 6px;
                border-radius: 6px;
                transition: background 0.2s;
            }
            .track-card:hover {
                background: rgba(255,255,255,0.08);
                cursor: pointer;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        with st.sidebar:
            st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
            for idx, track in enumerate(items):
                name = track.get("name")
                artists = ", ".join([a["name"] for a in track.get("artists", [])])
                preview_url = track.get("preview_url")

                st.markdown(
                    f'<div class="track-card">🎵 <b>{name}</b><br><span style="font-size:12px; color:#aaa;">{artists}</span></div>',
                    unsafe_allow_html=True,
                )
                if preview_url:
                    if st.button("▶ Load", key=f"sp_play_{idx}"):
                        # store preview and now playing into session state so player re-renders reliably
                        st.session_state["audio_url_data"] = preview_url
                        st.session_state["now_playing"] = f"{name} — {artists}"
                        st.sidebar.success(f"Loaded {name}")
                        st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.sidebar.warning("Could not fetch library.")
        st.sidebar.info(str(e))

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
            demo_files.append(p)

selected_demo = None
if demo_files:
    demo_labels = ["-- none --"] + [p.name for p in demo_files]  # show only file names
    selected_label = st.sidebar.selectbox("Or choose demo song", demo_labels)

    if selected_label != "-- none --":
        selected_demo = str(demo_path / selected_label)
        if not uploaded and not audio_url_data:
            uploaded = open(selected_demo, "rb")
            st.session_state["now_playing"] = selected_label  # set "Now Playing"
    if selected_demo and selected_demo != "-- none --" and not uploaded and not audio_url_data:
        uploaded = open(selected_demo, "rb")
        # set now playing label for demo selection
        st.session_state["now_playing"] = Path(selected_demo).name

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
            st.session_state["audio_url_data"] = audio_url_data
            # set now_playing from uploaded file name when available
            try:
                name_label = uploaded.name if hasattr(uploaded, "name") else Path(temp_path).name
            except Exception:
                name_label = Path(temp_path).name
            st.session_state["now_playing"] = name_label

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
    # always pull the current audio and now_playing label from session state so clicks update the player
    current_audio = st.session_state.get("audio_url_data", None)
    now_playing_label = st.session_state.get("now_playing", None)

    if now_playing_label:
        st.markdown(f"**Now Playing:** {now_playing_label}")

    if current_audio:
        try:
            from custom_player import render_custom_player
            if current_audio.startswith("https://p.scdn.co"):
                render_custom_player(current_audio, logo_b64=logo_b64)
            else:
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
