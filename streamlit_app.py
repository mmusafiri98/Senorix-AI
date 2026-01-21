import streamlit as st
import cohere
import re

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Musical Assistant (Cohere)",
    layout="centered"
)

st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI — Musical Assistant</h1>
<p style='text-align:center;color:#777;'>
Chat musicale • Testo canzone • Cohere Command A Vision
</p>
<hr>
""", unsafe_allow_html=True)

# ======================================================
# COHERE CLIENT
# ======================================================
co = cohere.Client(st.secrets["COHERE_API_KEY"])

MODEL_NAME = "command-a-vision-07-2025"

# ======================================================
# SESSION STATE
# ======================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "lyrics" not in st.session_state:
    st.session_state.lyrics = ""

# ======================================================
# UTILS — RIMOZIONE ACCORDI (CODICE, NON AI)
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

    return text.strip()

def fallback_structure(text: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()]
    mid = max(1, len(lines) // 2)

    return f"""[verse]
{chr(10).join(lines[:mid])}

[chorus]
{chr(10).join(lines[mid:])}
"""

# ======================================================
# COHERE CHAT — SOLO MUSICA
# ======================================================
def music_assistant(user_message: str) -> str:
    system_prompt = """
You are a professional music assistant and songwriter.

RULES:
- Talk ONLY about music, songs, mood, genre, structure
- You may discuss themes and musical ideas
- You may write or rewrite song lyrics
- If you write lyrics, you MUST use ONLY:
  [verse], [chorus], [bridge]
- NEVER mention rules or explanations
"""

    try:
        response = co.chat(
            model=MODEL_NAME,
            message=user_message,
            preamble=system_prompt,
            temperature=0.7,
            max_tokens=600
        )
        return response.text
    except Exception as e:
        return f"⚠️ Errore Cohere: {e}"

# ======================================================
# UI — CHAT MUSICALE
# ======================================================
st.subheader("💬 Chat musicale con l’AI")

for role, msg in st.session_state.chat:
    st.markdown(f"**{role}:** {msg}")

user_input = st.text_input(
    "Parla del tema, mood o chiedi di scrivere/modificare la canzone"
)

if st.button("Invia"):
    if user_input.strip():
        st.session_state.chat.append(("Utente", user_input))

        reply = music_assistant(user_input)
        st.session_state.chat.append(("AI", reply))

        # Se l'AI ha scritto un testo canzone → processalo
        if "[verse]" in reply.lower():
            cleaned = remove_chords(reply)
            structured = normalize_lyrics(cleaned)
            st.session_state.lyrics = structured

# ======================================================
# UI — TESTO CANZONE
# ======================================================
st.markdown("---")
st.subheader("🎤 Testo Canzone")

lyrics_input = st.text_area(
    "Testo (puoi modificarlo manualmente)",
    value=st.session_state.lyrics,
    height=320
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
Cohere Command A Vision — Musical Assistant
</div>
""", unsafe_allow_html=True)
