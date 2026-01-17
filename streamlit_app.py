import streamlit as st
from gradio_client import Client, file as gr_file
import tempfile
from pathlib import Path
import time

st.set_page_config(page_title="Senorix AI — Song Generation", layout="centered")

# Custom CSS
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

st.markdown('<div class="main-header"><h1>🎵 Senorix AI — Song Generation</h1><p>Génération de chansons avec Intelligence Artificielle</p></div>', unsafe_allow_html=True)

st.markdown(
    """
    ### Comment ça marche ?
    1. **Génération des paroles** : Qwen3-VL crée les paroles à partir de votre description
    2. **Génération de la musique** : Le modèle Tencent transforme ces paroles en chanson chantée
    """
)

# --- Sidebar Configuration ---
st.sidebar.header("⚙️ Configuration")

st.sidebar.markdown("### 🎤 Mode de Génération des Paroles")
lyrics_mode = st.sidebar.radio(
    "Comment générer les paroles ?",
    ["🤖 Automatique (Qwen3-VL)", "✍️ Manuel"],
    index=0,
    help="Automatique: Qwen3-VL génère les paroles. Manuel: vous les écrivez vous-même."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎹 Modèle de Génération Musicale")
space_url_song = st.sidebar.text_input(
    "Gradio Space URL",
    value="https://tencent-songgeneration.hf.space/",
    help="URL du Space Gradio pour la génération de musique."
)
api_name_song = st.sidebar.text_input("Endpoint API", value="/generate_song")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎚️ Paramètres de Génération")
genre = st.sidebar.selectbox(
    "Genre Musical",
    ["Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Folk", "Jazz", "Classical", "Country", "Other"],
    index=0
)

# --- Functions ---

def generate_lyrics_with_qwen(description):
    """Génère des paroles avec Qwen3-VL-Demo"""
    
    try:
        st.info("🔄 Connexion à Qwen3-VL-Demo...")
        client = Client("Qwen/Qwen3-VL-Demo")
        
        # Prompt optimisé pour Qwen3-VL
        prompt = f"""Tu es un parolier professionnel expert.

TÂCHE : Génère des paroles de chanson basées sur cette description :
"{description}"

RÈGLES STRICTES ET OBLIGATOIRES :
1. Utilise UNIQUEMENT ces balises : [verse], [chorus], [bridge]
2. Commence TOUJOURS par [verse] ou [chorus]
3. N'utilise JAMAIS : [intro], [inst], [outro] ou leurs variantes
4. Chaque section doit contenir 2 à 6 lignes de paroles
5. Structure minimale : au moins 2 [verse] et 1 [chorus]
6. Ne génère RIEN d'autre que les paroles avec balises

EXEMPLE DE FORMAT CORRECT :

[verse]
Je marche seul dans la nuit étoilée
Ton souvenir brille dans ma vie
Les ombres dansent sur le pavé
Mais tu n'es plus là près de moi

[chorus]
Oh mon cœur reviens à moi
Sans toi le monde est si froid
Je cherche ton regard partout
Mais tu es loin de nous

[verse]
Les rues résonnent de ton absence
Je garde en moi notre romance
Chaque coin me rappelle ton visage
Un éternel et doux mirage

[chorus]
Oh mon cœur reviens à moi
Sans toi le monde est si froid
Je cherche ton regard partout
Mais tu es loin de nous

[bridge]
Peut-être qu'un jour nos chemins
Se croiseront à nouveau demain
Et je pourrai enfin te dire
Combien tu me fais souffrir

[chorus]
Oh mon cœur reviens à moi
Sans toi le monde est si froid
Je cherche ton regard partout
Mais tu es loin de nous

MAINTENANT, génère les paroles (UNIQUEMENT les paroles avec balises, rien d'autre) :"""

        st.info("🤖 Génération des paroles avec Qwen3-VL...")
        
        # Première tentative : avec apply_state_change
        try:
            # Initialiser l'état si nécessaire
            client.predict(api_name="/apply_state_change")
            
            # Générer les paroles
            lyrics_result = client.predict(
                text_input=prompt,
                api_name="/submit_message"
            )
            
        except Exception as e1:
            st.warning(f"⚠️ Méthode 1 échouée, tentative alternative...")
            
            # Deuxième tentative : méthode alternative
            try:
                lyrics_result = client.predict(
                    message=prompt,
                    api_name="/chat"
                )
            except Exception as e2:
                st.warning(f"⚠️ Méthode 2 échouée, tentative basique...")
                
                # Troisième tentative : appel direct
                lyrics_result = client.predict(
                    prompt,
                    api_name="/predict"
                )
        
        # Extraction du texte
        if isinstance(lyrics_result, (list, tuple)):
            lyrics_text = lyrics_result[0] if len(lyrics_result) > 0 else ""
        elif isinstance(lyrics_result, dict):
            lyrics_text = lyrics_result.get('text') or lyrics_result.get('output') or str(lyrics_result)
        else:
            lyrics_text = str(lyrics_result)
        
        # Vérification de la qualité
        if lyrics_text and len(lyrics_text.strip()) > 50 and "[verse]" in lyrics_text.lower():
            st.success("✅ Paroles générées avec succès par Qwen3-VL")
            return lyrics_text
        else:
            st.warning("⚠️ Résultat incomplet, utilisation d'un template...")
            return generate_default_lyrics(description)
            
    except Exception as e:
        st.error(f"❌ Erreur avec Qwen3-VL : {str(e)[:150]}")
        st.info("💡 Utilisation d'un template par défaut...")
        return generate_default_lyrics(description)


def generate_default_lyrics(description):
    """Génère des paroles par défaut basées sur la description"""
    
    keywords = description.lower()
    
    if any(word in keywords for word in ["amour", "love", "cœur", "heart"]):
        theme = "amour"
    elif any(word in keywords for word in ["triste", "sad", "mélancolie", "nostalgie"]):
        theme = "tristesse"
    elif any(word in keywords for word in ["joie", "happy", "heureux", "fête"]):
        theme = "joie"
    else:
        theme = "vie"
    
    templates = {
        "amour": """[verse]
Mon cœur bat pour toi chaque jour
Ton sourire illumine mes nuits
Dans tes bras j'ai trouvé l'amour
Une histoire qui ne finit pas ici

[chorus]
Tu es ma lumière dans le noir
Mon étoile qui brille le soir
Avec toi je peux tout affronter
Notre amour ne peut pas s'arrêter

[verse]
Chaque moment passé à tes côtés
Est un trésor que je garde précieusement
Nos rires nos joies nos vérités
Construisent notre histoire lentement

[chorus]
Tu es ma lumière dans le noir
Mon étoile qui brille le soir
Avec toi je peux tout affronter
Notre amour ne peut pas s'arrêter

[bridge]
Et même si le temps passe
Même si tout change autour
Notre amour jamais ne se lasse
C'est un éternel retour

[chorus]
Tu es ma lumière dans le noir
Mon étoile qui brille le soir
Avec toi je peux tout affronter
Notre amour ne peut pas s'arrêter""",

        "tristesse": """[verse]
Les jours passent sans couleur
Depuis que tu es parti loin
Mon âme pleure en silence
Cherchant ton ombre en vain

[chorus]
Je marche seul dans la nuit
Ton absence me poursuit
Les souvenirs me hantent encore
Dans ce monde où tu n'es plus là

[verse]
Les rues vides résonnent
De ton rire disparu
Chaque coin me rappelle
Les moments qu'on a vécu

[chorus]
Je marche seul dans la nuit
Ton absence me poursuit
Les souvenirs me hantent encore
Dans ce monde où tu n'es plus là

[bridge]
Peut-être qu'un jour la douleur
S'effacera de mon cœur
Mais pour l'instant je reste
Prisonnier de ton absence

[chorus]
Je marche seul dans la nuit
Ton absence me poursuit
Les souvenirs me hantent encore
Dans ce monde où tu n'es plus là""",

        "joie": """[verse]
Le soleil brille aujourd'hui
La vie est belle et colorée
Mon cœur danse de joie
Prêt à tout célébrer

[chorus]
Je vis je ris je chante
Chaque instant est précieux
La vie est éclatante
Sous ce ciel merveilleux

[verse]
Les oiseaux chantent pour moi
Le vent souffle la liberté
Aujourd'hui c'est ma voie
De profiter sans compter

[chorus]
Je vis je ris je chante
Chaque instant est précieux
La vie est éclatante
Sous ce ciel merveilleux

[bridge]
Rien ne peut m'arrêter
Rien ne peut me briser
Je suis libre et vivant
Porté par le moment présent

[chorus]
Je vis je ris je chante
Chaque instant est précieux
La vie est éclatante
Sous ce ciel merveilleux""",

        "vie": """[verse]
La vie est un voyage sans fin
Chaque jour apporte son mystère
On marche sur un long chemin
Vers un avenir à faire

[chorus]
Je continue d'avancer
Sans savoir où je vais
Mais je garde la foi
Que demain sera mieux

[verse]
Les épreuves nous rendent forts
Les joies nous font grandir
Entre ombre et lumière encore
On apprend à vivre et à rire

[chorus]
Je continue d'avancer
Sans savoir où je vais
Mais je garde la foi
Que demain sera mieux

[bridge]
Chaque pas compte dans cette danse
Chaque choix dessine notre chance
La vie c'est maintenant
Vivons-la pleinement

[chorus]
Je continue d'avancer
Sans savoir où je vais
Mais je garde la foi
Que demain sera mieux"""
    }
    
    return templates.get(theme, templates["vie"])


def clean_lyrics(lyrics_text):
    """Nettoie et valide les paroles"""
    
    lyrics_text = lyrics_text.replace("```", "").strip()
    
    lines = lyrics_text.splitlines()
    cleaned_lines = []
    
    valid_tags = ["[verse]", "[chorus]", "[bridge]"]
    forbidden_tags = [
        "[intro]", "[intro-short]", "[intro-medium]", "[intro-long]",
        "[inst]", "[inst-short]", "[inst-medium]", "[inst-long]",
        "[outro]", "[outro-short]", "[outro-medium]", "[outro-long]",
        "[silence]"
    ]
    
    skip_section = False
    
    for line in lines:
        line_stripped = line.strip().lower()
        
        if not cleaned_lines and not line_stripped:
            continue
        
        if any(line_stripped.startswith(tag) for tag in forbidden_tags):
            skip_section = True
            continue
        
        if line_stripped.startswith("[") and line_stripped.endswith("]"):
            if any(line_stripped.startswith(tag) for tag in valid_tags):
                skip_section = False
                cleaned_lines.append(line)
                continue
        
        if not skip_section:
            cleaned_lines.append(line)
    
    lyrics_text = "\n".join(cleaned_lines).strip()
    
    if not any(lyrics_text.lower().startswith(tag) for tag in valid_tags):
        lyrics_text = "[verse]\n" + lyrics_text
    
    return lyrics_text


# --- Main Interface ---

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Description de la Chanson")
    description = st.text_area(
        "Décrivez l'ambiance, le thème, les émotions de votre chanson",
        value="Une chanson pop moderne sur l'espoir et la persévérance, avec des paroles inspirantes",
        height=120,
        placeholder="Ex: Une ballade mélancolique sur l'amour perdu, style R&B...",
        help="Soyez aussi détaillé que possible pour de meilleurs résultats"
    )

with col2:
    st.subheader("🎵 Audio de Référence")
    uploaded_audio = st.file_uploader(
        "Audio optionnel (mp3/wav)",
        type=["mp3", "wav", "ogg"],
        help="Un extrait audio pour guider le style musical"
    )

# Zone de paroles manuelles
if lyrics_mode == "✍️ Manuel":
    st.subheader("✍️ Vos Paroles")
    st.info("💡 Utilisez uniquement les balises : [verse], [chorus], [bridge]")
    
    manual_lyrics = st.text_area(
        "Écrivez vos paroles ici",
        value="""[verse]
Je marche seul dans la nuit
Ton souvenir brille dans ma vie
Les ombres dansent autour de moi
Mais tu n'es plus là près de moi

[chorus]
Oh mon cœur reviens à moi
Sans toi le monde est si froid
Je cherche ton regard partout
Mais tu es loin de nous

[verse]
Les rues résonnent de ton absence
Je garde en moi notre romance
Chaque coin me rappelle ton visage
Un éternel et doux mirage

[chorus]
Oh mon cœur reviens à moi
Sans toi le monde est si froid
Je cherche ton regard partout
Mais tu es loin de nous""",
        height=350,
        help="Respectez le format avec les balises [verse], [chorus], [bridge]"
    )

# Bouton de génération
st.markdown("---")
generate_button = st.button("🎛️ GÉNÉRER LA CHANSON", use_container_width=True)

# --- Workflow de Génération ---
if generate_button:
    if not description.strip():
        st.error("❌ Veuillez fournir une description de la chanson.")
    else:
        results_container = st.container()
        
        with results_container:
            try:
                # === ÉTAPE 1: Génération des Paroles ===
                st.markdown("### 🎼 Étape 1 : Génération des Paroles")
                
                if lyrics_mode == "✍️ Manuel":
                    st.info("📝 Utilisation de vos paroles manuelles")
                    lyrics_text = manual_lyrics
                    time.sleep(0.5)
                else:
                    st.info("🤖 Génération automatique avec Qwen3-VL...")
                    with st.spinner("Génération en cours..."):
                        lyrics_text = generate_lyrics_with_qwen(description)
                
                # Nettoyage
                lyrics_text = clean_lyrics(lyrics_text)
                
                st.success("✅ Paroles prêtes !")
                
                with st.expander("📜 Voir les Paroles Complètes", expanded=True):
                    st.code(lyrics_text, language=None)
                
                # === ÉTAPE 2: Génération de la Musique ===
                st.markdown("### 🎵 Étape 2 : Génération de la Musique")
                
                st.info("🎹 Connexion au modèle de génération musicale...")
                
                try:
                    client_song = Client(space_url_song)
                    st.success("✅ Connecté au modèle Tencent Song Generation")
                except Exception as e:
                    st.error(f"❌ Impossible de se connecter : {str(e)}")
                    st.stop()
                
                # Audio de référence
                prompt_audio_arg = None
                if uploaded_audio is not None:
                    st.info("🎧 Traitement de l'audio de référence...")
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_audio.name).suffix)
                    tmp.write(uploaded_audio.getbuffer())
                    tmp.flush()
                    tmp.close()
                    prompt_audio_arg = gr_file(tmp.name)
                    st.success("✅ Audio de référence chargé")
                
                # Génération
                st.info("🎼 Génération de la chanson en cours... (1-3 minutes)")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)
                    if i < 30:
                        status_text.text("🎵 Analyse des paroles...")
                    elif i < 60:
                        status_text.text("🎹 Génération de la mélodie...")
                    elif i < 90:
                        status_text.text("🎤 Synthèse vocale...")
                    else:
                        status_text.text("🎚️ Mixage final...")
                
                try:
                    # Appel API avec fallback
                    try:
                        song_result = client_song.predict(
                            lyric=lyrics_text,
                            description=description,
                            prompt_audio=prompt_audio_arg,
                            api_name=api_name_song
                        )
                    except:
                        try:
                            song_result = client_song.predict(
                                lyric=lyrics_text,
                                description=description,
                                api_name=api_name_song
                            )
                        except:
                            song_result = client_song.predict(
                                lyric=lyrics_text,
                                api_name=api_name_song
                            )
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Génération terminée !")
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
                    st.stop()
                
                # === ÉTAPE 3: Résultats ===
                st.markdown("### 🎧 Votre Chanson")
                
                with st.expander("🔍 Informations de Debug"):
                    st.write("**Type:**", type(song_result))
                    st.write("**Contenu:**", song_result)
                
                # Gestion audio
                audio_found = False
                audio_path = None
                
                if isinstance(song_result, (list, tuple)) and len(song_result) > 0:
                    audio_path = song_result[0]
                elif isinstance(song_result, str):
                    audio_path = song_result
                elif isinstance(song_result, dict):
                    audio_path = song_result.get('audio') or song_result.get('file') or song_result.get('path')
                
                if audio_path and isinstance(audio_path, str):
                    if audio_path.endswith((".wav", ".mp3", ".ogg", ".flac")):
                        try:
                            st.success("🎉 Chanson générée avec succès !")
                            st.audio(audio_path)
                            
                            with open(audio_path, "rb") as f:
                                audio_bytes = f.read()
                                st.download_button(
                                    label="⬇️ Télécharger la Chanson",
                                    data=audio_bytes,
                                    file_name=f"senorix_qwen_song_{int(time.time())}.wav",
                                    mime="audio/wav",
                                    use_container_width=True
                                )
                            
                            audio_found = True
                            file_size = len(audio_bytes) / (1024 * 1024)
                            st.info(f"📊 Taille : {file_size:.2f} MB")
                            
                        except Exception as e:
                            st.error(f"❌ Erreur lecture audio : {str(e)}")
                
                if not audio_found:
                    st.warning("⚠️ Aucun fichier audio extrait.")
                    st.info("""
                    💡 **Solutions :**
                    - Vérifiez la disponibilité du modèle
                    - Essayez avec des paroles plus courtes
                    - Utilisez le mode manuel
                    """)
                
            except Exception as e:
                st.error("❌ Erreur pendant le processus")
                st.exception(e)

# --- Footer ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p style='font-size: 14px;'>🎵 <strong>Senorix AI</strong> — Génération avec Qwen3-VL</p>
        <p style='font-size: 12px;'>Propulsé par Qwen3-VL-Demo & Tencent Song Generation</p>
    </div>
    """,
    unsafe_allow_html=True
)
