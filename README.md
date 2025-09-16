# 🎶 SonicPlay — Music Visualizer

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![Librosa](https://img.shields.io/badge/Librosa-Audio%20Analysis-orange)
![JioSaavn](https://img.shields.io/badge/API-JioSaavn-00C300?logo=spotify&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative)
![Status](https://img.shields.io/badge/Status-Active-success?logo=github)

---

> A modern, interactive **music visualizer** built with **Streamlit** and integrated with **JioSaavn** 🎧  
> Upload your own songs or search directly from JioSaavn, and experience immersive real-time visual effects.

---

## 🚀 Live Demo
👉 [**Try SonicPlay Now**](https://music-visualizer-hxuorbfc6jxffrzaujna37.streamlit.app/)  

---

## ✨ Features

- 🎼 **Play music from multiple sources**
  - Upload your own MP3/WAV/FLAC files
  - Choose from included **demo songs**
  - Search and play tracks directly from **JioSaavn**
- 🎨 **Dynamic Visualizers**
  - Ripple
  - Synthwave (retro grid 🌌)
  - Ocean Reverb
  - Resonance
  - Mesh
  - BeatSaber
  - Custom Player
- 🎚 **Custom Controls**
  - Adjust beat sensitivity
  - Switch between multiple **themes** (Neon, Cyberpunk, Vaporwave, Galaxy, etc.)
  - Change particle intensity & animation parameters
- 💡 **Interactive UI**
  - "Now Playing" info above player
  - Smooth **reload with st.rerun()**
  - Intro animation for immersive entry
- 🌐 **Accessible Anywhere**
  - Runs in the browser via Streamlit
  - No installation needed for end-users

---

## 🛠️ Tech Stack

- [Streamlit](https://streamlit.io/) — Frontend framework
- [Librosa](https://librosa.org/) — Audio analysis (beats, tempo, waveform)
- [Numpy](https://numpy.org/) — Data processing
- [Requests](https://docs.python-requests.org/) — API requests
- [JioSaavn API](https://saavn.dev) — Music search & playback integration
- Custom HTML + CSS + JS animations for **visual effects**

---

## 📂 Project Structure

Music-visualizer/ ├── app.py                # Main Streamlit app ├── custom_player.py      # Custom audio player ├── effects/              # Visualization effects (Ripple, Synthwave, etc.) ├── demo_songs/           # Sample demo songs ├── static/               # Static assets (logo, video, favicon) ├── requirements.txt      # Dependencies └── README.md             # Project documentation

---

## ⚡ Getting Started

### 1️⃣ Clone the repository
```bash
git clone https://github.com/NilamXSC/Music-visualizer.git
cd Music-visualizer

2️⃣ Create a virtual environment

python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

3️⃣ Install dependencies

pip install -r requirements.txt

4️⃣ Run the app

streamlit run app.py

Then open 👉 http://localhost:8501/ in your browser.


---

🎧 How to Use

1. Choose Mode

Continue as Guest, or simply start searching.



2. Play a Song

Upload a file, select from demo songs, or search via JioSaavn.



3. Customize Visualizer

Change visual mode, sensitivity, particles, and theme.



4. Enjoy the Music

Hit Start Visualizer and immerse yourself! 🔥





---

📸 Screenshots

Visualizer	Demo

Synthwave	🌌 Retro futuristic grid with beats
Ripple	💧 Wave-like ripples synced to tempo
Mesh	🔗 3D reactive mesh
BeatSaber	⚡ Neon block slicer animation


(Add actual screenshots here if available)


---

🔗 Connect With Me

💻 GitHub: NilamXSC

💼 LinkedIn: Nilam Chakraborty

📷 Instagram: @nilam.jackdaw7

🌍 Official App: SonicPlay



---

⭐ Acknowledgments

Streamlit community for enabling quick data apps

saavn.dev for JioSaavn API

Open-source libraries powering this project



---

📝 License

This project is licensed under the MIT License.
Feel free to use, modify, and share — just credit the author.


---

🎶 Made with passion by Nilam Chakraborty 💜