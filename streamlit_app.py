import streamlit as st
import cohere
import re
import time
import traceback
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

try:
    music_client = Client(MUSIC_SPACE)
    st.success("✅ DiffRhythm2 connecté")
except Exception as e:
    st.error(f"❌ DiffRhythm2 indisponible : {e}")
    music_client = None

# ======================================================
# CONSTANTES
# ======================================================
MAX_WORDS = 220
MAX_LINES = 22
SAFE_STEPS = 16
SAFE_CFG = 1.3
FILE_TYPE = "mp3"

# ======================================================
# SESSION STATE APP
# ======================================================
for k in ["lyrics", "audio"]:
    if k not in st.session_state:
        st.session_state[k] = ""

# ======================================================
# 🎤 VOICE MAPPING
# ======================================================
VOICE_MAP = {
    "Baritone": "male baritone vocal, deep warm voice",
    "Tenor": "male tenor vocal, bright expressive voice",
    "Mezzo-soprano": "female mezzo-soprano vocal, warm balanced voice",
    "Soprano": "female soprano vocal, high clear voice"
}

# ======================================================
# LYRICS PIPELINE
# ======================================================
def clean_text(text):
    text = text.replace("```", "")
    text = re.sub(r'\b[A-G](#|b|m|maj|min|sus|dim)?\d*\b', '', text)
    return text.strip()

def enforce_limits(text):
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
    return "\n".join(lines)

def force_lrc_format(raw):
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if len(lines) < 8:
        lines += ["..."] * (8 - len(lines))

    verse1 = lines[0:4]
    chorus = lines[4:8]
    verse2 = lines[8:12] if len(lines) >= 12 else verse1
    outro = lines[-2:]

    return "\n".join([
        "[start]",
        "[intro]",
        "",
        "[verse]", *verse1,
        "",
        "[chorus]", *chorus,
        "",
        "[verse]", *verse2,
        "",
        "[chorus]", *chorus,
        "",
        "[outro]", *outro
    ])

def prepare_lyrics(text):
    return force_lrc_format(enforce_limits(clean_text(text)))

def lyrics_are_valid(text):
    return text and len(text.split()) >= 10

# ======================================================
# 🎤 COHERE LYRICS
# ======================================================
def generate_lyrics(prompt):
    system = """
You are a songwriter.
Write emotional lyrics.
Rules:
- NO chords
- Short lines
- Simple English
- No section labels
- 12–16 lines
"""
    try:
        r = co.chat(
            model=MODEL_NAME,
            message=f"Write lyrics about: {prompt}",
            preamble=system,
            temperature=0.7,
            max_tokens=300
        )
        return r.text.strip()
    except:
        return ""

# ======================================================
# 🎶 MUSIC GENERATION
# ======================================================
def generate_music(lyrics, genre, mood, voice):
    lrc = prepare_lyrics(lyrics)

    with st.expander("🧪 LRC envoyé"):
        st.code(lrc)

    voice_prompt = VOICE_MAP[voice]
    full_prompt = f"{genre}, {mood}, {voice_prompt}, emotional singing"

    try:
        result = music_client.predict(
            lrc=lrc,
            audio_prompt=None,
            text_prompt=full_prompt,
            seed=0,
            randomize_seed=True,
            steps=SAFE_STEPS,
            cfg_strength=SAFE_CFG,
            file_type=FILE_TYPE,
            odeint_method="euler",
            api_name=MUSIC_API
        )
        return result[0] if isinstance(result, (list, tuple)) else result
    except Exception as e:
        st.error(str(e))
        return None

# ======================================================
# UI — LYRICS
# ======================================================
st.markdown("### ✍️ Paroles")

prompt = st.text_input("Décris ta chanson")

if st.button("Générer les paroles"):
    st.session_state.lyrics = generate_lyrics(prompt)

lyrics_input = st.text_area(
    "Paroles (formatées automatiquement)",
    value=st.session_state.lyrics,
    height=260
)

# ======================================================
# UI — MUSIC PARAMETERS
# ======================================================
st.markdown("### 🎼 Paramètres musicaux")

genre = st.selectbox("Genre", ["Pop", "Rock", "Ambient", "Hip-Hop"])
mood = st.selectbox("Mood", ["Sad", "Happy", "Romantic", "Calm"])
voice = st.selectbox(
    "Voix chantée",
    ["Baritone", "Tenor", "Mezzo-soprano", "Soprano"]
)

# ======================================================
# GENERATE
# ======================================================
if st.button("🎵 GÉNÉRER LA MUSIQUE", type="primary"):
    if lyrics_are_valid(lyrics_input):
        with st.spinner("Composition musicale..."):
            audio = generate_music(lyrics_input, genre, mood, voice)
        if audio:
            st.audio(audio)
            with open(audio, "rb") as f:
                st.download_button(
                    "Télécharger MP3",
                    f.read(),
                    file_name=f"senorix_{voice.lower()}_{int(time.time())}.mp3",
                    mime="audio/mp3"
                )
    else:
        st.error("Paroles insuffisantes")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    "<center><b>Senorix AI</b><br>Voix sélectionnable • Accès sécurisé • DiffRhythm2</center>",
    unsafe_allow_html=True
)

