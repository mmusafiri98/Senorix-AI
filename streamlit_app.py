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

st.title("🎵 Senorix AI — Stable Music Generator")
st.caption("Lyrics → Format LRC strict → DiffRhythm2")

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
# SESSION STATE
# ======================================================
for key in ["lyrics", "audio"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ======================================================
# 🔒 LYRICS SECURITY PIPELINE
# ======================================================
def clean_text(text: str) -> str:
    text = text.replace("```", "")
    text = re.sub(r'\b[A-G](#|b|m|maj|min|sus|dim)?\d*\b', '', text)
    return text.strip()

def enforce_limits(text: str) -> str:
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])
        st.warning("✂️ Paroles tronquées (max mots)")

    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        st.warning("✂️ Paroles tronquées (max lignes)")

    return "\n".join(lines)

# ======================================================
# 🔒 STRICT LRC FORMATTER
# ======================================================
def force_lrc_format(raw_text: str) -> str:
    """
    FORCE le format exact :
    [start]
    [intro]
    [verse]
    ...
    [chorus]
    ...
    [verse]
    ...
    [outro]
    """

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if len(lines) < 8:
        lines += ["..."] * (8 - len(lines))

    # Découpage logique
    verse1 = lines[0:4]
    chorus1 = lines[4:8]
    verse2 = lines[8:12] if len(lines) >= 12 else lines[0:4]
    chorus2 = chorus1
    outro = lines[-2:]

    lrc = [
        "[start]",
        "[intro]",
        "",
        "[verse]",
        *verse1,
        "",
        "[chorus]",
        *chorus1,
        "",
        "[verse]",
        *verse2,
        "",
        "[chorus]",
        *chorus2,
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
    return text and len(text.split()) >= 10

# ======================================================
# 🎤 COHERE LYRICS GENERATION
# ======================================================
def generate_lyrics(prompt: str) -> str:
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
    except Exception as e:
        st.error(f"Cohere error: {e}")
        return ""

# ======================================================
# 🎶 MUSIC GENERATION
# ======================================================
def generate_music(lyrics, mood, genre):
    if not music_client:
        return None

    lrc = prepare_lyrics(lyrics)

    with st.expander("🧪 LRC FINAL ENVOYÉ"):
        st.code(lrc)

    prompt = f"{genre}, {mood}"

    try:
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

        if isinstance(result, (list, tuple)):
            return result[0]
        return result

    except Exception as e:
        st.error(str(e))
        with st.expander("Trace"):
            st.code(traceback.format_exc())
        return None

# ======================================================
# UI — LYRICS
# ======================================================
st.markdown("### ✍️ Génération des paroles")

prompt = st.text_input("Décris ta chanson")

if st.button("Générer paroles"):
    with st.spinner("Écriture..."):
        st.session_state.lyrics = generate_lyrics(prompt)

lyrics_input = st.text_area(
    "Paroles (libres — format forcé automatiquement)",
    value=st.session_state.lyrics,
    height=260
)

st.session_state.lyrics = lyrics_input

# ======================================================
# UI — MUSIC
# ======================================================
genre = st.selectbox("Genre", ["Pop", "Rock", "Ambient", "Hip-Hop"])
mood = st.selectbox("Mood", ["Sad", "Happy", "Romantic", "Calm"])

if st.button("🎵 GÉNÉRER LA MUSIQUE", type="primary"):
    if not lyrics_are_valid(lyrics_input):
        st.error("Paroles insuffisantes")
    else:
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

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    "<center><b>Senorix AI</b><br>Format LRC strict • DiffRhythm2</center>",
    unsafe_allow_html=True
)

