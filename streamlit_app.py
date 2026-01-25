import streamlit as st
import cohere
import re
import time
import traceback
from gradio_client import Client

# ======================================================
# 🔐 LOGIN CONFIG (À MODIFIER)
# ======================================================
VALID_USERS = {
    "admin": "admin123",
    "senorix": "music2025"
}

# ======================================================
# SESSION STATE INIT
# ======================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ======================================================
# 🔐 LOGIN UI
# ======================================================
def login_screen():
    st.set_page_config(
        page_title="Senorix AI — Login",
        layout="centered"
    )

    st.title("🔐 Senorix AI")
    st.caption("Connexion requise")

    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")

    if submit:
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Connexion réussie")
            st.rerun()
        else:
            st.error("Identifiants incorrects")

# ======================================================
# 🚪 LOGOUT
# ======================================================
def logout_button():
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ======================================================
# 🔒 BLOQUER L’APP SI NON CONNECTÉ
# ======================================================
if not st.session_state.logged_in:
    login_screen()
    st.stop()

# ======================================================
# PAGE CONFIG (APP)
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Stable Music Generator",
    layout="centered"
)

st.title("🎵 Senorix AI — Stable Music Generator")
st.caption(f"Connecté en tant que **{st.session_state.username}**")

logout_button()

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
    st.success("✅ Connecté à DiffRhythm2")
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
for key in ["lyrics", "audio"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ======================================================
# 🔒 LYRICS PIPELINE
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

def force_lrc_format(raw_text):
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if len(lines) < 8:
        lines += ["..."] * (8 - len(lines))

    verse1 = lines[0:4]
    chorus1 = lines[4:8]
    verse2 = lines[8:12] if len(lines) >= 12 else verse1
    outro = lines[-2:]

    lrc = [
        "[start]",
        "[intro]",
        "",
        "[verse]", *verse1,
        "",
        "[chorus]", *chorus1,
        "",
        "[verse]", *verse2,
        "",
        "[chorus]", *chorus1,
        "",
        "[outro]", *outro
    ]
    return "\n".join(lrc)

def prepare_lyrics(text):
    return force_lrc_format(enforce_limits(clean_text(text)))

def lyrics_are_valid(text):
    return text and len(text.split()) >= 10

# ======================================================
# 🎤 COHERE
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
# 🎶 MUSIC
# ======================================================
def generate_music(lyrics, mood, genre):
    lrc = prepare_lyrics(lyrics)

    with st.expander("🧪 LRC ENVOYÉ"):
        st.code(lrc)

    try:
        result = music_client.predict(
            lrc=lrc,
            audio_prompt=None,
            text_prompt=f"{genre}, {mood}",
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
# UI
# ======================================================
st.markdown("### ✍️ Génération des paroles")

prompt = st.text_input("Décris ta chanson")

if st.button("Générer paroles"):
    st.session_state.lyrics = generate_lyrics(prompt)

lyrics_input = st.text_area(
    "Paroles",
    value=st.session_state.lyrics,
    height=260
)

genre = st.selectbox("Genre", ["Pop", "Rock", "Ambient", "Hip-Hop"])
mood = st.selectbox("Mood", ["Sad", "Happy", "Romantic", "Calm"])

if st.button("🎵 GÉNÉRER LA MUSIQUE", type="primary"):
    if lyrics_are_valid(lyrics_input):
        with st.spinner("Composition musicale..."):
            audio = generate_music(lyrics_input, mood, genre)
        if audio:
            st.audio(audio)
            with open(audio, "rb") as f:
                st.download_button(
                    "Télécharger MP3",
                    f.read(),
                    file_name=f"senorix_{int(time.time())}.mp3",
                    mime="audio/mp3"
                )
    else:
        st.error("Paroles insuffisantes")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    "<center><b>Senorix AI</b><br>Accès sécurisé • DiffRhythm2</center>",
    unsafe_allow_html=True
)
