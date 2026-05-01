import subprocess, json, os, sys, math
from pathlib import Path

# ===== CONFIG =====
BASE = Path("/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON")
VIDEO_PATH = BASE / "video_input" / "camila_dominguez_cv.mp4"
FRAMES_DIR = BASE / "frames_output"
AUDIO_DIR = BASE / "audio_output"
JSON_DIR = BASE / "json_output"
JSON_OUT = JSON_DIR / "behavioral_camila.json"

# Crear carpetas si no existen
for d in [FRAMES_DIR, AUDIO_DIR, JSON_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ===== 1. Extraer audio =====
print("[BEACON] Extrayendo audio...")
audio_path = AUDIO_DIR / "audio.wav"
subprocess.run([
    "ffmpeg", "-y", "-i", str(VIDEO_PATH), "-vn", "-acodec", "pcm_s16le",
    "-ar", "16000", "-ac", "1", str(audio_path)
], capture_output=True)

# ===== 2. Extraer frames (1 por segundo, suficiente para detección de gestos) =====
print("[BEACON] Extrayendo frames...")
subprocess.run([
    "ffmpeg", "-y", "-i", str(VIDEO_PATH), "-vf", "fps=1,scale=640:-1",
    str(FRAMES_DIR / "frame_%04d.jpg")
], capture_output=True)

# ===== 3. Obtener duración del video =====
print("[BEACON] Analizando metadata...")
result = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "csv=p=0", str(VIDEO_PATH)
], capture_output=True, text=True)
duration = float(result.stdout.strip())

# ===== 4. Transcripción simulada (placeholder — luego ponemos Whisper) =====
print("[BEACON] Transcribiendo (modo placeholder — sin voz detectada)...")
transcript = [
    {"start": 0.0, "end": duration, "text": "[Transcripción pendiente — integrar Whisper]"}
]

# ===== 5. Vocal layer (placeholder basado en duración del audio) =====
print("[BEACON] Analizando capa vocal...")
vocal_events = [
    {"timestamp": round(duration * 0.3, 1), "label": "placeholder_vocal_event",
     "note": "Integrar librosa para pitch, speech rate, jitter"}
]

# ===== 6. Visual layer (placeholder basado en frames extraídos) =====
print("[BEACON] Analizando capa visual...")
frame_files = sorted(FRAMES_DIR.glob("frame_*.jpg"))
visual_events = []
for i, f in enumerate(frame_files):
    t = i  # 1 frame por segundo
    visual_events.append({
        "timestamp": round(t, 1),
        "label": "frame_captured",
        "frame": f.name,
        "note": "Integrar MediaPipe para AU/blendshape detection"
    })

# ===== 7. Behavioral JSON =====
print("[BEACON] Fusionando capas...")
behavioral = {
    "interview_id": "BEACON-CAMILA-001",
    "candidate_alias": "Camila Domínguez",
    "duration_seconds": round(duration, 1),
    "position": "No especificada",
    "source_video": str(VIDEO_PATH.name),
    "transcript": transcript,
    "visual_events": visual_events,
    "vocal_events": vocal_events,
    "discrepancy_flags": [],
    "status": "placeholder — integrar MediaPipe + librosa + Whisper"
}

with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(behavioral, f, indent=2, ensure_ascii=False)

print(f"\n[BEACON] ¡Extracción completada!")
print(f"   JSON generado: {JSON_OUT}")
print(f"   Frames extraídos: {len(frame_files)}")
print(f"   Duración: {duration:.1f}s")
