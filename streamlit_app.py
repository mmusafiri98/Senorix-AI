import gradio as gr
import time
import os

# Exemple simplifié de génération de chanson
# (à remplacer par ton vrai pipeline / modèle de génération musicale)
def generate_song(lyric, description, prompt_audio, genre, cfg_coef, temperature, top_k):
    # Simulation du temps d'inférence
    time.sleep(3)

    # Pour la démo : on va juste copier un fichier audio de test
    # Dans ton cas, tu devras appeler ton modèle et sauvegarder la sortie audio
    output_path = "/tmp/generated_song.wav"

    # Ici tu génères ton audio avec ton modèle
    # Exemple (FAUX) : fake audio vide pour l'exemple
    with open(output_path, "wb") as f:
        f.write(b"RIFF....WAVEfmt ")  # en vrai tu écris le wav du modèle

    # Retourne le fichier audio ET les métadonnées
    return output_path, {
        "lyric": lyric,
        "genre": genre,
        "prompt_audio": prompt_audio,
        "description": description,
        "params": {
            "cfg_coef": cfg_coef,
            "temperature": temperature,
            "top_k": top_k,
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

# --- Interface Gradio ---
demo = gr.Interface(
    fn=generate_song,
    inputs=[
        gr.Textbox(label="Lyric", lines=10, placeholder="[verse] ..."),
        gr.Textbox(label="Description", placeholder="Description optionnelle"),
        gr.Audio(label="Prompt audio", type="filepath"),
        gr.Dropdown(
            label="Genre",
            choices=["Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Folk", "Other"],
            value="Pop",
        ),
        gr.Number(label="cfg_coef", value=1.5),
        gr.Number(label="temperature", value=0.9),
        gr.Number(label="top_k", value=50),
    ],
    outputs=[
        gr.Audio(label="Generated Song", type="filepath"),  # ✅ audio exploitable par gradio_client
        gr.JSON(label="Infos"),                             # ✅ métadonnées
    ],
    title="🎵 Senorix AI — Song Generation",
    description="Génère une chanson à partir de paroles et de paramètres (genre, température, etc.).",
)

if __name__ == "__main__":
    demo.launch()

