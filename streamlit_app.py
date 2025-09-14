import streamlit as st
from gradio_client import Client, file as gr_file
import json
import base64
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
api_name = st.sidebar.text_input("/generate endpoint", value="/generate_song")

st.sidebar.markdown("---")
st.sidebar.header("Options de génération")
default_genre = st.sidebar.selectbox("Genre par défaut", ["Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Folk"])
st.sidebar.write("Astuce : ajuste `cfg_coef`, `temperature` et `top_k` pour plus/moins de créativité.")

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
        with st.spinner("Génération en cours… cela peut prendre quelques secondes"):
            try:
                # Préparer prompt_audio si présent
                prompt_audio_arg = None
                if uploaded_audio is not None:
                    # Sauvegarder temporairement et utiliser gradio_client.file
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
                # Afficher le résultat brut (utile pour debug)
                st.subheader("Réponse brute")
                try:
                    st.json(result)
                except Exception:
                    st.write(result)

                # Tenter d'extraire une sortie audio si existante
                # Le format renvoyé par Gradio Space peut être :
                # - une chaîne / dictionnaire contenant un chemin/url
                # - un blob audio encodé (base64) ou un chemin côté serveur
                audio_found = False

                # Si c'est un dict, parcourir à la recherche de clé plausible
                if isinstance(result, dict):
                    # Cherche clés contenant "audio", "wav", "audio_path", "output_audio"
                    for k, v in result.items():
                        lk = k.lower()
                        if "audio" in lk or "wav" in lk or "path" in lk:
                            if isinstance(v, str) and v.strip():
                                # si c'est une URL (commence par http) => afficher le lien
                                if v.startswith("http"):
                                    st.markdown(f"**Audio URL ({k}) :** {v}")
                                    st.audio(v)
                                    audio_found = True
                                    break
                                # si c'est base64 data:audio/...
                                if v.startswith("data:audio"):
                                    # extraire base64 portion
                                    parts = v.split(",", 1)
                                    if len(parts) == 2:
                                        b64 = parts[1]
                                        try:
                                            data = base64.b64decode(b64)
                                            st.audio(data)
                                            audio_found = True
                                            break
                                        except Exception:
                                            pass
                                # si c'est un chemin local côté Space (ex: /tmp/...), on ne peut pas y accéder directement.
                                # afficher le chemin pour debug
                                st.write(f"Audio (clé `{k}`) : {v}")
                                audio_found = True
                                # try to show if it's a relative URL
                                if v.startswith("/"):
                                    full = space_url.rstrip("/") + v
                                    st.markdown(f"Possible URL: {full}")
                                    try:
                                        st.audio(full)
                                    except Exception:
                                        pass
                                break

                # si résultat est une liste, parcourir
                if not audio_found and isinstance(result, (list, tuple)):
                    for item in result:
                        if isinstance(item, str) and item.startswith("http"):
                            st.audio(item)
                            audio_found = True
                            break
                        if isinstance(item, dict):
                            for k, v in item.items():
                                if isinstance(v, str) and v.startswith("http"):
                                    st.audio(v)
                                    audio_found = True
                                    break
                        if audio_found:
                            break

                # si rien d'audio trouvé, afficher message
                if not audio_found:
                    st.info("Aucun fichier audio détecté dans la réponse. Vérifie le contenu JSON ci-dessus.")

            except Exception as e:
                st.error("Erreur lors de l'appel au Space Gradio :")
                st.exception(e)
