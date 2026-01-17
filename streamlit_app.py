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
# CUSTOM CSS
# ===============================
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 30px;
}
.stButton>button {
    width: 100%;
    background-color: #667eea;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 15px;
    font-size: 16px;
}
.stButton>button:hover {
    background-color: #764ba2;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-header">'
    '<h1>🎵 Senorix AI — Song Generation</h1>'
    '<p>Génération de chansons avec Intelligence Artificielle</p>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("""
### Comment ça marche ?
1. **Génération des paroles** : Qwen3-VL crée les paroles
2. **Génération de la musique** : Tencent transforme les paroles en chanson
""")

# ===============================
# SIDEBAR
# ===============================
st.sidebar.header("⚙️ Configuration")

lyrics_mode = st.sidebar.radio(
    "🎤 Génération des paroles",
    ["🤖 Automatique (Qwen3-VL)", "✍️ Manuel"],
    index=0
)

st.sidebar.markdown("---")

space_url_song = st.sidebar.text_input(
    "🎹 Tencent Song Space URL",
    value="https://tencent-songgeneration.hf.space/"
)

api_name_song = st.sidebar.text_input(
    "Endpoint API",
    value="/generate_song"
)

# ===============================
# FUNCTIONS
# ===============================

def generate_lyrics_with_qwen(description: str) -> str:
    """
    Génère les paroles avec Qwen3-VL-Demo
    CORRECTION CLÉ : utilisation EXCLUSIVE de /chat
    """

    st.info("🔄 Connexion à Qwen3-VL-Demo...")
    client = Client("Qwen/Qwen3-VL-Demo")

    prompt = f"""
Tu es un parolier professionnel expert.

TÂCHE :
Génère des paroles de chanson à partir de cette description :

\"{description}\"

RÈGLES STRICTES :
- Utilise UNIQUEMENT [verse], [chorus], [bridge]
- Commence par [verse] ou [chorus]
- Minimum 2 [verse] et 1 [chorus]
- 2 à 6 lignes par section
- AUCUN autre texte

Génère maintenant les paroles :
"""

    st.info("🤖 Génération des paroles...")
    try:
        result = client.predict(
            message=prompt,
            api_name="/chat"
        )
    except Exception as e:
        st.error(f"❌ Erreur Qwen3-VL : {e}")
        return generate_default_lyrics(description)

    # Extraction texte
    if isinstance(result, list) and result:
        text = result[0]
    else:
        text = str(result)

    if "[verse]" not in text.lower():
        st.warning("⚠️ Sortie invalide, utilisation du template.")
        return generate_default_lyrics(description)

    st.success("✅ Paroles générées avec succès")
    return text.strip()


def generate_default_lyrics(description: str) -> str:
    """Template de secours"""
    return """[verse]
Je marche seul dans la nuit
Cherchant encore ton regard
Le silence me poursuit
Comme un écho trop tard

[chorus]
Je garde l'espoir en moi
Même quand tout s'effondre
Je sais qu'un jour quelque part
La lumière va répondre

[verse]
Chaque pas me rapproche
D'un futur à écrire
Même quand le ciel est sombre
Je choisis de sourire

[chorus]
Je garde l'espoir en moi
Même quand tout s'effondre
Je sais qu'un jour quelque part
La lumière va répondre
"""


def clean_lyrics(text: str) -> str:
    """Nettoyage basique"""
    return text.replace("```", "").strip()

# ===============================
# MAIN UI
# ===============================

st.subheader("📝 Description de la chanson")

description = st.text_area(
    "Décrivez l'ambiance et le thème",
    value="Une chanson pop moderne sur l'espoir et la persévérance",
    height=120
)

uploaded_audio = st.file_uploader(
    "🎧 Audio de référence (optionnel)",
    type=["mp3", "wav", "ogg"]
)

if lyrics_mode == "✍️ Manuel":
    manual_lyrics = st.text_area(
        "✍️ Vos paroles",
        height=300,
        value="""[verse]
Je marche seul dans la nuit
Ton souvenir me poursuit

[chorus]
Oh reviens vers moi
Le monde est froid sans toi"""
    )

st.markdown("---")

generate_button = st.button("🎛️ GÉNÉRER LA CHANSON")

# ===============================
# WORKFLOW
# ===============================
if generate_button:
    if not description.strip():
        st.error("❌ Description requise")
        st.stop()

    # STEP 1 – LYRICS
    st.markdown("## 🎼 Étape 1 : Paroles")

    if lyrics_mode == "✍️ Manuel":
        lyrics_text = manual_lyrics
    else:
        with st.spinner("Génération des paroles..."):
            lyrics_text = generate_lyrics_with_qwen(description)

    lyrics_text = clean_lyrics(lyrics_text)

    st.code(lyrics_text)

    # STEP 2 – MUSIC
    st.markdown("## 🎵 Étape 2 : Génération musicale")

    client_song = Client(space_url_song)

    prompt_audio = None
    if uploaded_audio:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_audio.name).suffix)
        tmp.write(uploaded_audio.getbuffer())
        tmp.close()
        prompt_audio = gr_file(tmp.name)

    with st.spinner("🎶 Génération en cours..."):
        try:
            song_result = client_song.predict(
                lyric=lyrics_text,
                description=description,
                prompt_audio=prompt_audio,
                api_name=api_name_song
            )
        except Exception as e:
            st.error(f"❌ Erreur génération musicale : {e}")
            st.stop()

    # STEP 3 – RESULT
    st.markdown("## 🎧 Résultat")

    audio_path = None
    if isinstance(song_result, (list, tuple)):
        audio_path = song_result[0]
    elif isinstance(song_result, str):
        audio_path = song_result

    if audio_path:
        st.audio(audio_path)
        with open(audio_path, "rb") as f:
            st.download_button(
                "⬇️ Télécharger",
                f.read(),
                file_name="senorix_song.wav",
                mime="audio/wav"
            )
    else:
        st.warning("⚠️ Aucun audio retourné")

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#666;'>"
    "🎵 <b>Senorix AI</b> — Qwen3-VL & Tencent Song Generation"
    "</div>",
    unsafe_allow_html=True
)

