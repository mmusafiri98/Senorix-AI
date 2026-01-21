import streamlit as st
import cohere
import re
import time

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Musical Assistant",
    layout="centered"
)

st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI</h1>
<p style='text-align:center;color:#777;'>
Musical Assistant • Lyrics for Music Generation
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
# UTILS — ACCORDI & STRUTTURA
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
# TYPEWRITER EFFECT
# ======================================================
def typewriter(container, text, delay=0.015):
    rendered = ""
    for char in text:
        rendered += char
        container.markdown(rendered)
        time.sleep(delay)

# ======================================================
# SENORIX AI — CHAT MUSICALE
# ======================================================
def senorix_ai(user_message: str) -> str:
    system_prompt = """
You are Senorix AI, a professional musical assistant and songwriter.

RULES:
- Talk ONLY about music, songwriting, mood, genre, structure
- You may discuss musical themes and creative direction
- You may write or rewrite song lyrics
- If you write lyrics, output ONLY valid lyrics
- Use ONLY the following tags:
  [verse], [chorus], [bridge]
- No titles, no explanations, no comments
"""

    response = co.chat(
        model=MODEL_NAME,
        message=user_message,
        preamble=system_prompt,
        temperature=0.7,
        max_tokens=700
    )
    return response.text

# ======================================================
# UI — CHAT
# ======================================================
st.subheader("💬 Chat musicale")

for role, msg in st.session_state.chat:
    st.markdown(f"**{role}:** {msg}")

user_input = st.text_input(
    "Parle du thème, du mood ou demande d’écrire/modifier la chanson"
)

if st.button("Envoyer"):
    if user_input.strip():
        st.session_state.chat.append(("Utilisateur", user_input))

        thinking = st.empty()
        thinking.markdown("**Senorix AI is thinking...**")

        try:
            reply = senorix_ai(user_input)
        except Exception as e:
            reply = f"⚠️ Erreur Cohere: {e}"

        thinking.empty()

        response_container = st.empty()
        typewriter(response_container, f"**Senorix AI:** {reply}")

        st.session_state.chat.append(("Senorix AI", reply))

        # Se contiene lyrics → pulizia + struttura
        if "[verse]" in reply.lower():
            cleaned = remove_chords(reply)
            structured = normalize_lyrics(cleaned)
            st.session_state.lyrics = structured

# ======================================================
# UI — LYRICS OUTPUT
# ======================================================
st.markdown("---")
st.subheader("🎤 Lyrics (format musique)")

lyrics_input = st.text_area(
    "Lyrics prêts pour la génération musicale",
    value=st.session_state.lyrics,
    height=320
)

col1, col2 = st.columns(2)

with col1:
    if st.button("🧹 Nettoyer accords"):
        cleaned = remove_chords(lyrics_input)
        st.session_state.lyrics = normalize_lyrics(cleaned)

with col2:
    if st.button("💾 Sauvegarder"):
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

