import streamlit as st
import cohere
import re
import time
from gradio_client import Client

# ======================================================
# 🔐 LOGIN CONFIG
# ======================================================
VALID_USERS = {
    "admin": "admin123",
    "senorix": "music2025"
}

# ======================================================
# SESSION INIT
# ======================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ======================================================
# LOGIN UI
# ======================================================
def login_screen():
    st.set_page_config(page_title="Senorix AI — Login", layout="centered")
    st.title("🔐 Senorix AI")
    st.caption("Connexion requise")

    with st.form("login"):
        u = st.text_input("Nom d'utilisateur")
        p = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Se connecter")

    if ok:
        if u in VALID_USERS and VALID_USERS[u] == p:
            st.session_state.logged_in = True
            st.session_state.username = u
            st.rerun()
        else:
            st.error("Identifiants incorrects")

def logout():
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Senorix AI — Stable Music Generator", layout="centered")
st.title("🎵 Senorix AI — Stable Music Generator")
st.caption(f"Connecté en tant que **{st.session_state.username}**")
logout()

# ======================================================
# COHERE
# ======================================================
co = cohere.Client(st.secrets["COHERE_API_KEY"])
MODEL_NAME = "command-a-vision-07-2025"

# ======================================================
# DIFFRHYTHM2
# ======================================================
MUSIC_SPACE = "ASLP-lab/DiffRhythm2"
MUSIC_API = "/infer_music"

music_client = Client(MUSIC_SPACE)

# ======================================================
# CONSTANTES
# ======================================================
MAX_WORDS = 220
MAX_LINES = 22
SAFE_STEPS = 16
SAFE_CFG = 1.3
FILE_TYPE = "mp3"

# ======================================================
# VOICES
# ======================================================
VOICE_MAP = {
    "Baritone": "male baritone vocal, deep warm voice",
    "Tenor": "male tenor vocal, bright expressive voice",
    "Mezzo-soprano": "female mezzo-soprano vocal, warm balanced voice",
    "Soprano": "female soprano vocal, high clear voice"
}

# ======================================================
# GENRES & MOODS
# ======================================================
GENRES = [
    "Pop", "Rock", "Hip-Hop", "Jazz", "Classical",
    "Electronic", "Ambient", "Lo-fi", "Synthwave",
    "Folk", "World Folk", "Celtic Folk", "Nordic Folk",
    "African", "Afrobeat", "Latin", "Salsa", "Reggaeton",
    "Flamenco", "Tango", "Fado",
    "Indian Classical", "Bollywood",
    "Arabic", "Middle Eastern",
    "Asian Traditional", "K-Pop", "J-Pop",
    "Gospel", "Soul", "R&B", "Funk",
    "Blues", "Country", "Bluegrass",
    "Metal", "Punk", "Indie",
    "Cinematic", "Soundtrack"
]

MOODS = [
    "Happy", "Sad", "Melancholic",
    "Romantic", "Passionate",
    "Calm", "Peaceful", "Relaxing",
    "Energetic", "Powerful", "Epic",
    "Dark", "Mysterious",
    "Hopeful", "Inspiring",
    "Nostalgic", "Dreamy",
    "Spiritual", "Sacred",
    "Aggressive", "Angry",
    "Chill", "Warm", "Cozy",
    "Ethereal", "Atmospheric"
]

# ======================================================
# LYRICS PIPELINE
# ======================================================
def prepare_lyrics(text):
    text = re.sub(r'\b[A-G](#|b|m|maj|min|sus|dim)?\d*\b', '', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 8:
        lines += ["..."] * (8 - len(lines))

    return "\n".join([
        "[start]",
        "[intro]",
        "",
        "[verse]", *lines[:4],
        "",
        "[chorus]", *lines[4:8],
        "",
        "[verse]", *lines[8:12] if len(lines) >= 12 else *lines[:4],
        "",
        "[chorus]", *lines[4:8],
        "",
        "[outro]", *lines[-2:]
    ])

# ======================================================
# COHERE LYRICS
# ======================================================
def generate_lyrics(prompt):
    system = """
Write emotional song lyrics.
No chords.
Short lines.
No labels.
"""
    r = co.chat(
        model=MODEL_NAME,
        message=f"Write lyrics about: {prompt}",
        preamble=system,
        temperature=0.7,
        max_tokens=300
    )
    return r.text.strip()

# ======================================================
# MUSIC GENERATION
# ======================================================
def generate_music(lyrics, genre, mood, voice):
    lrc = prepare_lyrics(lyrics)
    with st.expander("🧪 LRC"):
        st.code(lrc)

    prompt = f"{genre}, {mood}, {VOICE_MAP[voice]}, emotional singing"

    result = music_client.predict(
        lrc=lrc,
        audio_prompt=None,
        text_prompt=prompt,
        seed=0,
        randomize_seed=True,
        steps=SAFE_STEPS,
        cfg_strength=SAFE_CFG,
        file_type=FILE_TYPE,
        odeint_method="euler",
        api_name=MUSIC_API
    )

    return result[0] if isinstance(result, (list, tuple)) else result

# ======================================================
# UI
# ======================================================
st.markdown("### ✍️ Paroles")
prompt = st.text_input("Décris ta chanson")

if st.button("Générer les paroles"):
    st.session_state.lyrics = generate_lyrics(prompt)

lyrics = st.text_area("Paroles", value=st.session_state.get("lyrics", ""), height=260)

st.markdown("### 🎼 Paramètres musicaux")
genre = st.selectbox("Genre musical", GENRES)
mood = st.selectbox("Mood", MOODS)
voice = st.selectbox("Voix chantée", list(VOICE_MAP.keys()))

if st.button("🎵 GÉNÉRER LA MUSIQUE", type="primary"):
    with st.spinner("Composition musicale..."):
        audio = generate_music(lyrics, genre, mood, voice)
    st.audio(audio)
    with open(audio, "rb") as f:
        st.download_button(
            "Télécharger MP3",
            f.read(),
            file_name=f"senorix_{genre}_{voice}.mp3",
            mime="audio/mp3"
        )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    "<center><b>Senorix AI</b><br>World Genres • Global Moods • DiffRhythm2</center>",
    unsafe_allow_html=True
)
