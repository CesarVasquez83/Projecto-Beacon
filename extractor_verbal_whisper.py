import whisper
import json
from pathlib import Path

BASE = Path("/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON")
AUDIO_PATH = BASE / "audio_output" / "audio.wav"
JSON_IN = BASE / "json_output" / "behavioral_camila.json"
JSON_OUT = BASE / "json_output" / "behavioral_camila.json"

# Cargar JSON
with open(JSON_IN, "r", encoding="utf-8") as f:
    behavioral = json.load(f)

# Cargar modelo Whisper
print("[BEACON] Cargando Whisper (modelo base)...")
model = whisper.load_model("base")

# Transcribir
print("[BEACON] Transcribiendo audio de Camila...")
result = model.transcribe(
    str(AUDIO_PATH),
    language="es",
    word_timestamps=True
)

# Construir transcript con timestamps
transcript = []
for segment in result["segments"]:
    transcript.append({
        "start": round(segment["start"], 1),
        "end": round(segment["end"], 1),
        "text": segment["text"].strip()
    })

print(f"[BEACON] Transcripción completada: {len(transcript)} segmentos")
print(f"[BEACON] Texto completo: \"{result['text']}\"")

# Actualizar JSON
behavioral["transcript"] = transcript
behavioral["position"] = "No especificada (video CV)"
behavioral["status"] = "all_layers_complete — pendiente discrepancy_flags"

with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(behavioral, f, indent=2, ensure_ascii=False)

print(f"\n[BEACON] Capa Verbal completada!")
print(f"   JSON actualizado: {JSON_OUT}")
print(f"\n[BEACON] BEACON ahora tiene las 3 capas reales:")
print(f"   Visual:  {len(behavioral['visual_events'])} eventos (MediaPipe)")
print(f"   Vocal:   {len(behavioral['vocal_events'])} eventos (librosa)")
print(f"   Verbal:  {len(transcript)} segmentos (Whisper)")
