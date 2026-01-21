import streamlit as st
from gradio_client import Client
import re

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Song Preparation",
    layout="wide"
)

# ======================================================
# HEADER
# ======================================================
st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI — Preparazione Testo Canzone</h1>
<p style='text-align:center;color:gray;'>
Pulizia accordi • Strutturazione AI • Pronto per la musica
</p>
<hr>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.header("⚙️ Modalità Testo")

lyrics_mode = st.sidebar.radio(
    "Scegli modalità",
    [
        "🤖 Genera testo (LLaMA)",
        "✍️ Manuale (già formattato)",
        "🧹 Formatta testo esistente (AI rimuove accordi)"
    ]
)

# ======================================================
# UTILS
# ======================================================

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
# AI — CLEAN & STRUCTURE
# ======================================================

def ai_clean_and_structure(raw_text: str) -> str:
    client = Client("huggingface-projects/llama-2-13b-chat")

    system_prompt = """
You are a professional music editor.

YOUR TASK:
- REMOVE ALL chords (C, Am7, F#m7b5, etc.)
- REMOVE musical symbols, tabs, bars
- DO NOT rewrite or improve lyrics
- DO NOT add new lines
- KEEP original words only
- Structure the song using ONLY:
  [verse], [chorus], [bridge]
- Start immediately with [verse]
- Output ONLY lyrics
"""

    user_prompt = f"""
Clean and structure this song text:

{raw_text}
"""

    result = client.predict(
        message=user_prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_new_tokens=800,
        api_name="/chat"
    )

    text = result[0] if isinstance(result, list) else str(result)
    return normalize_lyrics(text)

# ======================================================
# MAIN UI
# ======================================================

st.subheader("📝 Descrizione (opzionale)")
description = st.text_area(
    "Tema o contesto della canzone",
    value="Una canzone sulla libertà e il viaggio"
)

st.markdown("---")
st.subheader("🎤 Testo Canzone")

lyrics_text = ""

# ======================================================
# MODALITÀ
# ======================================================

if lyrics_mode == "✍️ Manuale (già formattato)":
    lyrics_text = st.text_area(
        "Inserisci testo con [verse], [chorus]",
        height=300
    )

elif lyrics_mode == "🤖 Genera testo (LLaMA)":
    if st.button("🤖 Genera testo"):
        with st.spinner("Generazione testo..."):
            client = Client("huggingface-projects/llama-2-13b-chat")
            result = client.predict(
                message=f"Write song lyrics about {description}. Use [verse] and [chorus] only.",
                temperature=0.6,
                max_new_tokens=700,
                api_name="/chat"
            )
            lyrics_text = normalize_lyrics(result[0])
            st.code(lyrics_text)

elif lyrics_mode == "🧹 Formatta testo esistente (AI rimuove accordi)":
    raw_text = st.text_area(
        "Incolla testo / spartito / accordi",
        height=300,
        placeholder="""
C   G   Am   F
Quando cammino solo per la strada
C           G
Cerco una casa che non ho
"""
    )

    if st.button("🧠 Pulisci e formatta con AI"):
        with st.spinner("AI sta rimuovendo accordi..."):
            lyrics_text = ai_clean_and_structure(raw_text)
            st.success("✅ Accordi rimossi e testo strutturato")
            st.code(lyrics_text)

# ======================================================
# VALIDAZIONE FINALE
# ======================================================

st.markdown("---")
if lyrics_text:
    if is_valid_lyrics(lyrics_text):
        st.success("🎉 Testo PRONTO per la generazione musicale")
    else:
        st.error("❌ Testo non valido: servono almeno [verse] e [chorus]")

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<hr>
<div style='text-align:center;color:#777;'>
<b>Senorix AI</b><br>
AI Song Preparation Pipeline
</div>
""", unsafe_allow_html=True)
