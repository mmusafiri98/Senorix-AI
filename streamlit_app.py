import streamlit as st
from gradio_client import Client, file as gr_file
import tempfile
from pathlib import Path
import re

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Musical Assistant",
    layout="centered"
)

# ======================================================
# HEADER
# ======================================================
st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI — Musical Assistant</h1>
<p style='text-align:center;color:#777;'>
Chat musicale • Testo pulito • Generazione musica
</p>
<hr>
""", unsafe_allow_html=True)

# ======================================================
# SESSION STATE
# ======================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "lyrics" not in st.session_state:
    st.session_state.lyrics = ""

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.header("⚙️ Impostazioni")

space_url_song = st.sidebar.text_input(
    "Tencent Song Space",
    value="https://tencent-songgeneration.hf.space/"
)

api_name_song = st.sidebar.text_input(
    "Endpoint musica",
    value="/generate_song"
)

# ======================================================
# HARD CHORD REMOVAL (ROBUSTO)
# ======================================================
def remove_chords(text: str) -> str:
    patterns = [
        r'\b[A-G](?:#|b|♭)?(?:maj|min|m|dim|aug|sus|add)?\d*(?:/[A-G](?:#|b|♭)?)?\b',
        r'\b(?:DO|RE|MI|FA|SOL|LA|SI)(?:b|#|♭)?(?:m|maj|min|sus|add)?\d*\b',
        r'\[[^\]]+\]',
        r'\([^)]+\)',
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)

    text = "\n".join(
        line for line in text.splitlines()
        if re.search(r'[a-zA-Zàèìòùé]', line)
    )
    return re.sub(r'\s{2,}', ' ', text).strip()

# ======================================================
# NORMALIZATION
# ======================================================
def normalize_lyrics(text: str) -> str:
    text = text.replace("```", "").strip()
    match = re.search(r'\[(verse|chorus|bridge)\]', text, re.I)
    if match:
        text = text[match.start():]
    text = re.sub(r'\[verse\]', '[verse]', text, flags=re.I)
    text = re.sub(r'\[chorus\]', '[chorus]', text, flags=re.I)
    text = re.sub(r'\[bridge\]', '[bridge]', text, flags=re.I)
    return text

def is_valid(text: str) -> bool:
    t = text.lower()
    return "[verse]" in t and "[chorus]" in t

def fallback_structure(text: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()]
    mid = len(lines) // 2
    return f"""[verse]
{chr(10).join(lines[:mid])}

[chorus]
{chr(10).join(lines[mid:])}
"""

# ======================================================
# AI CHAT — MUSICA ONLY
# ======================================================
def music_chat(user_msg: str) -> str:
    client = Client("HuggingFaceH4/zephyr-7b-beta")

    system_prompt = """
You are a music assistant.

RULES:
- Talk ONLY about music
- Discuss theme, mood, genre, structure
- Help improve lyrics musically
- NEVER talk about politics, news, coding
"""

    result = client.predict(
        f"{system_prompt}\nUser: {user_msg}",
        api_name="/predict"
    )

    return result

# ======================================================
# UI — CHAT MUSICALE
# ======================================================
st.subheader("💬 Chat musicale con l’AI")

for role, msg in st.session_state.chat:
    st.markdown(f"**{role}:** {msg}")

user_input = st.text_input("Parla del tema, stile o mood della canzone")

if st.button("💬 Invia messaggio"):
    if user_input:
        st.session_state.chat.append(("Utente", user_input))
        reply = music_chat(user_input)
        st.session_state.chat.append(("AI", reply))

# ======================================================
# UI — TESTO CANZONE
# ======================================================
st.markdown("---")
st.subheader("🎤 Testo Canzone")

lyrics_input = st.text_area(
    "Scrivi o modifica il testo (anche con accordi)",
    value=st.session_state.lyrics,
    height=300
)

col1, col2 = st.columns(2)

with col1:
    if st.button("🧹 Rimuovi accordi"):
        cleaned = remove_chords(lyrics_input)
        structured = fallback_structure(cleaned)
        st.session_state.lyrics = structured
        st.success("Accordi rimossi")

with col2:
    if st.button("✍️ Salva testo"):
        st.session_state.lyrics = lyrics_input

st.code(st.session_state.lyrics)

# ======================================================
# GENERAZIONE MUSICA
# ======================================================
st.markdown("---")
st.subheader("🎵 Generazione Musica")

uploaded_audio = st.file_uploader(
    "Audio di riferimento (opzionale)",
    type=["mp3", "wav", "ogg"]
)

if st.button("🎶 Genera canzone"):
    lyrics_final = normalize_lyrics(st.session_state.lyrics)

    if not is_valid(lyrics_final):
        st.warning("Testo non strutturato → fallback automatico")
        lyrics_final = fallback_structure(lyrics_final)

    client_song = Client(space_url_song)

    prompt_audio = None
    if uploaded_audio:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.write(uploaded_audio.getbuffer())
        tmp.close()
        prompt_audio = gr_file(tmp.name)

    with st.spinner("Generazione musica in corso..."):
        result = client_song.predict(
            lyric=lyrics_final,
            prompt_audio=prompt_audio,
            api_name=api_name_song
        )

    audio_path = result[0] if isinstance(result, (list, tuple)) else result

    if audio_path:
        st.audio(audio_path)
        with open(audio_path, "rb") as f:
            st.download_button(
                "⬇️ Scarica canzone",
                f.read(),
                file_name="senorix_song.wav",
                mime="audio/wav"
            )

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<hr>
<div style='text-align:center;color:#666;'>
<b>Senorix AI</b><br>
Musical AI Assistant
</div>
""", unsafe_allow_html=True)

