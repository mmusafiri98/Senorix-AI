import streamlit as st
import cohere
import re
import time
import traceback
from gradio_client import Client

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Senorix AI — Stable Music Generator",
    layout="centered"
)

st.title("🎵 Senorix AI — Stable Music Generator")
st.caption("Lyrics → Format sécurisé → Génération musicale stable (DiffRhythm2)")

# ======================================================
# COHERE
# ======================================================
co = cohere.Client(st.secrets["COHERE_API_KEY"])
MODEL_NAME = "command-a-vision-07-2025"

# ======================================================
# DIFFRHYTHM2
# ======================================================
MUSIC_SPACE = "ASLP-lab/DiffRhythm2"
MUSIC_API = "/infer_music"

try:
    music_client = Client(MUSIC_SPACE)
    st.success("Connecté à DiffRhythm2")
except Exception as e:
    st.error(f"Impossible de connecter DiffRhythm2: {e}")
    music_client = None

# ======================================================
# CONSTANTES
# ======================================================
MAX_WORDS = 220
MAX_LINES = 20
SAFE_STEPS = 16
SAFE_CFG = 1.3
FILE_TYPE = "mp3"

# ======================================================
# SESSION STATE
# ======================================================
for key in ["lyrics", "audio", "generated"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ======================================================
# UTILS
# ======================================================
def clean_text(text):
    """Remove code blocks and chords"""
    text = text.replace("```", "")
    text = re.sub(r'\b[A-G](#|b|m|maj|min|sus|dim)?\d*\b', '', text)
    return text.strip()

def enforce_limits(text):
    """Enforce word and line limits"""
    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])
        st.warning(f"Texte tronqué à {MAX_WORDS} mots")

    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        st.warning(f"Texte tronqué à {MAX_LINES} lignes")

    return "\n".join(lines)

def safe_lrc_structure(text):
    """Create valid LRC structure for DiffRhythm2"""
    lines = [l for l in text.splitlines() if l.strip()]

    if not lines:
        return "[start]\n[intro]\n[verse]\nEmpty song\n[chorus]\nEmpty chorus\n[outro]"

    # Split into verse and chorus
    mid = max(1, len(lines) // 2)
    verse_lines = lines[:mid]
    chorus_lines = lines[mid:] if mid < len(lines) else lines[:2]

    # Build LRC format
    lrc_parts = [
        "[start]",
        "[intro]",
        "",
        "[verse]"
    ]
    lrc_parts.extend(verse_lines)
    lrc_parts.extend(["", "[chorus]"])
    lrc_parts.extend(chorus_lines)
    lrc_parts.extend(["", "[outro]"])
    
    return "\n".join(lrc_parts)

def prepare_lyrics(text):
    """Full preparation pipeline"""
    text = clean_text(text)
    text = enforce_limits(text)
    return safe_lrc_structure(text)

def lyrics_are_valid(text):
    """Validate lyrics"""
    if not text or not text.strip():
        return False
    words = text.split()
    if len(words) < 10:
        return False
    if len(words) > MAX_WORDS:
        return False
    return True

# ======================================================
# COHERE LYRICS GENERATION
# ======================================================
def generate_lyrics(prompt):
    """Generate lyrics with Cohere"""
    system = """You are a professional songwriter.
Write short emotional lyrics.
Rules:
- NO chords
- MAX 2 sections (verse + chorus)
- Simple lines
- Emotional
- Total: max 16 lines"""

    try:
        response = co.chat(
            model=MODEL_NAME,
            message=f"Write a song about: {prompt}",
            preamble=system,
            temperature=0.7,
            max_tokens=300
        )
        return response.text.strip()
    except Exception as e:
        st.error(f"Erreur Cohere: {e}")
        return ""

# ======================================================
# MUSIC GENERATION
# ======================================================
def generate_music_safe(lyrics, mood, genre):
    """Generate music with detailed error handling"""
    if not music_client:
        st.error("Client musical non disponible")
        return None

    # Prepare lyrics
    lrc = prepare_lyrics(lyrics)
    
    # Show generated LRC (debug)
    with st.expander("Debug: Format LRC Généré"):
        st.code(lrc)
    
    # Build prompt
    prompt = f"{genre}, {mood}"
    
    st.info(f"Envoi à DiffRhythm2...")
    st.info(f"Prompt: {prompt}")
    st.info(f"Steps: {SAFE_STEPS}, CFG: {SAFE_CFG}")

    try:
        # First attempt with normal parameters
        st.info("Tentative 1: Paramètres normaux...")
        
        result = music_client.predict(
            lrc=lrc,
            audio_prompt=None,
            text_prompt=prompt,
            seed=0,
            randomize_seed=True,
            steps=SAFE_STEPS,
            cfg_strength=SAFE_CFG,
            file_type=FILE_TYPE,
            odeint_method="euler",
            api_name=MUSIC_API
        )
        
        st.success("Génération complétée!")
        
        # Debug: show result
        with st.expander("Debug: Réponse API"):
            st.write("Type:", type(result))
            st.write("Contenu:", result)
        
        # Extract audio path
        if isinstance(result, (list, tuple)) and len(result) > 0:
            return result[0]
        elif isinstance(result, str):
            return result
        else:
            st.error(f"Format de réponse invalide: {type(result)}")
            return None

    except Exception as e:
        # Show REAL error instead of hiding it
        error_msg = str(e)
        st.error(f"Erreur spécifique: {error_msg}")
        
        # Show full stack trace
        with st.expander("Stack Trace Complet"):
            st.code(traceback.format_exc())
        
        # Fallback only if GPU error
        if "gpu" in error_msg.lower() or "memory" in error_msg.lower():
            st.warning("Tentative avec paramètres réduits...")
            try:
                result = music_client.predict(
                    lrc=lrc,
                    audio_prompt=None,
                    text_prompt="ambient, simple",
                    seed=0,
                    randomize_seed=True,
                    steps=8,
                    cfg_strength=1.0,
                    file_type="mp3",
                    odeint_method="euler",
                    api_name=MUSIC_API
                )
                
                if isinstance(result, (list, tuple)) and len(result) > 0:
                    return result[0]
                elif isinstance(result, str):
                    return result
                    
            except Exception as e2:
                st.error(f"Fallback échoué: {str(e2)}")
                return None
        else:
            st.error("Vérifiez le format LRC dans l'expander debug ci-dessus")
            return None

# ======================================================
# UI - LYRICS GENERATION
# ======================================================
st.markdown("### Génération de Paroles")

col1, col2 = st.columns([3, 1])

with col1:
    user_prompt = st.text_input(
        "Décris ta chanson",
        placeholder="ex: une chanson triste sur l'amour perdu..."
    )

with col2:
    generate_lyrics_btn = st.button("Générer", use_container_width=True)

if generate_lyrics_btn and user_prompt:
    with st.spinner("Écriture des paroles..."):
        lyrics = generate_lyrics(user_prompt)
        if lyrics:
            st.session_state.lyrics = lyrics
            st.session_state.generated = False
            st.success("Paroles générées!")

# ======================================================
# UI - LYRICS EDITOR
# ======================================================
st.markdown("---")
st.markdown("### Paroles")

lyrics_input = st.text_area(
    "Paroles (modifiables)",
    value=st.session_state.lyrics or "",
    height=250,
    help="Les paroles seront automatiquement formatées pour DiffRhythm2"
)

st.session_state.lyrics = lyrics_input

# Stats
if lyrics_input:
    words = len(lyrics_input.split())
    lines = len([l for l in lyrics_input.splitlines() if l.strip()])
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Mots", words, delta=f"Max: {MAX_WORDS}")
    with col_stat2:
        st.metric("Lignes", lines, delta=f"Max: {MAX_LINES}")
    with col_stat3:
        valid = "Valide" if lyrics_are_valid(lyrics_input) else "Invalide"
        st.metric("Status", valid)

# ======================================================
# UI - MUSIC PARAMETERS
# ======================================================
st.markdown("---")
st.markdown("### Paramètres Musicaux")

col_genre, col_mood = st.columns(2)

with col_genre:
    genre = st.selectbox(
        "Genre",
        ["Pop", "Rock", "Electronic", "Jazz", "Ambient", "Classical", "Hip-Hop"]
    )

with col_mood:
    mood = st.selectbox(
        "Mood",
        ["Happy", "Sad", "Calm", "Romantic", "Energetic", "Melancholic"]
    )

# Advanced parameters
with st.expander("Paramètres Avancés"):
    col_steps, col_cfg = st.columns(2)
    
    with col_steps:
        custom_steps = st.slider(
            "Steps (qualité)",
            min_value=8,
            max_value=24,
            value=SAFE_STEPS,
            step=4
        )
    
    with col_cfg:
        custom_cfg = st.slider(
            "CFG Strength",
            min_value=0.8,
            max_value=2.0,
            value=SAFE_CFG,
            step=0.1
        )
    
    use_custom = st.checkbox("Utiliser paramètres personnalisés", value=False)
    
    if use_custom:
        SAFE_STEPS = custom_steps
        SAFE_CFG = custom_cfg

st.markdown("---")

# ======================================================
# UI - MUSIC GENERATION
# ======================================================
generate_music_btn = st.button(
    "GÉNÉRER LA MUSIQUE",
    type="primary",
    use_container_width=True
)

if generate_music_btn:
    if not lyrics_are_valid(lyrics_input):
        st.error("""Paroles invalides
        
Les paroles doivent:
- Contenir au moins 10 mots
- Ne pas dépasser 220 mots
- Ne pas être vides""")
    else:
        # Progress bar
        progress = st.progress(0)
        status = st.empty()
        
        for i in range(100):
            time.sleep(0.02)
            progress.progress(i + 1)
            if i < 30:
                status.text("Préparation du format LRC...")
            elif i < 60:
                status.text("Génération musicale...")
            else:
                status.text("Finalisation...")
        
        # Generate music
        with st.spinner("Composition en cours..."):
            audio = generate_music_safe(lyrics_input, mood, genre)
        
        progress.empty()
        status.empty()
        
        if audio:
            st.success("Musique générée avec succès!")
            
            st.markdown("### Écouter")
            st.audio(audio)
            
            st.session_state.audio = audio
            st.session_state.generated = True
            
            # Download button
            try:
                with open(audio, "rb") as f:
                    st.download_button(
                        label=f"Télécharger {FILE_TYPE.upper()}",
                        data=f.read(),
                        file_name=f"senorix_{genre.lower()}_{int(time.time())}.{FILE_TYPE}",
                        mime=f"audio/{FILE_TYPE}",
                        use_container_width=True
                    )
            except Exception as e:
                st.warning(f"Download non disponible: {e}")
        else:
            st.error("""Génération échouée
            
Vérifiez:
1. Le format LRC dans l'expander debug
2. Les erreurs spécifiques affichées ci-dessus
3. Que DiffRhythm2 est connecté

Essayez de:
- Réduire la longueur des paroles
- Simplifier le texte
- Utiliser des paramètres plus bas""")

# Show last generation
if st.session_state.audio and not generate_music_btn:
    st.markdown("---")
    st.markdown("### Dernière Génération")
    st.audio(st.session_state.audio)
    
    try:
        with open(st.session_state.audio, "rb") as f:
            st.download_button(
                label=f"Télécharger {FILE_TYPE.upper()}",
                data=f.read(),
                file_name=f"senorix_song.{FILE_TYPE}",
                mime=f"audio/{FILE_TYPE}",
                use_container_width=True
            )
    except:
        pass

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#666;'>
<b>Senorix AI</b><br>
Powered by Cohere + DiffRhythm2<br>
<small>Version avec Debug Détaillé</small>
</div>
""", unsafe_allow_html=True)

