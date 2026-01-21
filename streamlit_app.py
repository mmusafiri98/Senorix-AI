import streamlit as st
from gradio_client import Client
import re

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Pulizia Testo Canzone",
    layout="wide"
)

# ======================================================
# HEADER
# ======================================================
st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI — Pulizia & Strutturazione Testo</h1>
<p style='text-align:center;color:#777;'>
Accordi rimossi • AI controllata • Output musicale valido
</p>
<hr>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.header("⚙️ Modalità Testo")

mode = st.sidebar.radio(
    "Scegli modalità",
    [
        "🧹 Pulisci testo con accordi (AI + controllo)",
        "✍️ Testo già formattato"
    ]
)

# ======================================================
# HARD CHORD REMOVAL (DEFINITIVO)
# ======================================================
def hard_remove_chords(text: str) -> str:
    patterns = [
        # accordi anglosassoni + jazz
        r'\b[A-G](?:#|b|♭)?(?:maj|min|m|dim|aug|sus|add)?\d*(?:/[A-G](?:#|b|♭)?)?\b',
        # accordi latini (DO RE MI FA SOL LA SI)
        r'\b(?:DO|RE|MI|FA|SOL|LA|SI)(?:b|#|♭)?(?:m|maj|min|sus|add)?\d*\b',
        # accordi tra parentesi
        r'\[[^\]]+\]',
        r'\([^)]+\)',
    ]

    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)

    # rimuove righe che non contengono lettere (solo accordi)
    text = "\n".join(
        line for line in text.splitlines()
        if re.search(r'[a-zA-Zàèìòùé]', line)
    )

    # pulizia spazi
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

# ======================================================
# AI STRUCTURING (SOLO TAG)
# ======================================================
def ai_structure_only(clean_text: str) -> str:
    client = Client("huggingface-projects/llama-2-13b-chat")

    system_prompt = """
You are a strict formatter.

RULES:
- DO NOT rewrite lyrics
- DO NOT add or remove words
- DO NOT translate
- ONLY add structure tags:
  [verse], [chorus], [bridge]
- Start immediately with [verse]
- Output ONLY structured lyrics
"""

    user_prompt = f"""
Structure this song text:

{clean_text}
"""

    result = client.predict(
        message=user_prompt,
        system_prompt=system_prompt,
        temperature=0.0,
        max_new_tokens=700,
        api_name="/chat"
    )

    text = result[0] if isinstance(result, list) else str(result)
    return normalize_lyrics(text)

# ======================================================
# NORMALIZATION & VALIDATION
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
# MAIN UI
# ======================================================
st.subheader("🎤 Testo Canzone")

final_lyrics = ""

if mode == "🧹 Pulisci testo con accordi (AI + controllo)":
    raw_text = st.text_area(
        "Incolla testo / spartito / accordi",
        height=350
    )

    if st.button("🧠 Rimuovi accordi e struttura"):
        with st.spinner("Pulizia accordi..."):
            cleaned = hard_remove_chords(raw_text)

        with st.spinner("Strutturazione AI..."):
            structured = ai_structure_only(cleaned)

        if not is_valid(structured):
            st.warning("⚠️ AI non valida → uso fallback sicuro")
            structured = fallback_structure(cleaned)

        final_lyrics = structured
        st.success("✅ Testo pronto per la generazione musicale")
        st.code(final_lyrics)

elif mode == "✍️ Testo già formattato":
    final_lyrics = st.text_area(
        "Inserisci testo con [verse] e [chorus]",
        height=350
    )

# ======================================================
# VALIDAZIONE FINALE
# ======================================================
st.markdown("---")
if final_lyrics:
    if is_valid(final_lyrics):
        st.success("🎉 OUTPUT FINALE VALIDO")
    else:
        st.error("❌ Testo NON valido (manca [verse] o [chorus])")

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<hr>
<div style='text-align:center;color:#666;'>
<b>Senorix AI</b><br>
Pipeline professionale per testi musicali
</div>
""", unsafe_allow_html=True)

