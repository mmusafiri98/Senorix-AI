import streamlit as st
import cohere
import re
import time
from gradio_client import Client

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="🎵 Senorix AI — Stable Music Generator",
    layout="centered"
)

st.title("🎵 Senorix AI — Stable Music Generator")
st.caption("Lyrics → Format sécurisé → Génération musicale stable (DiffRhythm2)")

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
except Exception as e:
    st.error(f"❌ Impossible de connecter DiffRhythm2 : {e}")
    music_client = None

# ======================================================
# CONSTANTES DE SÉCURITÉ GPU
# ======================================================
MAX_WORDS = 220
MAX_LINES = 20
SAFE_STEPS = 8
SAFE_CFG = 1.0
FILE_TYPE = "wav"

# ======================================================
# SESSION STATE
# ======================================================
for key in ["lyrics", "audio", "generated"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ======================================================
# UTILS
# ======================================================
def clean_text(text: str) -> str:
    text = text.replace("```", "")
    text = re.sub(r'\b[A-G](#|b|m|maj|min|sus|dim)?\d*\b', '', text)
    return text.strip()

def enforce_limits(text: str) -> str:
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])

    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]

    return "\n".join(lines)

def safe_lrc_structure(text: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()]

    verse = lines[:6]
    chorus = lines[6:10] if len(lines) > 6 else lines[:4]

    return f"""[start]
[verse]
{chr(10).join(verse)}

[chorus]
{chr(10).join(chorus)}

[outro]"""

def prepare_lyrics(text: str) -> str:
    text = clean_text(text)
    text = enforce_limits(text)
    return safe_lrc_structure(text)

def lyrics_are_valid(text: str) -> bool:
    if len(text.split()) < 20:
        return False
    if len(text.split()) > MAX_WORDS:
        return False
    return True

# ======================================================
# COHERE — LYRICS GENERATION
# ======================================================
def generate_lyrics(prompt: str) -> str:
    system = """
You are a professional songwriter.
Write short emotional lyrics.
Rules:
- NO chords
- MAX 2 sections
- Simple lines
- Emotional
"""
    response = co.chat(
        model=MODEL_NAME,
        message=prompt,
        preamble=system,
        temperature=0.7,
        max_tokens=300
    )
    return response.text.strip()

# ======================================================
# MUSIC GENERATION (SAFE)
# ======================================================
def generate_music_safe(lyrics: str, mood: str, genre: str):
    if not music_client:
        return None

    lrc = prepare_lyrics(lyrics)
    prompt = f"{genre}, {mood}"

    try:
        result = music_client.predict(
            lrc=lrc,
            text_prompt=prompt,
            steps=SAFE_STEPS,
            cfg_strength=SAFE_CFG,
            randomize_seed=True,
            file_type=FILE_TYPE,
            api_name=MUSIC_API
        )
        return result[0]

    except Exception:
        # Fallback ULTRA SAFE
        try:
            result = music_client.predict(
                lrc=lrc,
                text_prompt="ambient, simple",
                steps=6,
                cfg_strength=0.8,
                randomize_seed=True,
                file_type="wav",
                api_name=MUSIC_API
            )
            return result[0]
        except Exception:
            return None

# ======================================================
# UI
# ======================================================
st.markdown("### ✍️ Lyrics")

user_prompt = st.text_input("Décris ta chanson")

if st.button("🎼 Générer les paroles"):
    with st.spinner("Écriture des paroles..."):
        lyrics = generate_lyrics(user_prompt)
        st.session_state.lyrics = lyrics
        st.session_state.generated = False

lyrics_input = st.text_area(
    "Paroles (auto-sécurisées)",
    value=st.session_state.lyrics or "",
    height=220
)

st.session_state.lyrics = lyrics_input

st.markdown("### 🎚️ Musique")

genre = st.selectbox("Genre", ["Pop", "Electronic", "Jazz", "Ambient"])
mood = st.selectbox("Mood", ["Happy", "Sad", "Calm", "Romantic"])

if st.button("🎧 Générer la musique"):
    if not lyrics_are_valid(lyrics_input):
        st.warning("⚠️ Lyrics trop courtes ou invalides")
    else:
        with st.spinner("Génération musicale stable..."):
            audio = generate_music_safe(lyrics_input, mood, genre)
            if audio:
                st.audio(audio)
                st.session_state.audio = audio
                st.success("✅ Musique générée avec succès")
            else:
                st.error("❌ GPU occupé — réessaie dans quelques secondes")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption("Powered by Cohere + DiffRhythm2 — Version GPU Safe")

