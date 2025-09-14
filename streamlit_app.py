import streamlit as st
from gradio_client import Client, file as gr_file
import tempfile
from pathlib import Path

st.set_page_config(page_title="Senorix AI — Song Generation", layout="centered")

st.title("🎵 Senorix AI — Song Generation")
st.markdown(
    "Une interface simple pour appeler le modèle de génération de chansons via le Gradio Space.\n\n"
    "Colle tes paroles (ou utilise le template), choisis des réglages, puis clique sur **Générer**."
)

# --- Sidebar / settings ---
st.sidebar.header("Paramètres API")
space_url = st.sidebar.text_input(
    "Gradio Space URL",
    value="https://tencent-songgeneration.hf.space/",
    help="URL du Space Gradio/HF. Par défaut celle fournie."
)
api_name = st.sidebar.text_input("Endpoint", value="/generate_song")

st.sidebar.markdown("---")
st.sidebar.header("Options de génération")
default_genre = st.sidebar.selectbox("Genre par défaut", ["Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Folk"])

# --- Main form ---
with st.form(key="gen_form"):
    st.subheader("Paroles (lyric)")
    lyric = st.text_area(
        "Paroles",
        value="""[intro-short]

[verse]
夜晚的街灯闪烁
我漫步在熟悉的角落
回忆像潮水般涌来
你的笑容如此清晰
在心头无法抹去
那些曾经的甜蜜
如今只剩我独自回忆

[verse]
手机屏幕亮起
是你发来的消息
简单的几个字
却让我泪流满面
曾经的拥抱温暖
如今却变得遥远
我多想回到从前
重新拥有你的陪伴

[chorus]
回忆的温度还在
你却已不在
我的心被爱填满
却又被思念刺痛
音乐的节奏奏响
我的心却在流浪
没有你的日子
我该如何继续向前

[outro-short]""",
        height=260
    )

    description = st.text_input("Description (optionnelle)", value="")
    uploaded_audio = st.file_uploader(
        "Prompt audio (optionnel) — mp3/wav",
        type=["mp3", "wav", "ogg"],
        help="Envoyer un court extrait audio si le modèle supporte 'prompt_audio'."
    )

    genre = st.selectbox("Genre", options=["Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Folk", "Other"], index=0)
    cfg_coef = st.number_input("cfg_coef", value=1.5, step=0.1, format="%.2f")
    temperature = st.number_input("temperature", value=0.9, step=0.05, format="%.2f")
    top_k = st.number_input("top_k", value=50, step=1, min_value=1)

    submit = st.form_submit_button("🎛️ Générer la chanson")

# --- Predict / call API ---
if submit:
    if not lyric.strip():
        st.warning("Veuillez fournir des paroles (lyric).")
    else:
        client = Client(space_url)
        st.info("Envoi de la requête au modèle...")
        with st.spinner("Génération en cours… cela peut prendre du temps"):
            try:
                # Préparer prompt_audio si présent
                prompt_audio_arg = None
                if uploaded_audio is not None:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_audio.name).suffix)
                    tmp.write(uploaded_audio.getbuffer())
                    tmp.flush()
                    tmp.close()
                    prompt_audio_arg = gr_file(tmp.name)

                # Appel predict
                result = client.predict(
                    lyric=lyric,
                    description=description or None,
                    prompt_audio=prompt_audio_arg,
                    genre=genre,
                    cfg_coef=float(cfg_coef),
                    temperature=float(temperature),
                    top_k=int(top_k),
                    api_name=api_name
                )

                st.success("Réponse reçue du modèle.")
                st.subheader("Réponse brute")
                st.write(result)

                # ---- Extraction du fichier audio ----
                audio_found = False

                if isinstance(result, (list, tuple)) and len(result) > 0:
                    first_item = result[0]
                    if isinstance(first_item, str) and first_item.startswith("/tmp/gradio"):
                        try:
                            local_path = client.download(first_item)  # téléchargement du wav
                            st.audio(local_path)

                            with open(local_path, "rb") as f:
                                st.download_button(
                                    "⬇️ Télécharger l'audio",
                                    data=f,
                                    file_name="generated_song.wav",
                                    mime="audio/wav"
                                )
                            audio_found = True
                        except Exception as e:
                            st.error(f"Impossible de télécharger le fichier audio : {e}")

                if not audio_found:
                    st.info("Aucun fichier audio exploitable détecté dans la réponse.")

            except Exception as e:
                st.error("Erreur lors de l'appel au Space Gradio :")
                st.exception(e)
