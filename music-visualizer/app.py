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

# ✅ Load logo + favicon
def load_base64(filename: str) -> str:
    path = os.path.join(STATIC_DIR, filename)
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

favicon_b64 = load_base64("favicon.ico")
logo_b64 = load_base64("logo.png")

# ✅ Synthwave video path
synthwave_video_path = os.path.join(STATIC_DIR, "synthwave_bg.mp4")

# ✅ Intro animation
def show_intro():
    favicon_link = f'<link rel="icon" href="data:image/x-icon;base64,{favicon_b64}">' if favicon_b64 else ""
    logo_img = f'<img src="data:image/png;base64,{logo_b64}" class="transparent-logo" width="180">' if logo_b64 else ""
    st.markdown(
        f"""
        {favicon_link}
        <style>
        @keyframes logoIntroAnim {{
          0%   {{ left:0; top:50%; transform: translateY(-50%) scale(0.2) rotate(0deg); opacity:0; }}
          40%  {{ left:50%; top:50%; transform:translate(-50%,-50%) scale(1.0) rotate(180deg); opacity:1; filter:drop-shadow(0 0 25px #ff2d95); }}
          70%  {{ left:50%; top:50%; transform:translate(-50%,-50%) scale(1.2) rotate(360deg); opacity:1; filter:drop-shadow(0 0 40px #ff9a2d); }}
          100% {{ left:0; top:50%; transform:translateY(-50%) scale(0.2) rotate(-360deg); opacity:0; }}
        }}
        #logoIntro {{
          position:fixed; top:50%; left:0;
          animation: logoIntroAnim 4s ease-in-out forwards;
          z-index:10000; background:transparent !important;
        }}
        img.transparent-logo {{ background:transparent !important; display:block; }}
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
# Spotify OAuth helper
# ------------------------
# We will use st.secrets to store Spotify credentials. Example in Streamlit Cloud:
# [spotify]
# SPOTIPY_CLIENT_ID = "..."
# SPOTIPY_CLIENT_SECRET = "..."
# SPOTIPY_REDIRECT_URI = "https://<your-app>.streamlit.app/"

def make_sp_oauth():
    """
    Create a SpotifyOAuth manager using values from st.secrets.
    Returns None if secrets not configured.
    """
    try:
        client_id = st.secrets["spotify"]["083fa034491a43e28929a294097721c5"]
        client_secret = st.secrets["spotify"]["fe82667d7d374f13af99dc18fd4b7ea6"]
        redirect_uri = st.secrets["spotify"]["https://music-visualizer-hxuorbfc6jxffrzaujna37.streamlit.app/"]
    except Exception:
        return None

    # Request basic scopes to read user's library and playlists and profile
    scope = "user-library-read playlist-read-private user-read-private"
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=".spotify_cache"  # use a per-app cache file
    )

sp_oauth = make_sp_oauth()

# ------------------------
# Replace plain title (shows Guest by default — updated to user when logged in)
# ------------------------
logo_img_small = f'<img src="data:image/png;base64,{logo_b64}" width="60" height="60">' if logo_b64 else ""
# We'll later update header text when user is logged in (via session_state).
def render_header():
    user_label = "(Guest)"
    if "spotify_user" in st.session_state and st.session_state.get("spotify_user"):
        user_label = f"Welcome {st.session_state['spotify_user']}"
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:12px;">
          {logo_img_small}
          <div>
            <div style="font-size:20px; font-weight:700;">SonicPlay : Music Visualizer <span style="font-size:12px; color:#9aa0b4; font-weight:500; margin-left:8px;">{user_label}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

render_header()

# ------------------------
# Sidebar - Auth / Guest & Upload
# ------------------------
st.sidebar.header("Welcome")

# Authentication controls
# If Spotify OAuth is configured, show Sign in/out buttons and display status
if sp_oauth:
    # handle redirect back with "code" parameter
    query_params = st.experimental_get_query_params()
    if "code" in query_params and "spotify_auth_in_progress" in st.session_state:
        # exchange code for token
        try:
            code = query_params["code"][0]
            token_info = sp_oauth.get_access_token(code)
            if token_info and "access_token" in token_info:
                access_token = token_info["access_token"]
                # instantiate a Spotipy client with the token
                sp_client = spotipy.Spotify(auth=access_token)
                profile = sp_client.me()
                display_name = profile.get("display_name") or profile.get("id") or "Spotify User"
                st.session_state["spotify_token_info"] = token_info
                st.session_state["spotify_user"] = display_name.split()[0] if isinstance(display_name, str) else display_name
                st.experimental_set_query_params()  # clear query params
                st.experimental_rerun()
        except Exception as e:
            st.sidebar.error(f"Spotify login failed: {e}")

    # Show sign in / sign out buttons and current user
    if "spotify_user" in st.session_state and st.session_state["spotify_user"]:
        st.sidebar.success(f"Signed in as **{st.session_state['spotify_user']}**")
        if st.sidebar.button("Sign out of Spotify"):
            # Clear tokens / session
            st.session_state.pop("spotify_token_info", None)
            st.session_state.pop("spotify_user", None)
            # remove cache file if exists
            try:
                cache_path = sp_oauth.cache_path
                if cache_path and os.path.exists(cache_path):
                    os.remove(cache_path)
            except Exception:
                pass
            st.experimental_rerun()
    else:
        st.sidebar.info("Sign in with Spotify to access your library")
        auth_url = sp_oauth.get_authorize_url()
        # Provide link button that opens Spotify login in a new tab
        st.sidebar.markdown(f"[▶ Sign in with Spotify]({auth_url})", unsafe_allow_html=True)
else:
    st.sidebar.warning("Spotify OAuth not configured (check st.secrets). You can still upload local files.")

# Guest toggle (still available)
if "guest" not in st.session_state:
    if st.sidebar.button("Continue as Guest"):
        st.session_state["guest"] = True

if "guest" in st.session_state:
    st.sidebar.success("Signed in as **Guest**")
else:
    st.sidebar.info("Click **Continue as Guest** to start.")

st.sidebar.markdown("---")

# 🎧 Spotify search / library & upload controls
audio_url_data = None
uploaded = None
beats = []
file_duration = 0.0
processing_error = None

# If logged in via Spotify, create a user-scoped spotipy client
sp_user = None
if "spotify_token_info" in st.session_state:
    try:
        access_token = st.session_state["spotify_token_info"]["access_token"]
        sp_user = spotipy.Spotify(auth=access_token)
    except Exception:
        sp_user = None

# If we have a logged-in user, show their library / playlists + search bar
if sp_user:
    st.sidebar.markdown("### 🎧 Your Spotify Library")
    # Provide a search field at top of the library popup
    lib_query = st.sidebar.text_input("Search in Spotify library (tracks/playlists/artists)", key="lib_search")
    # Show the user's display name at the top
    if "spotify_user" in st.session_state:
        st.sidebar.markdown(f"**{st.session_state['spotify_user']}'s Library**")
    # Fetch user's playlists (first 30) and saved tracks (first 20)
    try:
        if lib_query:
            # search user's library and public Spotify catalog for matches
            results = sp_user.search(q=lib_query, limit=8, type="track,playlist,artist")
            # show tracks first
            tracks = results.get("tracks", {}).get("items", [])
            if tracks:
                st.sidebar.markdown("**Tracks**")
                for idx, t in enumerate(tracks):
                    name = t.get("name")
                    artists = ", ".join([a.get("name") for a in t.get("artists", [])])
                    preview = t.get("preview_url")
                    st.sidebar.write(f"{name} — {artists}")
                    if preview:
                        if st.sidebar.button(f"▶ Play {idx}", key=f"play_search_{idx}"):
                            audio_url_data = preview
                            st.sidebar.success(f"Loaded {name} (preview)")
            # playlists
            playlists = results.get("playlists", {}).get("items", [])
            if playlists:
                st.sidebar.markdown("**Playlists**")
                for pidx, p in enumerate(playlists):
                    pname = p.get("name")
                    owner = p.get("owner", {}).get("display_name") or p.get("owner", {}).get("id")
                    if st.sidebar.button(f"Open: {pname}", key=f"open_pl_{pidx}"):
                        # list first few tracks from playlist
                        pl_id = p.get("id")
                        try:
                            pl_tracks = sp_user.playlist_items(pl_id, fields="items(track(name,artists,preview_url))", limit=12)
                            st.sidebar.markdown(f"**{pname} — {owner}**")
                            for tdx, ti in enumerate(pl_tracks.get("items", [])):
                                tr = ti.get("track", {})
                                tname = tr.get("name")
                                tarts = ", ".join([a.get("name") for a in tr.get("artists", [])])
                                preview = tr.get("preview_url")
                                st.sidebar.write(f"{tname} — {tarts}")
                                if preview:
                                    if st.sidebar.button(f"▶ Play pl_{pidx}_{tdx}", key=f"play_pl_{pidx}_{tdx}"):
                                        audio_url_data = preview
                                        st.sidebar.success(f"Loaded {tname} (preview)")
                        except Exception as e:
                            st.sidebar.error(f"Could not fetch playlist items: {e}")
        else:
            # when no query: show quick saved tracks + playlists
            saved = sp_user.current_user_saved_tracks(limit=8)
            if saved and saved.get("items"):
                st.sidebar.markdown("**Saved Tracks (first 8)**")
                for idx, item in enumerate(saved.get("items", [])):
                    tr = item.get("track", {})
                    name = tr.get("name")
                    artists = ", ".join([a.get("name") for a in tr.get("artists", [])])
                    preview = tr.get("preview_url")
                    st.sidebar.write(f"{name} — {artists}")
                    if preview:
                        if st.sidebar.button(f"▶ Play saved {idx}", key=f"play_saved_{idx}"):
                            audio_url_data = preview
                            st.sidebar.success(f"Loaded {name} (preview)")
            # playlists
            pls = sp_user.current_user_playlists(limit=8)
            if pls and pls.get("items"):
                st.sidebar.markdown("**Your Playlists (first 8)**")
                for pidx, p in enumerate(pls.get("items", [])):
                    pname = p.get("name")
                    if st.sidebar.button(f"Open: {pname}", key=f"open_user_pl_{pidx}"):
                        pl_id = p.get("id")
                        try:
                            pl_tracks = sp_user.playlist_items(pl_id, fields="items(track(name,artists,preview_url))", limit=12)
                            st.sidebar.markdown(f"**{pname}**")
                            for tdx, ti in enumerate(pl_tracks.get("items", [])):
                                tr = ti.get("track", {})
                                tname = tr.get("name")
                                tarts = ", ".join([a.get("name") for a in tr.get("artists", [])])
                                preview = tr.get("preview_url")
                                st.sidebar.write(f"{tname} — {tarts}")
                                if preview:
                                    if st.sidebar.button(f"▶ Play userpl_{pidx}_{tdx}", key=f"play_userpl_{pidx}_{tdx}"):
                                        audio_url_data = preview
                                        st.sidebar.success(f"Loaded {tname} (preview)")
                        except Exception as e:
                            st.sidebar.error(f"Could not fetch playlist items: {e}")
    except Exception as e:
        st.sidebar.error(f"Error fetching Spotify library: {e}")

# If user not logged in or user chose not to use Spotify, show a generic search (non-auth) using a public search if client credentials are available
else:
    # attempt client-credentials search if developer provided client ID/secret in st.secrets but user didn't authenticate
    cc_sp = None
    try:
        # try client credentials manager if configured
        if st.secrets.get("spotify"):
            cid = st.secrets["spotify"].get("083fa034491a43e28929a294097721c5")
            csec = st.secrets["spotify"].get("fe82667d7d374f13af99dc18fd4b7ea6")
            if cid and csec:
                from spotipy.oauth2 import SpotifyClientCredentials
                cc = SpotifyClientCredentials(client_id=cid, client_secret=csec)
                cc_sp = spotipy.Spotify(auth_manager=cc)
    except Exception:
        cc_sp = None

    if cc_sp:
        st.sidebar.markdown("### 🎧 Search Spotify (public)")
        query = st.sidebar.text_input("Search for a song (public preview)", key="public_search")
        if query:
            try:
                results = cc_sp.search(q=query, limit=6, type="track")
                for idx, track in enumerate(results["tracks"]["items"]):
                    track_name = track["name"]
                    artist_name = track["artists"][0]["name"]
                    preview_url = track.get("preview_url")
                    st.sidebar.write(f"{track_name} — {artist_name}")
                    if preview_url:
                        if st.sidebar.button(f"▶ Play {track_name}", key=f"public_play_{idx}"):
                            audio_url_data = preview_url
                            st.sidebar.success(f"Loaded {track_name} (preview)")
            except Exception as e:
                st.sidebar.error(f"Spotify public search error: {e}")

st.sidebar.markdown("### Or upload your own")
uploaded = st.sidebar.file_uploader("Upload MP3/WAV", type=["mp3", "wav", "m4a", "flac"])

# Demo songs
demo_path = Path(os.path.join(BASE_DIR, "demo_songs"))
demo_files = [str(p) for p in demo_path.iterdir() if p.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac"]] if demo_path.exists() else []
if demo_files:
    selected_demo = st.sidebar.selectbox("Or choose demo song", ["-- none --"] + demo_files)
    if selected_demo and selected_demo != "-- none --" and not uploaded and not audio_url_data:
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
    # re-render header so name updates after login state change
    render_header()

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
st.markdown("🎧 **Tip:** Music Might take a while to Load, For the best immersive experience, use headphones!", unsafe_allow_html=True)
st.markdown(
    """<div style="text-align:center; margin-top:20px; font-size:14px; color:#ccc; text-shadow:0px 0px 6px rgba(255,255,255,0.3);">
    Created by <b>Nilam Chakraborty</b></div>""",
    unsafe_allow_html=True,
)
