import streamlit as st
import cohere
import re
import time
import traceback
from gradio_client import Client

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Stable Music Generator",
    layout="centered"
)

# ======================================================
# 🔐 LOGIN SYSTEM
# ======================================================
VALID_USERS = {
    "admin": "admin123",
    "senorix": "music2025"
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Senorix AI — Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if VALID_USERS.get(username) == password:
            st.session_state.authenticated = True
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

# ======================================================
# APP HEADER
# ======================================================
st.title("🎵 Senorix AI — Stable Music Generator")
st.caption("Lyrics → LRC strict → DiffRhythm2")

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
# CONSTANTS
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
    "Baritone": "baritone male voice",
    "Tenor": "tenor male voice",
    "Soprano": "soprano female voice",
    "Mezzo-soprano": "mezzo soprano female voice"
}

# ======================================================
# GENRES (WORLDWIDE)
# ======================================================
GENRES = [
    "Pop", "Rock", "Hip-Hop", "Rap", "Trap",
    "EDM", "House", "Techno", "Trance",
    "Ambient", "Cinematic", "Orchestral",
    "Jazz", "Blues", "Soul", "Funk",
    "R&B", "Reggae", "Dancehall",
    "Latin Pop", "Salsa", "Bachata", "Reggaeton",
    "Afrobeat", "Amapiano",
    "K-Pop", "J-Pop",
    "Folk", "World Folk", "Celtic Folk",
    "Arabic Folk", "African Folk",
    "Indian Classical", "Bollywood",
    "Flamenco", "Fado",
    "Lo-fi", "Chillhop"
]

# ======================================================
# MOODS (GLOBAL)
# ======================================================
MOODS = [
    "Happy", "Sad", "Romantic", "Calm",
    "Dark", "Epic", "Dreamy", "Peaceful",
    "Energetic", "Aggressive",
    "Melancholic", "Hopeful",
    "Spiritual", "Mystical",
    "Emotional", "Nostalgic",
    "Party", "Chill",
    "Meditative", "Uplifting"
]

# ======================================================
# TEXT SANITIZATION
# ======================================================
def clean_text(text: str) -> str:
    text = text.replace("```", "")
    text = re.sub(r'\b[A-G](#|b|m|maj|min|sus|dim)?\d*\b', '', text)
    return text.strip()

def enforce_limits(text: str) -> str:
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])
        st.warning("✂️ Lyrics truncated (word limit)")

    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        st.warning("✂️ Lyrics truncated (line limit)")

    return "\n".join(lines)

# ======================================================
# STRICT LRC FORMAT
# ======================================================
def force_lrc_format(raw_text: str) -> str:
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    while len(lines) < 12:
        lines.append("...")

    verse1 = lines[0:4]
    chorus = lines[4:8]
    verse2 = lines[8:12]
    outro = lines[-2:]

    lrc = [
        "[start]",
        "[intro]",
        "",
        "[verse]",
        *verse1,
        "",
        "[chorus]",
        *chorus,
        "",
        "[verse]",
        *verse2,
        "",
        "[chorus]",
        *chorus,
        "",
        "[outro]",
        *outro
    ]

    return "\n".join(lrc)

def prepare_lyrics(text: str) -> str:
    text = clean_text(text)
    text = enforce_limits(text)
    return force_lrc_format(text)

def lyrics_are_valid(text: str) -> bool:
    return len(text.split()) >= 10

# ======================================================
# COHERE LYRICS
# ======================================================
def generate_lyrics(prompt: str) -> str:
    system = """
You are a songwriter.
Rules:
- Emotional lyrics
- Simple English
- Short lines
- No section labels
- No chords
- 12 to 16 lines
"""

    response = co.chat(
        model=MODEL_NAME,
        message=f"Write lyrics about: {prompt}",
        preamble=system,
        temperature=0.7,
        max_tokens=300
    )

    return response.text.strip()

# ======================================================
# MUSIC GENERATION (CORRECT API)
# ======================================================
def generate_music(lyrics, genre, mood, voice):
    lrc = prepare_lyrics(lyrics)

    with st.expander("🧪 LRC sent to DiffRhythm2"):
        st.code(lrc)

    text_prompt = f"{genre}, {mood}, {VOICE_MAP[voice]}, emotional singing"

    try:
        result = music_client.predict(
            lrc,
            text_prompt,
            SAFE_STEPS,
            SAFE_CFG,
            FILE_TYPE,
            api_name=MUSIC_API
        )
    except Exception as e:
        st.error("❌ DiffRhythm2 error")
        st.exception(e)
        return None

    if isinstance(result, (list, tuple)):
        return result[0]
    return result

# ======================================================
# UI — LYRICS
# ======================================================
st.markdown("### ✍️ Lyrics")

prompt = st.text_input("Describe your song")

if st.button("Generate lyrics"):
    with st.spinner("Writing lyrics..."):
        st.session_state.lyrics = generate_lyrics(prompt)

lyrics_input = st.text_area(
    "Lyrics (free — LRC enforced automatically)",
    value=st.session_state.get("lyrics", ""),
    height=260
)

# ======================================================
# UI — MUSIC OPTIONS
# ======================================================
genre = st.selectbox("Genre", GENRES)
mood = st.selectbox("Mood", MOODS)
voice = st.selectbox("Voice", list(VOICE_MAP.keys()))

# ======================================================
# GENERATE MUSIC
# ======================================================
if st.button("🎵 GENERATE MUSIC", type="primary"):
    if not lyrics_are_valid(lyrics_input):
        st.error("❌ Lyrics too short")
    else:
        with st.spinner("Composing music..."):
            audio = generate_music(lyrics_input, genre, mood, voice)

        if audio:
            st.audio(audio)
            with open(audio, "rb") as f:
                st.download_button(
                    "⬇️ Download MP3",
                    f.read(),
                    file_name=f"senorix_{int(time.time())}.mp3",
                    mime="audio/mp3"
                )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    "<center><b>Senorix AI</b><br>LRC strict • DiffRhythm2 • Worldwide Music</center>",
    unsafe_allow_html=True
)
