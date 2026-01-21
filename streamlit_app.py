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
    layout="wide",
    initial_sidebar_state="expanded"
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
    transition: all 0.3s;
}
.stButton>button:hover {
    background-color: #764ba2;
    transform: scale(1.02);
}
.info-box {
    background: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}
.genre-badge {
    display: inline-block;
    background: #667eea;
    color: white;
    padding: 5px 12px;
    border-radius: 20px;
    margin: 3px;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
<h1>🎵 Senorix AI — Song Generation</h1>
<p>Generazione Avanzata: Lyrics AI + Musica Personalizzata</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR - CONFIGURAZIONE AVANZATA
# ======================================================
st.sidebar.header("⚙️ Configurazione Avanzata")

# --- Sezione Generazione Parole ---
st.sidebar.markdown("### 🎤 Generazione Parole")
lyrics_mode = st.sidebar.radio(
    "Modalità",
    ["🤖 Automatica (LLaMA-2)", "✍️ Manuale"],
    index=0,
    help="Automatica: l'AI genera le parole. Manuale: scrivi tu."
)

st.sidebar.markdown("---")

# --- Sezione Genere Musicale ---
st.sidebar.markdown("### 🎸 Genere Musicale")
genre = st.sidebar.selectbox(
    "Scegli il genere",
    [
        "Pop",
        "Rock",
        "Alternative Rock",
        "Indie Pop",
        "R&B",
        "Hip-Hop",
        "Rap",
        "Gospel",
        "Soul",
        "Jazz",
        "Blues",
        "Country",
        "Folk",
        "Electronic",
        "Dance/EDM",
        "Classical",
        "Metal",
        "Punk",
        "Reggae",
        "Latin",
        "K-Pop",
        "Ballad",
        "Acoustic",
        "Other"
    ],
    index=0,
    help="Il genere influenza lo stile musicale generato"
)

# Sub-genere opzionale
sub_genre = st.sidebar.text_input(
    "Sub-genere (opzionale)",
    placeholder="es: synthwave, lo-fi, trap...",
    help="Specifica ulteriormente lo stile"
)

st.sidebar.markdown("---")

# --- Sezione Tipo di Voce ---
st.sidebar.markdown("### 🎤 Tipo di Voce")

voice_gender = st.sidebar.radio(
    "Genere vocale",
    ["Maschile", "Femminile", "Misto/Duetto"],
    index=0
)

if voice_gender == "Maschile":
    voice_type = st.sidebar.selectbox(
        "Registro vocale",
        [
            "Baritono (medio)",
            "Tenore (alto)",
            "Basso (profondo)",
            "Controtenore (molto alto)"
        ],
        index=0
    )
elif voice_gender == "Femminile":
    voice_type = st.sidebar.selectbox(
        "Registro vocale",
        [
            "Mezzosoprano (medio)",
            "Soprano (alto)",
            "Contralto (grave)"
        ],
        index=0
    )
else:  # Misto
    voice_type = st.sidebar.selectbox(
        "Tipo duetto",
        [
            "Duetto bilanciato (M+F)",
            "Lead maschile + cori femminili",
            "Lead femminile + cori maschili",
            "Alternato (verse M / chorus F)"
        ],
        index=0
    )

# Caratteristiche vocali aggiuntive
st.sidebar.markdown("**Caratteristiche vocali:**")
vocal_style = st.sidebar.multiselect(
    "Stile vocale (opzionale)",
    [
        "Emotivo/Espressivo",
        "Potente/Energico",
        "Dolce/Delicato",
        "Rauco/Grintoso",
        "Vibrato marcato",
        "Voce pulita",
        "Con autotune",
        "Stile rap/parlato",
        "Melismatico (gospel)"
    ],
    help="Seleziona una o più caratteristiche"
)

st.sidebar.markdown("---")

# --- Sezione Parametri Tecnici ---
st.sidebar.markdown("### 🎚️ Parametri Audio")

tempo_bpm = st.sidebar.slider(
    "Tempo (BPM)",
    min_value=60,
    max_value=180,
    value=90,
    step=5,
    help="Velocità della canzone (60=lento, 180=veloce)"
)

mood = st.sidebar.selectbox(
    "Atmosfera generale",
    [
        "Allegra/Positiva",
        "Malinconica/Triste",
        "Energica/Motivante",
        "Rilassante/Calma",
        "Drammatica/Intensa",
        "Romantica/Intima",
        "Aggressiva/Ribelle",
        "Spirituale/Contemplativa"
    ],
    index=0
)

st.sidebar.markdown("---")

# --- Sezione API ---
st.sidebar.markdown("### 🔌 Configurazione API")
space_url_song = st.sidebar.text_input(
    "Tencent Song Space URL",
    value="https://tencent-songgeneration.hf.space/",
    help="URL dello Space Gradio"
)

api_name_song = st.sidebar.text_input(
    "Endpoint API",
    value="/generate_song"
)

# ======================================================
# LYRICS UTILS
# ======================================================

def normalize_lyrics(text: str) -> str:
    """Rende SEMPRE valido l'output dell'AI se possibile"""
    if not text:
        return ""

    text = text.replace("```", "").strip()
    
    # Rimuove testo prima del primo tag
    match = re.search(r'\[(verse|chorus|bridge)\]', text, re.I)
    if match:
        text = text[match.start():]

    # Normalizza i tag
    text = re.sub(r'\[verse\]', '[verse]', text, flags=re.I)
    text = re.sub(r'\[chorus\]', '[chorus]', text, flags=re.I)
    text = re.sub(r'\[bridge\]', '[bridge]', text, flags=re.I)

    return text.strip()


def is_valid_lyrics(text: str) -> bool:
    """Valido se contiene almeno verse + chorus"""
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

def generate_lyrics_with_llama(description: str, genre: str, mood: str) -> str:
    """Generazione ROBUSTA con LLaMA-2"""
    
    st.info("🔄 Connessione a LLaMA-2-13B-Chat…")

    try:
        client = Client("huggingface-projects/llama-2-13b-chat")
    except Exception as e:
        st.error(f"❌ Errore connessione: {e}")
        return default_lyrics()

    system_prompt = (
        "You are a professional songwriter.\n"
        "You must ONLY output song lyrics.\n"
        "You must NEVER explain.\n"
        "You must start immediately with [verse] or [chorus]."
    )

    user_prompt = f"""
Write a {genre} song with a {mood} mood about:

\"{description}\"

STRICT RULES:
- Output ONLY lyrics
- Use ONLY: [verse], [chorus], [bridge]
- Start IMMEDIATELY with a tag
- No titles, no comments
- 2–6 lines per section
- Minimum: 2 verses + 1 chorus
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
        st.error(f"❌ Errore generazione: {e}")
        return default_lyrics()

    # Estrazione testo
    if isinstance(raw, list):
        raw_text = raw[0]
    else:
        raw_text = str(raw)

    # Normalizzazione
    cleaned = normalize_lyrics(raw_text)

    # Validazione
    if not is_valid_lyrics(cleaned):
        st.warning("⚠️ Output AI non strutturato, uso fallback")
        return default_lyrics()

    st.success("✅ Parole generate correttamente")
    return cleaned


def build_music_description(genre: str, sub_genre: str, voice_gender: str, 
                           voice_type: str, vocal_style: list, 
                           tempo_bpm: int, mood: str, description: str) -> str:
    """Costruisce la descrizione dettagliata per il modello musicale"""
    
    parts = []
    
    # Genere
    if sub_genre:
        parts.append(f"{sub_genre} {genre}")
    else:
        parts.append(genre)
    
    # Voce
    voice_desc = voice_type.split("(")[0].strip().lower()
    if voice_gender == "Maschile":
        parts.append(f"male {voice_desc} vocals")
    elif voice_gender == "Femminile":
        parts.append(f"female {voice_desc} vocals")
    else:
        parts.append(f"duet vocals {voice_desc}")
    
    # Stile vocale
    if vocal_style:
        style_terms = {
            "Emotivo/Espressivo": "emotional expressive delivery",
            "Potente/Energico": "powerful energetic voice",
            "Dolce/Delicato": "soft delicate vocals",
            "Rauco/Grintoso": "raspy gritty voice",
            "Vibrato marcato": "with vibrato",
            "Voce pulita": "clean vocals",
            "Con autotune": "with autotune",
            "Stile rap/parlato": "rap style delivery",
            "Melismatico (gospel)": "melismatic gospel style"
        }
        for style in vocal_style:
            if style in style_terms:
                parts.append(style_terms[style])
    
    # Atmosfera
    mood_terms = {
        "Allegra/Positiva": "upbeat and positive",
        "Malinconica/Triste": "melancholic and sad",
        "Energica/Motivante": "energetic and motivational",
        "Rilassante/Calma": "relaxing and calm",
        "Drammatica/Intensa": "dramatic and intense",
        "Romantica/Intima": "romantic and intimate",
        "Aggressiva/Ribelle": "aggressive and rebellious",
        "Spirituale/Contemplativa": "spiritual and contemplative"
    }
    if mood in mood_terms:
        parts.append(mood_terms[mood])
    
    # Tempo
    parts.append(f"{tempo_bpm} bpm")
    
    # Descrizione originale
    parts.append(f"about: {description}")
    
    return ", ".join(parts)


# ======================================================
# MAIN UI
# ======================================================

# Layout a colonne
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Descrizione della Canzone")
    description = st.text_area(
        "Tema, storia, messaggio o emozioni",
        value="Una canzone sull'immigrazione e sulla libertà di esplorare nuovi popoli",
        height=120,
        help="Descrivi il contenuto della canzone nel modo più dettagliato possibile"
    )

with col2:
    st.subheader("🎧 Audio di Riferimento")
    
    # Tabs per diversi tipi di upload
    audio_tab1, audio_tab2 = st.tabs(["📁 Carica File", "ℹ️ Info"])
    
    with audio_tab1:
        uploaded_audio = st.file_uploader(
            "Carica un brano di riferimento",
            type=["mp3", "wav", "ogg", "flac"],
            help="L'AI userà questo audio come riferimento per lo stile"
        )
        
        if uploaded_audio:
            st.audio(uploaded_audio)
            st.success("✅ Audio caricato")
    
    with audio_tab2:
        st.info("""
        **Come funziona?**
        
        L'audio di riferimento permette all'AI di:
        - Analizzare lo stile musicale
        - Replicare il sound
        - Mantenere coerenza timbrica
        
        💡 **Consiglio:** Carica 15-30 secondi del brano che ti piace
        """)

# Area parole manuali
if lyrics_mode == "✍️ Manuale":
    st.markdown("---")
    st.subheader("✍️ Scrivi le Tue Parole")
    
    col_help1, col_help2 = st.columns(2)
    
    with col_help1:
        st.info("💡 Usa solo: **[verse]**, **[chorus]**, **[bridge]**")
    
    with col_help2:
        st.info("📋 Struttura minima: 2 verse + 1 chorus")
    
    manual_lyrics = st.text_area(
        "Inserisci le parole (con tag)",
        height=300,
        placeholder="""[verse]
Prima strofa qui...

[chorus]
Ritornello qui...

[verse]
Seconda strofa qui...

[chorus]
Ritornello ripetuto..."""
    )

# Riepilogo selezioni
st.markdown("---")
st.subheader("📊 Riepilogo Configurazione")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.markdown(f"""
    <div class="info-box">
    <b>🎸 Genere:</b><br>
    <span class="genre-badge">{genre}</span>
    {f'<span class="genre-badge">{sub_genre}</span>' if sub_genre else ''}
    </div>
    """, unsafe_allow_html=True)

with summary_col2:
    st.markdown(f"""
    <div class="info-box">
    <b>🎤 Voce:</b><br>
    {voice_gender} - {voice_type}
    </div>
    """, unsafe_allow_html=True)

with summary_col3:
    st.markdown(f"""
    <div class="info-box">
    <b>⏱️ Tempo:</b><br>
    {tempo_bpm} BPM - {mood}
    </div>
    """, unsafe_allow_html=True)

# Bottone generazione
st.markdown("---")
generate_button = st.button("🎛️ GENERA CANZONE", use_container_width=True)

# ======================================================
# PIPELINE
# ======================================================

if generate_button:
    if not description.strip():
        st.error("❌ Inserisci una descrizione della canzone")
        st.stop()

    # Container per i risultati
    results_container = st.container()
    
    with results_container:
        try:
            # === STEP 1: PAROLE ===
            st.markdown("## 🎼 Step 1 — Generazione Parole")
            
            if lyrics_mode == "✍️ Manuale":
                st.info("📝 Utilizzo parole manuali")
                lyrics_text = manual_lyrics
                if not lyrics_text.strip():
                    st.error("❌ Inserisci le parole nella sezione sopra")
                    st.stop()
            else:
                st.info(f"🤖 Generazione parole in stile {genre}...")
                with st.spinner("Generazione in corso..."):
                    lyrics_text = generate_lyrics_with_llama(description, genre, mood)
            
            # Visualizza parole
            with st.expander("📜 Visualizza Parole Complete", expanded=True):
                st.code(lyrics_text, language=None)
            
            # === STEP 2: MUSICA ===
            st.markdown("## 🎵 Step 2 — Generazione Musica")
            
            st.info("🎹 Connessione al modello musicale...")
            
            try:
                client_song = Client(space_url_song)
                st.success("✅ Connesso a Tencent Song Generation")
            except Exception as e:
                st.error(f"❌ Errore connessione: {e}")
                st.stop()
            
            # Prepara audio di riferimento
            prompt_audio = None
            if uploaded_audio:
                st.info("🎧 Elaborazione audio di riferimento...")
                tmp = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=Path(uploaded_audio.name).suffix
                )
                tmp.write(uploaded_audio.getbuffer())
                tmp.close()
                prompt_audio = gr_file(tmp.name)
                st.success("✅ Audio di riferimento caricato")
            
            # Costruisci descrizione dettagliata
            music_description = build_music_description(
                genre, sub_genre, voice_gender, voice_type,
                vocal_style, tempo_bpm, mood, description
            )
            
            with st.expander("🔍 Descrizione Inviata al Modello"):
                st.code(music_description)
            
            # Genera musica
            st.info("🎼 Generazione musica in corso... (può richiedere 1-3 minuti)")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
                if i < 25:
                    status_text.text("🎵 Analisi parole e stile...")
                elif i < 50:
                    status_text.text("🎹 Generazione strumentali...")
                elif i < 75:
                    status_text.text("🎤 Sintesi vocale...")
                else:
                    status_text.text("🎚️ Mixaggio e mastering...")
            
            try:
                # Chiamata API con fallback
                try:
                    song_result = client_song.predict(
                        lyric=lyrics_text,
                        description=music_description,
                        prompt_audio=prompt_audio,
                        api_name=api_name_song
                    )
                except:
                    st.warning("⚠️ Tentativo senza audio di riferimento...")
                    try:
                        song_result = client_song.predict(
                            lyric=lyrics_text,
                            description=music_description,
                            api_name=api_name_song
                        )
                    except:
                        song_result = client_song.predict(
                            lyric=lyrics_text,
                            api_name=api_name_song
                        )
                
                progress_bar.progress(100)
                status_text.text("✅ Generazione completata!")
                
            except Exception as e:
                st.error(f"❌ Errore generazione: {e}")
                st.stop()
            
            # === STEP 3: RISULTATO ===
            st.markdown("## 🎧 La Tua Canzone")
            
            # Debug info
            with st.expander("🔍 Informazioni Debug"):
                st.write("**Tipo risultato:**", type(song_result))
                st.write("**Contenuto:**", song_result)
            
            # Estrai audio
            audio_path = None
            if isinstance(song_result, (list, tuple)) and len(song_result) > 0:
                audio_path = song_result[0]
            elif isinstance(song_result, str):
                audio_path = song_result
            elif isinstance(song_result, dict):
                audio_path = song_result.get('audio') or song_result.get('file')
            
            # Mostra audio
            if audio_path and isinstance(audio_path, str):
                if audio_path.endswith((".wav", ".mp3", ".ogg", ".flac")):
                    try:
                        st.success("🎉 Canzone generata con successo!")
                        
                        # Player
                        st.audio(audio_path)
                        
                        # Info file
                        try:
                            file_size = Path(audio_path).stat().st_size / (1024 * 1024)
                            st.info(f"📊 Dimensione: {file_size:.2f} MB")
                        except:
                            pass
                        
                        # Download
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                            
                            col_dl1, col_dl2 = st.columns(2)
                            
                            with col_dl1:
                                st.download_button(
                                    label="⬇️ Scarica Canzone (WAV)",
                                    data=audio_bytes,
                                    file_name=f"senorix_{genre.lower().replace(' ', '_')}_{int(time.time())}.wav",
                                    mime="audio/wav",
                                    use_container_width=True
                                )
                            
                            with col_dl2:
                                # Bottone per rigenerare
                                if st.button("🔄 Rigenera con Stesse Impostazioni", use_container_width=True):
                                    st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Errore lettura audio: {e}")
                else:
                    st.warning(f"⚠️ Formato audio non riconosciuto: {audio_path}")
            else:
                st.warning("⚠️ Nessun audio restituito dal modello")
                st.info("""
                💡 **Possibili soluzioni:**
                - Prova con parole più brevi
                - Rimuovi l'audio di riferimento
                - Semplifica la descrizione
                - Riprova tra qualche minuto
                """)
        
        except Exception as e:
            st.error("❌ Errore durante il processo")
            st.exception(e)
            st.info("""
            💡 **Suggerimenti:**
            - Verifica la connessione internet
            - Controlla che il modèle sia disponibile
            - Prova con una descrizione più semplice
            - Usa il modo manuale se persiste
            """)

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#666;padding:20px;'>
        <p style='font-size:14px;'><b>🎵 Senorix AI</b> — Generazione Avanzata di Canzoni</p>
        <p style='font-size:12px;'>LLaMA-2-13B + Tencent Song Generation</p>
        <p style='font-size:11px;margin-top:10px;'>
            Personalizza genere, voce, tempo e stile per creare la tua canzone unica
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
