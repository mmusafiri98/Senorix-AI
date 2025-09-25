import streamlit as st
from gradio_client import Client, file as gr_file
import tempfile
from pathlib import Path

st.set_page_config(page_title="Senorix AI — Song Generation", layout="centered")

st.title("🎵 Senorix AI — Song Generation")
st.markdown(
    "Cette app utilise **deux modèles** :\n"
    "1. `akhaliq/Apertus-8B-Instruct-2509` pour générer automatiquement les paroles.\n"
    "2. `tencent-songgeneration` pour transformer ces paroles en chanson chantée."
)

# --- Sidebar / settings ---
st.sidebar.header("Paramètres API chanson")
space_url_song = st.sidebar.text_input(
    "Gradio Space URL (song model)",
    value="https://tencent-songgeneration.hf.space/",
    help="URL du Space Gradio/HF pour la génération de musique."
)
api_name_song = st.sidebar.text_input("Endpoint chanson", value="/generate_song")

st.sidebar.markdown("---")
st.sidebar.header("Options de génération (chanson)")
genre = st.sidebar.selectbox("Genre", ["Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Folk", "Other"], index=0)
cfg_coef = st.sidebar.number_input("cfg_coef", value=1.5, step=0.1, format="%.2f")
temperature = st.sidebar.number_input("temperature", value=0.9, step=0.05, format="%.2f")
top_k = st.sidebar.number_input("top_k", value=50, step=1, min_value=1)

# --- Main form ---
with st.form(key="gen_form"):
    st.subheader("Description de la chanson")
    description = st.text_area(
        "Décris l’ambiance, le thème ou les émotions de la chanson (en français, anglais ou autre).",
        value="Une chanson nostalgique sur l’amour perdu, style pop moderne.",
        height=150
    )

    uploaded_audio = st.file_uploader(
        "Prompt audio (optionnel, mp3/wav/ogg)",
        type=["mp3", "wav", "ogg"],
        help="Un court extrait audio si supporté par le modèle."
    )

    submit = st.form_submit_button("🎛️ Générer la chanson")

# --- Workflow : description → lyrics → chanson ---
if submit:
    if not description.strip():
        st.warning("Veuillez fournir une description.")
    else:
        try:
            st.info("1️⃣ Génération des paroles à partir de la description...")

            # Client du modèle LLM (Apertus-8B)
            client_llm = Client("akhaliq/Apertus-8B-Instruct-2509")

            # Prompt amélioré pour forcer le bon format
            prompt = f"""Tu es un parolier.
Ta tâche est de générer des paroles de chanson à partir de cette description :
Description : {description}

⚠️ Les règles sont strictes :
- La chanson DOIT être structurée avec les tags suivants uniquement :
  [intro-short], [intro-medium], [intro-long], [verse], [chorus], [bridge], 
  [outro-short], [outro-medium], [outro-long], [inst-short], [inst-medium], [inst-long], [silence]
- Commence OBLIGATOIREMENT par un tag valide (par exemple [intro-short] ou [verse]).
- Chaque section doit être suivie de 1 à 6 lignes de texte.
- Utilise plusieurs sections ([verse], [chorus], etc.).
- N’écris rien d’autre que les paroles.

Exemple correct :

[intro-short]
La nuit tombe doucement
Les lumières brillent dans le vent

[verse]
Je marche seul dans la ville
Ton souvenir reste fragile

[chorus]
Oh mon cœur, reviens à moi
Sans toi, je ne vis pas
"""

            # Génération des paroles par le LLM
            lyrics_result = client_llm.predict(
                message=prompt,
                api_name="/chat"
            )

            lyrics_text = lyrics_result if isinstance(lyrics_result, str) else str(lyrics_result)

            # Post-traitement pour forcer un tag valide au début
            valid_tags = ["[verse]", "[chorus]", "[bridge]", "[intro-short]", "[intro-medium]", "[intro-long]",
                          "[outro-short]", "[outro-medium]", "[outro-long]", "[inst-short]", "[inst-medium]", "[inst-long]", "[silence]"]

            if not any(lyrics_text.strip().startswith(tag) for tag in valid_tags):
                lyrics_text = "[verse]\n" + lyrics_text.strip()

            st.success("✅ Paroles générées par le LLM")
            st.subheader("📜 Paroles générées")
            st.text_area("Paroles", lyrics_text, height=260)

            st.info("2️⃣ Génération de la chanson à partir des paroles...")

            # Client du modèle de chanson
            client_song = Client(space_url_song)

            # Préparer prompt audio si présent
            prompt_audio_arg = None
            if uploaded_audio is not None:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_audio.name).suffix)
                tmp.write(uploaded_audio.getbuffer())
                tmp.flush()
                tmp.close()
                prompt_audio_arg = gr_file(tmp.name)

            # Appel du modèle de chanson
            song_result = client_song.predict(
                lyric=lyrics_text,
                description=description,
                prompt_audio=prompt_audio_arg,
                genre=genre,
                cfg_coef=float(cfg_coef),
                temperature=float(temperature),
                top_k=int(top_k),
                api_name=api_name_song
            )

            st.success("✅ Réponse du modèle chanson")
            st.subheader("Réponse brute (debug)")
            st.write(song_result)

            # Gestion de l’audio
            audio_found = False
            if isinstance(song_result, (list, tuple)) and len(song_result) > 0:
                audio_path = song_result[0]
                if isinstance(audio_path, str) and audio_path.endswith(".wav"):
                    st.audio(audio_path)
                    with open(audio_path, "rb") as f:
                        st.download_button(
                            "⬇️ Télécharger l'audio",
                            data=f.read(),
                            file_name="generated_song.wav",
                            mime="audio/wav"
                        )
                    audio_found = True

            if not audio_found:
                st.info("ℹ️ Aucun fichier audio exploitable détecté.")

        except Exception as e:
            st.error("❌ Erreur pendant le workflow :")
            st.exception(e)

