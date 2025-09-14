🎶 SonicPlay — Interactive Music Visualizer

SonicPlay is a fully interactive music visualization platform built with Python (Streamlit) and Web Audio APIs. It blends audio analysis, cyberpunk-inspired UI, and immersive real-time graphics to deliver a next-generation music player and visualizer.

Whether you want to simply enjoy music with reactive visuals or experiment with audio effects like bass boost, reverb, pitch shift, DJ filters, and custom presets, SonicPlay turns every track into a visual and auditory performance.

✨ Features

🎧 Custom Cyberpunk Player

Play, pause, seek, record, and download recordings

Advanced controls: Bass, Treble, Pan, Reverb, Delay, Pitch Shift, DJ Sweep, Distortion

Save, load, and delete custom presets locally

🌌 Dynamic Visualizer Modes

Ripple

Synthwave Grid (with animated background)

Ocean Reverb

Resonance

Mesh

BeatSaber

Custom Cyber Player with 3D Spectrum + Particle Sync

🖼️ Custom Themes

Neon (Dark)

Cyberpunk

Vaporwave

Galaxy

Light & Blue variants

Vibrant mode: animated rainbow accents

⚡ Real-Time Audio Effects

Live FFT-based 3D spectrum analyzer

Particle sync with treble & bass frequencies

Impulse-response reverb engine

WebAudio API powered sound filters

🎨 Modern UI/UX

Animated intro logo sequence

Smooth glowing borders & cyberpunk style buttons

Streamlit integration with responsive layout

Favicon, branding logo, and fully themed dropdowns

🛠️ Tech Stack

Frontend / UI:

Streamlit (Python framework)

HTML5, CSS3, JavaScript (WebAudio API, Canvas)

Font Awesome icons

Audio Analysis:

Librosa
 (beat detection, tempo analysis, waveform processing)

NumPy

Visualizer Effects:

Custom JavaScript + Canvas animations

p5.js integration (for Ripple & others)

Deployment:

Streamlit (Cloud or Local)

Compatible with Docker / any Python hosting

🚀 Getting Started

1️⃣ Clone the Repository

git clone https://github.com/NilamXSC/Music-visualizer.git
cd sonicplay

2️⃣ Install Dependencies

We recommend using a virtual environment.

pip install -r requirements.txt

3️⃣ Run Locally
streamlit run app.py

4️⃣ Upload a Song

Upload an MP3/WAV/FLAC/M4A file from the sidebar

Or use the provided demo tracks in demo_songs/

5️⃣ Enjoy Interactive Visuals 🎶
📂 Project Structure
music-visualizer/
│── app.py                # Main Streamlit app
│── custom_player.py      # Cyberpunk player (HTML/CSS/JS)
│── effects/              # Visualization modes
│   ├── ripple.py
│   ├── synthwave.py
│   ├── ocean_reverb.py
│   ├── resonance.py
│   ├── mesh.py
│   └── beatsaber.py
│── demo_songs/           # Example tracks
│── static/               # Assets (logo, favicon, background video)
│── requirements.txt      # Python dependencies
│── README.md             # Documentation

📸 Screenshots
🔊 Custom Cyber Player

🌌 Synthwave Mode

🌍 Deployment

SonicPlay can be deployed on:

Streamlit Cloud (recommended for demo)

Heroku / Render / Railway

Dockerized environments

Any Python hosting with WebSocket support

streamlit run app.py --server.enableCORS false

🧑‍💻 Author

👤 Nilam Chakraborty

💼 LinkedIn : https://www.linkedin.com/in/chakrabortynilam9

📧 Email:chakrabortynilam88@gmail.com

📜 License

This project is licensed under the MIT License — feel free to use and modify with attribution.

🙌 Acknowledgments

Streamlit community for rapid prototyping

Librosa for amazing audio analysis tools

Web Audio API for real-time DSP effects

Inspiration from Cyberpunk, Vaporwave & Galaxy visual themes

🔥 SonicPlay makes your music visible. Turn every beat into an experience.
