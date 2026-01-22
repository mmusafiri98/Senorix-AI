import streamlit as st
import cohere
import re
import time
from gradio_client import Client

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="🎵 Senorix AI — Musical Assistant",
    layout="centered"
)

st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI — Musical Assistant</h1>
<p style='text-align:center;color:#777;'>
Chat musicale • Testo canzone • Generazione musica automatica
</p>
<hr>
""", unsafe_allow_html=True)

# ======================================================
# COHERE
# ======================================================
co = cohere.Client(st.secrets["COHERE_API_KEY"])
MODEL_NAME = "command-r-plus"

# ======================================================
# MUSIC MODEL (HF SPACE)
# ======================================================
MUSIC_SPACE = "https://tencent-songgeneration.hf.space/"
MUSIC_API = "/generate_song"
music_client = Client(MUSIC_SPACE)

# ======================================================
# SESSION STATE
# ======================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "lyrics" not in st.session_state:
    st.session_state.lyrics = ""

if "music_generated" not in st.session_state:
    st.session_state.music_generated = False

# ======================================================
# UTILS — TYPEWRITER EFFECT
# ======================================================
def typewriter(text: str, speed: float = 0.015):
    placeholder = st.empty()
    rendered = ""

    for char in text:
        rendered += char
        placeholder.markdown(f"**Senorix AI:** {rendered}")
        time.sleep(speed)

# ======================================================
# UTILS — REMOVE CHORDS
# ======================================================
def remove_chords(text: str) -> str:
    patterns = [
        r'\b[A-G](?:#|b)?(?:m|maj|min|sus|dim|aug)?\d*(?:/[A-G])?\b',
        r'\[[A-G0-9#bmadsus\/]+\]'
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.I)
    return re.sub(r'\n{2,}', '\n', text).strip()

# ======================================================
# NORMALIZE LYRICS
# ======================================================
def normalize_lyrics(text: str) -> str:
    text = text.replace("```", "").strip()

    if not re.search(r'\[(verse|chorus|bridge)\]', text, re.I):
        return fallback_structure(text)

    text = re.sub(r'\[verse\]', '[verse]', text, flags=re.I)
    text = re.sub(r'\[chorus\]', '[chorus]', text, flags=re.I)
    text = re.sub(r'\[bridge\]', '[bridge]', text, flags=re.I)

    return text.strip()

def fallback_structure(text: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()]
    mid = max(1, len(lines)//2)

    return f"""[verse]
{chr(10).join(lines[:mid])}

[chorus]
{chr(10).join(lines[mid:])}
"""

# ======================================================
# VALIDATE FOR MUSIC
# ======================================================
def lyrics_ready_for_music(text: str) -> bool:
    t = text.lower()

    if "[verse]" not in t or "[chorus]" not in t:
        return False

    if len(text.split()) > 350:
        return False

    if re.search(r'\b[A-G](?:#|b|m|maj|min|sus)?\d*\b', text):
        return False

    return True

# ======================================================
# SENORIX AI (COHERE CHAT)
# ======================================================
def senorix_ai(user_message: str) -> str:
    system_prompt = """
You are Senorix AI, a professional music assistant and songwriter.

RULES:
- Talk ONLY about music, songwriting, mood, genre
- You may write or edit song lyrics
- Lyrics MUST use ONLY:
  [verse], [chorus], [bridge]
- No explanations
"""

    response = co.chat(
        model=MODEL_NAME,
        message=user_message,
        preamble=system_prompt,
        temperature=0.7,
        max_tokens=700
    )

    return response.text.strip()

# ======================================================
# CHAT UI
# ======================================================
st.subheader("💬 Chat musicale")

for role, msg in st.session_state.chat:
    st.markdown(f"**{role}:** {msg}")

user_input = st.text_input("Scrivi a Senorix AI…")

if st.button("Invia"):
    if user_input.strip():
        st.session_state.chat.append(("Utente", user_input))

        with st.spinner("🎵 Senorix AI thinking..."):
            reply = senorix_ai(user_input)

        # Animazione dattilografica
        typewriter(reply)

        st.session_state.chat.append(("Senorix AI", reply))

        # Se l'AI genera testo canzone
        if "[verse]" in reply.lower():
            cleaned = remove_chords(reply)
            structured = normalize_lyrics(cleaned)
            st.session_state.lyrics = structured
            st.session_state.music_generated = False

# ======================================================
# LYRICS UI
# ======================================================
st.markdown("---")
st.subheader("🎤 Testo canzone")

lyrics_input = st.text_area(
    "Testo (modificabile)",
    value=st.session_state.lyrics,
    height=300
)

st.session_state.lyrics = lyrics_input
st.code(st.session_state.lyrics)

# ======================================================
# AUTO MUSIC GENERATION
# ======================================================
if lyrics_ready_for_music(st.session_state.lyrics) and not st.session_state.music_generated:
    st.info("🎶 Testo valido — generazione musica in corso…")

    with st.spinner("🎧 Composizione musicale…"):
        result = music_client.predict(
            lyric=st.session_state.lyrics,
            description="Original song by Senorix AI",
            prompt_audio=None,
            api_name=MUSIC_API
        )

    audio_path = result[0] if isinstance(result, list) else result

    if audio_path:
        st.audio(audio_path)
        st.session_state.music_generated = True

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<hr>
<div style='text-align:center;color:#666;'>
<b>Senorix AI</b><br>
Chat musicale → Testo → Musica automatica
</div>
""", unsafe_allow_html=True)

