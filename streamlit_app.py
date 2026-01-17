import streamlit as st
from gradio_client import Client, file as gr_file
import tempfile
from pathlib import Path
import time

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Senorix AI — Song Generation",
    layout="centered"
)

# ===============================
# CSS
# ===============================
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-radius: 12px;
    margin-bottom: 30px;
}
.stButton>button {
    width: 100%;
    background-color: #667eea;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 14px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
<h1>🎵 Senorix AI — Song Generation</h1>
<p>Lyrics con LLaMA-2 & Musica con Tencent</p>
</div>
""", unsafe_allow_html=True)

# ===============================
# SIDEBAR
# ===============================
st.sidebar.header("⚙️ Configurazione")

lyrics_mode = st.sidebar.radio(
    "🎤 Generazione parole",
    ["🤖 Automatica (LLaMA-2)", "✍️ Manuale"],
    index=0
)

st.sidebar.markdown("---")

space_url_song = st.sidebar.text_input(
    "🎹 Tencent Song Space URL",
    value="https://tencent-songgeneration.hf.space/"
)

api_name_song = st.sidebar.text_input(
    "Endpoint musica",
    value="/generate_song"
)

# ===============================
# FUNCTIONS
# ===============================

def generate_lyrics_with_llama(description: str) -> str:
    """Genera lyrics con LLaMA-2-13B-Chat"""

    st.info("🔄 Connessione a LLaMA-2-13B-Chat...")
    client = Client("huggingface-projects/llama-2-13b-chat")

    system_prompt = (
        "You are a professional songwriter. "
        "You write emotional, singable song lyrics."
    )

    user_prompt = f"""
Write song lyrics based on this theme:

"{description}"

STRICT RULES:
- Use ONLY these tags: [verse], [chorus], [bridge]
- Start with [verse] or [chorus]
- At least 2 [verse] and 1 [chorus]
- 2–6 lines per section
- NO explanations, NO titles, ONLY lyrics
"""

    try:
        result = client.predict(
            message=user_prompt,
            system_prompt=system_prompt,
            max_new_tokens=700,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1.1,
            api_name="/chat"
        )
    except Exception as e:
        st.error(f"❌ Errore LLaMA-2: {e}")
        return default_lyrics()

    if isinstance(result, list) and result:
        text = result[0]
    else:
        text = str(result)

    if "[verse]" not in text.lower():
        st.warning("⚠️ Output non valido, uso template")
        return default_lyrics()

    st.success("✅ Parole generate con successo")
    return text.strip()


def default_lyrics() -> str:
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


def clean_lyrics(text: str) -> str:
    return text.replace("```", "").strip()

# ===============================
# MAIN UI
# ===============================
st.subheader("📝 Descrizione della canzone")

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
        "✍️ Inserisci le tue parole",
        height=300
    )

st.markdown("---")
generate_button = st.button("🎛️ GENERA CANZONE")

# ===============================
# PIPELINE
# ===============================
if generate_button:
    if not description.strip():
        st.error("❌ Inserisci una descrizione")
        st.stop()

    # STEP 1 — LYRICS
    st.markdown("## 🎼 Step 1 — Parole")

    if lyrics_mode == "✍️ Manuale":
        lyrics_text = manual_lyrics
    else:
        with st.spinner("Generazione parole..."):
            lyrics_text = generate_lyrics_with_llama(description)

    lyrics_text = clean_lyrics(lyrics_text)
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

    with st.spinner("🎶 Generazione musica..."):
        song_result = client_song.predict(
            lyric=lyrics_text,
            description=description,
            prompt_audio=prompt_audio,
            api_name=api_name_song
        )

    # STEP 3 — RESULT
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

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#666;'>"
    "🎵 <b>Senorix AI</b> — LLaMA-2 + Tencent Song Generation"
    "</div>",
    unsafe_allow_html=True
)

