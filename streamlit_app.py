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
    layout="centered"
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
<h1>🎵 Senorix AI — Song Generation</h1>
<p>Lyrics AI + Music Generation</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.header("⚙️ Configurazione")

lyrics_mode = st.sidebar.radio(
    "🎤 Generazione parole",
    ["🤖 Automatica (LLaMA-2)", "✍️ Manuale"],
    index=0
)

st.sidebar.markdown("---")

space_url_song = st.sidebar.text_input(
    "🎹 Tencent Song Space",
    value="https://tencent-songgeneration.hf.space/"
)

api_name_song = st.sidebar.text_input(
    "🎵 Endpoint musica",
    value="/generate_song"
)

# ======================================================
# LYRICS UTILS
# ======================================================

def normalize_lyrics(text: str) -> str:
    """
    Rende SEMPRE valido l'output dell'AI se possibile
    """
    if not text:
        return ""

    # rimuove markdown
    text = text.replace("```", "").strip()

    # rimuove qualsiasi testo prima del primo tag
    match = re.search(r'\[(verse|chorus|bridge)\]', text, re.I)
    if match:
        text = text[match.start():]

    # normalizza i tag
    text = re.sub(r'\[verse\]', '[verse]', text, flags=re.I)
    text = re.sub(r'\[chorus\]', '[chorus]', text, flags=re.I)
    text = re.sub(r'\[bridge\]', '[bridge]', text, flags=re.I)

    return text.strip()


def is_valid_lyrics(text: str) -> bool:
    """
    Valido se contiene almeno verse + chorus
    """
    t = text.lower()
    return "[verse]" in t and "[chorus]" in t


def default_lyrics() -> str:
    """Fallback sicuro"""
    return """[verse]
Attraverso mari senza nome
Con una valigia di speranza
Ogni passo rompe il silenzio
Ogni sogno chiede una chance

[chorus]
Siamo liberi di camminare
Senza catene né confini
Ogni popolo è un orizzonte
Ogni voce un nuovo inizio

[verse]
Lingue diverse, stessi battiti
Occhi pieni di verità
Nel viaggio nasce il futuro
Nell'incontro la libertà

[chorus]
Siamo liberi di camminare
Senza catene né confini
Ogni popolo è un orizzonte
Ogni voce un nuovo inizio
"""

# ======================================================
# AI GENERATION
# ======================================================

def generate_lyrics_with_llama(description: str) -> str:
    """
    Generazione ROBUSTA con LLaMA-2
    """
    st.info("🔄 Connessione a LLaMA-2-13B-Chat…")

    client = Client("huggingface-projects/llama-2-13b-chat")

    system_prompt = (
        "You are a professional songwriter.\n"
        "You must ONLY output song lyrics.\n"
        "You must NEVER explain.\n"
        "You must start immediately with [verse] or [chorus]."
    )

    user_prompt = f"""
Write a song about:

\"{description}\"

STRICT RULES:
- Output ONLY lyrics
- Use ONLY: [verse], [chorus], [bridge]
- Start IMMEDIATELY with a tag
- No titles, no comments
- 2–6 lines per section
"""

    try:
        raw = client.predict(
            message=user_prompt,
            system_prompt=system_prompt,
            max_new_tokens=700,
            temperature=0.65,
            top_p=0.9,
            repetition_penalty=1.1,
            api_name="/chat"
        )
    except Exception as e:
        st.error(f"❌ Errore AI: {e}")
        return default_lyrics()

    # estrazione testo
    if isinstance(raw, list):
        raw_text = raw[0]
    else:
        raw_text = str(raw)

    # NORMALIZZAZIONE
    cleaned = normalize_lyrics(raw_text)

    # VALIDAZIONE
    if not is_valid_lyrics(cleaned):
        st.warning("⚠️ Output AI non strutturato, uso fallback")
        return default_lyrics()

    st.success("✅ Parole generate correttamente")
    return cleaned


# ======================================================
# MAIN UI
# ======================================================

st.subheader("📝 Descrizione canzone")

description = st.text_area(
    "Tema, emozione, messaggio",
    value="Una canzone sull'immigrazione e sulla libertà di esplorare nuovi popoli",
    height=120
)

uploaded_audio = st.file_uploader(
    "🎧 Audio di riferimento (opzionale)",
    type=["mp3", "wav", "ogg"]
)

if lyrics_mode == "✍️ Manuale":
    manual_lyrics = st.text_area(
        "✍️ Inserisci le parole",
        height=300
    )

st.markdown("---")
generate_button = st.button("🎛️ GENERA CANZONE")

# ======================================================
# PIPELINE
# ======================================================

if generate_button:
    if not description.strip():
        st.error("❌ Inserisci una descrizione")
        st.stop()

    # STEP 1 — LYRICS
    st.markdown("## 🎼 Step 1 — Parole")

    if lyrics_mode == "✍️ Manuale":
        lyrics_text = manual_lyrics
    else:
        with st.spinner("Generazione parole…"):
            lyrics_text = generate_lyrics_with_llama(description)

    st.code(lyrics_text)

    # STEP 2 — MUSIC
    st.markdown("## 🎵 Step 2 — Musica")

    client_song = Client(space_url_song)

    prompt_audio = None
    if uploaded_audio:
        tmp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(uploaded_audio.name).suffix
        )
        tmp.write(uploaded_audio.getbuffer())
        tmp.close()
        prompt_audio = gr_file(tmp.name)

    with st.spinner("🎶 Generazione musica…"):
        song_result = client_song.predict(
            lyric=lyrics_text,
            description=description,
            prompt_audio=prompt_audio,
            api_name=api_name_song
        )

    # STEP 3 — OUTPUT
    st.markdown("## 🎧 Risultato")

    audio_path = None
    if isinstance(song_result, (list, tuple)):
        audio_path = song_result[0]
    elif isinstance(song_result, str):
        audio_path = song_result

    if audio_path:
        st.audio(audio_path)
        with open(audio_path, "rb") as f:
            st.download_button(
                "⬇️ Scarica canzone",
                f.read(),
                file_name="senorix_song.wav",
                mime="audio/wav"
            )
    else:
        st.warning("⚠️ Nessun audio restituito")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#666;'>"
    "🎵 <b>Senorix AI</b> — LLaMA-2 + Tencent Song Generation"
    "</div>",
    unsafe_allow_html=True
)

