import streamlit as st
import cohere
import re
import time
from gradio_client import Client, handle_file

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="🎵 Senorix AI — Musical Assistant",
    layout="centered"
)

st.markdown("""
<h1 style='text-align:center;'>🎵 Senorix AI — Musical Assistant</h1>
<p style='text-align:center;color:#777;'>
Chat musicale • Testo canzone • Generazione musica con DiffRhythm2
</p>
<hr>
""", unsafe_allow_html=True)

# ======================================================
# COHERE
# ======================================================
co = cohere.Client(st.secrets["COHERE_API_KEY"])
MODEL_NAME = "command-a-vision-07-2025"

# ======================================================
# MUSIC MODEL (DiffRhythm2)
# ======================================================
MUSIC_SPACE = "ASLP-lab/DiffRhythm2"
MUSIC_API = "/infer_music"

try:
    music_client = Client(MUSIC_SPACE)
except Exception as e:
    st.error(f"⚠️ Errore connessione a DiffRhythm2: {e}")
    music_client = None

# ======================================================
# SESSION STATE
# ======================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "lyrics" not in st.session_state:
    st.session_state.lyrics = ""

if "music_generated" not in st.session_state:
    st.session_state.music_generated = False

if "last_audio_path" not in st.session_state:
    st.session_state.last_audio_path = None

# ======================================================
# SIDEBAR - MUSIC SETTINGS
# ======================================================
st.sidebar.header("🎚️ Impostazioni Musica")

st.sidebar.markdown("### 🎸 Stile Musicale")

music_genre = st.sidebar.selectbox(
    "Genere principale",
    ["Pop", "Rock", "Jazz", "Electronic", "Classical", "Hip-Hop", "R&B", "Country", "Folk"],
    index=0
)

instruments = st.sidebar.multiselect(
    "Strumenti (opzionale)",
    ["Piano", "Guitar", "Bass", "Drums", "Strings", "Synth", "Violin", "Saxophone", "Trumpet"],
    default=["Piano", "Bass", "Drums"]
)

mood = st.sidebar.selectbox(
    "Atmosfera",
    ["Happy", "Sad", "Energetic", "Calm", "Dramatic", "Romantic", "Melancholic"],
    index=0
)

st.sidebar.markdown("### ⚙️ Parametri Avanzati")

steps = st.sidebar.slider(
    "Steps (qualità)",
    min_value=8,
    max_value=32,
    value=16,
    step=4,
    help="Più alto = migliore qualità ma più lento"
)

cfg_strength = st.sidebar.slider(
    "CFG Strength",
    min_value=0.5,
    max_value=3.0,
    value=1.3,
    step=0.1,
    help="Controllo aderenza al testo"
)

file_type = st.sidebar.radio(
    "Formato output",
    ["mp3", "wav"],
    index=0
)

randomize_seed = st.sidebar.checkbox(
    "Randomize seed",
    value=True,
    help="Genera risultati diversi ogni volta"
)

if not randomize_seed:
    seed = st.sidebar.number_input(
        "Seed fisso",
        min_value=0,
        max_value=999999,
        value=0
    )
else:
    seed = 0

# ======================================================
# UTILS — TYPEWRITER EFFECT
# ======================================================
def typewriter(text: str, speed: float = 0.015):
    placeholder = st.empty()
    rendered = ""

    for char in text:
        rendered += char
        placeholder.markdown(f"**Senorix AI:** {rendered}")
        time.sleep(speed)

# ======================================================
# UTILS — REMOVE CHORDS
# ======================================================
def remove_chords(text: str) -> str:
    patterns = [
        r'\b[A-G](?:#|b)?(?:m|maj|min|sus|dim|aug)?\d*(?:/[A-G])?\b',
        r'\[[A-G0-9#bmadsus\/]+\]'
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.I)
    return re.sub(r'\n{2,}', '\n', text).strip()

# ======================================================
# NORMALIZE LYRICS FOR DIFFRHYTHM2
# ======================================================
def normalize_lyrics_diffrhythm(text: str) -> str:
    """
    DiffRhythm2 accetta formato LRC con tag:
    [start], [intro], [verse], [chorus], [outro]
    """
    text = text.replace("```", "").strip()
    
    # Se non ha tag, aggiungiamoli
    if not re.search(r'\[(start|intro|verse|chorus|bridge|outro)\]', text, re.I):
        text = fallback_structure_diffrhythm(text)
    
    # Normalizza i tag esistenti
    text = re.sub(r'\[verse\]', '[verse]', text, flags=re.I)
    text = re.sub(r'\[chorus\]', '[chorus]', text, flags=re.I)
    text = re.sub(r'\[bridge\]', '[bridge]', text, flags=re.I)
    text = re.sub(r'\[intro\]', '[intro]', text, flags=re.I)
    text = re.sub(r'\[outro\]', '[outro]', text, flags=re.I)
    
    # Aggiungi [start] all'inizio se non c'è
    if not text.startswith("[start]"):
        text = "[start]\n" + text
    
    # Aggiungi [outro] alla fine se non c'è
    if not "[outro]" in text.lower():
        text = text + "\n[outro]"
    
    return text.strip()

def fallback_structure_diffrhythm(text: str) -> str:
    """Struttura base per DiffRhythm2"""
    lines = [l for l in text.splitlines() if l.strip()]
    mid = max(1, len(lines)//2)

    return f"""[start]
[intro]
[verse]
{chr(10).join(lines[:mid])}
[chorus]
{chr(10).join(lines[mid:])}
[outro]"""

# ======================================================
# VALIDATE FOR MUSIC
# ======================================================
def lyrics_ready_for_music(text: str) -> bool:
    t = text.lower()

    # DiffRhythm2 richiede almeno verse o chorus
    if "[verse]" not in t and "[chorus]" not in t:
        return False

    # Controllo lunghezza
    if len(text.split()) > 400:
        return False

    # Controllo accordi
    if re.search(r'\b[A-G](?:#|b|m|maj|min|sus)?\d*\b', text):
        return False

    return True

# ======================================================
# BUILD TEXT PROMPT FOR DIFFRHYTHM2
# ======================================================
def build_text_prompt(genre: str, instruments: list, mood: str) -> str:
    """Costruisce il prompt testuale per DiffRhythm2"""
    parts = [genre]
    
    if instruments:
        parts.extend(instruments)
    
    parts.append(mood)
    
    return ", ".join(parts)

# ======================================================
# GENERATE MUSIC WITH DIFFRHYTHM2
# ======================================================
def generate_music_diffrhythm(lyrics: str, text_prompt: str, audio_prompt=None) -> str:
    """Genera musica con DiffRhythm2"""
    
    if not music_client:
        st.error("❌ Client musicale non disponibile")
        return None
    
    try:
        # Normalizza lyrics per DiffRhythm2
        lrc_formatted = normalize_lyrics_diffrhythm(lyrics)
        
        # Debug: mostra formato LRC
        with st.expander("🔍 Formato LRC Inviato"):
            st.code(lrc_formatted)
        
        st.info(f"🎼 Generazione con: {text_prompt}")
        
        # Chiamata API
        result = music_client.predict(
            lrc=lrc_formatted,
            audio_prompt=audio_prompt,
            text_prompt=text_prompt,
            seed=seed,
            randomize_seed=randomize_seed,
            steps=steps,
            cfg_strength=cfg_strength,
            file_type=file_type,
            odeint_method="euler",
            api_name=MUSIC_API
        )
        
        # Estrazione path audio
        if isinstance(result, (list, tuple)) and len(result) > 0:
            audio_path = result[0]
        elif isinstance(result, str):
            audio_path = result
        elif isinstance(result, dict):
            audio_path = result.get('audio') or result.get('file')
        else:
            audio_path = None
        
        return audio_path
        
    except Exception as e:
        st.error(f"❌ Errore generazione musica: {str(e)}")
        return None

# ======================================================
# SENORIX AI (COHERE CHAT)
# ======================================================
def senorix_ai(user_message: str) -> str:
    system_prompt = """
You are Senorix AI, a professional music assistant and songwriter.

RULES:
- Talk ONLY about music, songwriting, mood, genre
- You may write or edit song lyrics
- Lyrics MUST use ONLY:
  [verse], [chorus], [bridge]
- You can also use [intro] and [outro] if appropriate
- No chord symbols
- No explanations after lyrics
- Be creative and emotional
"""

    try:
        response = co.chat(
            model=MODEL_NAME,
            message=user_message,
            preamble=system_prompt,
            temperature=0.7,
            max_tokens=700
        )
        return response.text.strip()
    except Exception as e:
        return f"❌ Errore: {str(e)}"

# ======================================================
# CHAT UI
# ======================================================
st.subheader("💬 Chat musicale")

# Mostra chat history
chat_container = st.container()
with chat_container:
    for role, msg in st.session_state.chat:
        if role == "Utente":
            st.markdown(f"**🧑 Tu:** {msg}")
        else:
            st.markdown(f"**🎵 Senorix AI:** {msg}")

# Input utente
user_input = st.text_input("Scrivi a Senorix AI…", key="user_input_field")

col1, col2 = st.columns([1, 4])

with col1:
    send_button = st.button("📤 Invia", use_container_width=True)

with col2:
    clear_chat = st.button("🗑️ Pulisci Chat", use_container_width=True)

if clear_chat:
    st.session_state.chat = []
    st.rerun()

if send_button and user_input.strip():
    st.session_state.chat.append(("Utente", user_input))

    with st.spinner("🎵 Senorix AI sta pensando..."):
        reply = senorix_ai(user_input)

    # Animazione dattilografica
    typewriter(reply, speed=0.01)

    st.session_state.chat.append(("Senorix AI", reply))

    # Se l'AI genera testo canzone, aggiorna lyrics
    if "[verse]" in reply.lower() or "[chorus]" in reply.lower():
        cleaned = remove_chords(reply)
        st.session_state.lyrics = cleaned
        st.session_state.music_generated = False

    st.rerun()

# ======================================================
# LYRICS UI
# ======================================================
st.markdown("---")
st.subheader("🎤 Testo Canzone")

lyrics_input = st.text_area(
    "Testo (modificabile)",
    value=st.session_state.lyrics,
    height=300,
    help="Modifica il testo della canzone. Usa [verse], [chorus], [bridge]"
)

# Update session state
if lyrics_input != st.session_state.lyrics:
    st.session_state.lyrics = lyrics_input
    st.session_state.music_generated = False

# Preview formattato
with st.expander("📋 Preview Formato"):
    st.code(st.session_state.lyrics)

# ======================================================
# MANUAL MUSIC GENERATION BUTTON
# ======================================================
st.markdown("---")

col_gen1, col_gen2 = st.columns(2)

with col_gen1:
    manual_generate = st.button(
        "🎹 Genera Musica Manualmente",
        use_container_width=True,
        type="primary"
    )

with col_gen2:
    auto_mode = st.checkbox(
        "🤖 Generazione Automatica",
        value=False,
        help="Genera musica automaticamente quando il testo è pronto"
    )

# ======================================================
# MUSIC GENERATION
# ======================================================
should_generate = False

if manual_generate:
    should_generate = True

if auto_mode and lyrics_ready_for_music(st.session_state.lyrics) and not st.session_state.music_generated:
    should_generate = True
    st.info("🎶 Testo valido — generazione automatica attivata")

if should_generate and st.session_state.lyrics.strip():
    
    # Controllo validità
    if not lyrics_ready_for_music(st.session_state.lyrics):
        st.warning("""
        ⚠️ **Testo non valido per la generazione**
        
        Assicurati che:
        - Contenga almeno [verse] o [chorus]
        - Non superi 400 parole
        - Non contenga accordi musicali
        """)
    else:
        # Costruisci prompt
        text_prompt = build_text_prompt(music_genre, instruments, mood)
        
        # Progress bar
        progress_container = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
            if i < 30:
                status_text.text("🎵 Analisi testo...")
            elif i < 60:
                status_text.text("🎹 Generazione melodia...")
            elif i < 90:
                status_text.text("🎤 Sintesi vocale...")
            else:
                status_text.text("🎚️ Mixaggio finale...")
        
        # Genera
        with st.spinner("🎧 Composizione musicale in corso..."):
            audio_path = generate_music_diffrhythm(
                lyrics=st.session_state.lyrics,
                text_prompt=text_prompt,
                audio_prompt=None
            )
        
        progress_bar.empty()
        status_text.empty()
        
        # Mostra risultato
        if audio_path:
            st.success("✅ Musica generata con successo!")
            
            st.markdown("### 🎧 Ascolta la Tua Canzone")
            st.audio(audio_path)
            
            st.session_state.last_audio_path = audio_path
            st.session_state.music_generated = True
            
            # Download button
            try:
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                    st.download_button(
                        label=f"⬇️ Scarica {file_type.upper()}",
                        data=audio_bytes,
                        file_name=f"senorix_song_{int(time.time())}.{file_type}",
                        mime=f"audio/{file_type}",
                        use_container_width=True
                    )
            except Exception as e:
                st.warning(f"⚠️ Impossibile scaricare: {e}")
        else:
            st.error("❌ Generazione fallita. Riprova o modifica le impostazioni.")

# ======================================================
# SHOW LAST GENERATED AUDIO
# ======================================================
if st.session_state.last_audio_path and not should_generate:
    st.markdown("---")
    st.markdown("### 🎧 Ultima Canzone Generata")
    st.audio(st.session_state.last_audio_path)
    
    try:
        with open(st.session_state.last_audio_path, "rb") as f:
            audio_bytes = f.read()
            st.download_button(
                label=f"⬇️ Scarica {file_type.upper()}",
                data=audio_bytes,
                file_name=f"senorix_song_{int(time.time())}.{file_type}",
                mime=f"audio/{file_type}",
                use_container_width=True
            )
    except:
        pass

# ======================================================
# FOOTER
# ======================================================
st.markdown("""
<hr>
<div style='text-align:center;color:#666;'>
<b>🎵 Senorix AI</b><br>
Chat Musicale → Lyrics → Musica Automatica<br>
<small>Powered by Cohere + DiffRhythm2</small>
</div>
""", unsafe_allow_html=True)
