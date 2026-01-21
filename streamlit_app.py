import streamlit as st
from gradio_client import Client, file as gr_file
import tempfile
from pathlib import Path
import time
import re

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Song Generation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# STYLE
# ======================================================
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 22px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-radius: 14px;
    margin-bottom: 30px;
}
.stButton>button {
    width: 100%;
    background-color: #667eea;
    color: white;
    font-weight: bold;
    border-radius: 12px;
    padding: 14px;
}
.info-box {
    background: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
<h1>🎵 Senorix AI — Song Generation</h1>
<p>Lyrics AI + Musica Personalizzata</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.header("⚙️ Configurazione Testo")

lyrics_mode = st.sidebar.radio(
    "Modalità testo",
    [
        "🤖 Automatica (LLaMA-2)",
        "✍️ Manuale (già formattato)",
        "🧹 Formatta testo esistente (rimuove accordi)"
    ]
)

# ======================================================
# UTILS TESTO
# ======================================================

CHORD_REGEX = r"""
(\b[A-G][#b]?(maj|min|dim|aug|sus|m)?\d?\b) |
(\[[A-G][^\]]+\]) |
(\([A-G][^)]+\)) |
(\|[^|]+\|)
"""

def remove_chords(text: str) -> str:
    text = re.sub(CHORD_REGEX, "", text, flags=re.VERBOSE)
    return re.sub(r'\s{2,}', ' ', text).strip()

def auto_structure_lyrics(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    verse = lines[:len(lines)//2]
    chorus = lines[len(lines)//2:]

    return f"""[verse]
{chr(10).join(verse)}

[chorus]
{chr(10).join(chorus)}
"""

def normalize_lyrics(text: str) -> str:
    text = text.replace("```", "").strip()
    match = re.search(r'\[(verse|chorus|bridge)\]', text, re.I)
    if match:
        text = text[match.start():]
    text = re.sub(r'\[verse\]', '[verse]', text, flags=re.I)
    text = re.sub(r'\[chorus\]', '[chorus]', text, flags=re.I)
    text = re.sub(r'\[bridge\]', '[bridge]', text, flags=re.I)
    return text.strip()

def is_valid_lyrics(text: str) -> bool:
    t = text.lower()
    return "[verse]" in t and "[chorus]" in t

# ======================================================
# MAIN UI
# ======================================================

st.subheader("📝 Descrizione Canzone")
description = st.text_area(
    "Tema / messaggio",
    value="Una canzone sull'immigrazione e la libertà"
)

# ================================
# FORM TESTO
# ================================

st.markdown("---")
st.subheader("🎤 Testo Canzone")

lyrics_text = ""

if lyrics_mode == "✍️ Manuale (già formattato)":
    lyrics_text = st.text_area(
        "Inserisci testo con [verse], [chorus]",
        height=300
    )

elif lyrics_mode == "🧹 Formatta testo esistente (rimuove accordi)":
    raw_text = st.text_area(
        "Incolla testo / spartito / accordi",
        height=300,
        placeholder="C  G  Am  F\nQuando cammino solo per la strada..."
    )

    if st.button("🧹 Pulisci e formatta"):
        cleaned = remove_chords(raw_text)
        structured = auto_structure_lyrics(cleaned)
        lyrics_text = normalize_lyrics(structured)

        st.success("✅ Testo convertito")
        st.code(lyrics_text)

elif lyrics_mode == "🤖 Automatica (LLaMA-2)":
    if st.button("🤖 Genera Testo"):
        with st.spinner("Generazione in corso..."):
            client = Client("huggingface-projects/llama-2-13b-chat")
            result = client.predict(
                message=f"Write song lyrics about {description}. Use [verse] and [chorus] only.",
                api_name="/chat"
            )
            lyrics_text = normalize_lyrics(result[0])
            st.code(lyrics_text)

# ======================================================
# VALIDAZIONE
# ======================================================

st.markdown("---")
if lyrics_text:
    if not is_valid_lyrics(lyrics_text):
        st.error("❌ Testo non valido: servono almeno [verse] e [chorus]")
    else:
        st.success("✅ Testo pronto per la generazione musicale")

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<div style='text-align:center;color:#666;padding:20px;'>
<b>Senorix AI</b><br>
Generazione avanzata di canzoni
</div>
""", unsafe_allow_html=True)
