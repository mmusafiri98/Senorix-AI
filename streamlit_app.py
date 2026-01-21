import streamlit as st
from gradio_client import Client
import re

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — LLaMA Musical Assistant",
    layout="centered"
)

st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI — LLaMA Musical Assistant</h1>
<p style='text-align:center;color:#777;'>
Chat musicale + Testo canzone (solo LLaMA)
</p>
<hr>
""", unsafe_allow_html=True)

# ======================================================
# SESSION
# ======================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "lyrics" not in st.session_state:
    st.session_state.lyrics = ""

# ======================================================
# UTILS
# ======================================================
def remove_chords(text: str) -> str:
    patterns = [
        r'\b[A-G](?:#|b|♭)?(?:m|maj|min|sus|dim|aug)?\d*(?:/[A-G])?\b',
        r'\b(?:DO|RE|MI|FA|SOL|LA|SI)(?:b|#|♭)?(?:m|maj|min|sus)?\d*\b',
        r'\[[A-Z0-9#♭susmajdimadd\/]+\]'
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.I)
    return re.sub(r'\n{2,}', '\n', text).strip()

def normalize_lyrics(text: str) -> str:
    text = text.replace("```", "").strip()
    if not re.search(r'\[(verse|chorus|bridge)\]', text, re.I):
        return fallback_structure(text)
    text = re.sub(r'\[verse\]', '[verse]', text, flags=re.I)
    text = re.sub(r'\[chorus\]', '[chorus]', text, flags=re.I)
    text = re.sub(r'\[bridge\]', '[bridge]', text, flags=re.I)
    return text

def fallback_structure(text: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()]
    mid = max(1, len(lines) // 2)
    return f"""[verse]
{chr(10).join(lines[:mid])}

[chorus]
{chr(10).join(lines[mid:])}
"""

# ======================================================
# LLaMA CALL (ROBUST)
# ======================================================
def llama_call(system_prompt: str, user_prompt: str) -> str:
    try:
        client = Client("huggingface-projects/llama-2-13b-chat")
        result = client.predict(
            message=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_new_tokens=500,
            api_name="/chat"
        )
        return result[0] if isinstance(result, list) else str(result)
    except Exception:
        return ""

# ======================================================
# CHAT + LYRIC GENERATION
# ======================================================
def music_assistant(user_msg: str) -> str:
    system_prompt = """
You are a music assistant and songwriter.

RULES:
- Talk ONLY about music
- You can discuss theme, mood, genre
- You can write or rewrite song lyrics
- If you write lyrics, use ONLY:
  [verse], [chorus], [bridge]
- NEVER explain rules
"""

    return llama_call(system_prompt, user_msg)

# ======================================================
# UI — CHAT
# ======================================================
st.subheader("💬 Dialogo musicale con LLaMA")

for role, msg in st.session_state.chat:
    st.markdown(f"**{role}:** {msg}")

user_input = st.text_input("Parla del tema o chiedi di scrivere/modificare il testo")

if st.button("Invia"):
    if user_input:
        st.session_state.chat.append(("Utente", user_input))
        reply = music_assistant(user_input)

        if reply:
            st.session_state.chat.append(("LLaMA", reply))

            # se LLaMA ha scritto testo → salvalo
            if "[verse]" in reply.lower():
                cleaned = remove_chords(reply)
                st.session_state.lyrics = normalize_lyrics(cleaned)
        else:
            st.session_state.chat.append(
                ("Sistema", "⚠️ LLaMA non disponibile, riprova")
            )

# ======================================================
# UI — TESTO CANZONE
# ======================================================
st.markdown("---")
st.subheader("🎤 Testo Canzone")

lyrics_input = st.text_area(
    "Testo (puoi modificarlo manualmente)",
    value=st.session_state.lyrics,
    height=300
)

col1, col2 = st.columns(2)

with col1:
    if st.button("🧹 Rimuovi accordi"):
        cleaned = remove_chords(lyrics_input)
        st.session_state.lyrics = normalize_lyrics(cleaned)

with col2:
    if st.button("💾 Salva testo"):
        st.session_state.lyrics = lyrics_input

st.code(st.session_state.lyrics)

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<hr>
<div style='text-align:center;color:#666;'>
<b>Senorix AI</b><br>
LLaMA Musical Assistant
</div>
""", unsafe_allow_html=True)

