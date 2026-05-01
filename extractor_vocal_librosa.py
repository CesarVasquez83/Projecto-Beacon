import librosa
import numpy as np
import json
from pathlib import Path

BASE = Path("/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON")
AUDIO_PATH = BASE / "audio_output" / "audio.wav"
JSON_IN = BASE / "json_output" / "behavioral_camila.json"
JSON_OUT = BASE / "json_output" / "behavioral_camila.json"

# Cargar JSON
with open(JSON_IN, "r", encoding="utf-8") as f:
    behavioral = json.load(f)

# Cargar audio
print(f"[BEACON] Cargando audio...")
y, sr = librosa.load(str(AUDIO_PATH), sr=None)

# Calcular duración real
duration = len(y) / sr
print(f"[BEACON] Audio: {duration:.1f}s @ {sr}Hz")

# Extraer pitch (F0) con piptrack
print("[BEACON] Extrayendo pitch (F0)...")
pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=100, fmax=500)
pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
pitch_std = np.std(pitches[pitches > 0]) if np.any(pitches > 0) else 0
pitch_baseline = pitch_mean
print(f"[BEACON] Pitch medio: {pitch_baseline:.0f}Hz")

# Extraer RMS Energy a lo largo del tiempo
print("[BEACON] Extrayendo energía (RMS)...")
hop_length = 512
rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
times = librosa.times_like(rms, sr=sr, hop_length=hop_length)
rms_mean = np.mean(rms)
rms_std = np.std(rms)

# Extraer Zero Crossing Rate
print("[BEACON] Extrayendo Zero Crossing Rate...")
zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]

# Extraer Spectral Centroid
print("[BEACON] Extrayendo Spectral Centroid...")
spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]

# Detectar eventos vocales (picos/vales significativos en pitch y energía)
vocal_events = []
window_size = int(sr * 0.5 / hop_length)  # ventana de 0.5s

for i in range(window_size, len(times) - window_size):
    t = round(times[i], 1)
    
    # Pitch en esta ventana
    pitch_frame_idx = int(t * sr / hop_length)
    if pitch_frame_idx < pitches.shape[1]:
        pitch_slice = pitches[:, pitch_frame_idx]
        pitch_val = np.mean(pitch_slice[pitch_slice > 0]) if np.any(pitch_slice > 0) else 0
    else:
        pitch_val = 0
    
    # Energy en esta ventana
    energy_val = rms[i]
    energy_zscore = (energy_val - rms_mean) / rms_std if rms_std > 0 else 0
    
    # Spectral centroid
    spec_val = spectral_centroids[i]
    
    # Detectar picos de pitch (>1.5 desviaciones sobre la media)
    if pitch_val > pitch_baseline + 1.5 * pitch_std and pitch_baseline > 0:
        vocal_events.append({
            "timestamp": t,
            "label": "pitch_spike",
            "value_hz": round(float(pitch_val), 1),
            "baseline_hz": round(float(pitch_baseline), 1),
            "note": f"Pico de pitch detectado"
        })
    
    # Detectar energía alta (>2 desviaciones)
    if energy_zscore > 2.0:
        vocal_events.append({
            "timestamp": t,
            "label": "high_energy",
            "rms": round(float(energy_val), 4),
            "zscore": round(float(energy_zscore), 2),
            "note": "Energía vocal elevada"
        })
    
    # Detectar energía muy baja (<-1.5 desviaciones) = pausa
    if energy_zscore < -1.5:
        vocal_events.append({
            "timestamp": t,
            "label": "low_energy_pause",
            "rms": round(float(energy_val), 4),
            "zscore": round(float(energy_zscore), 2),
            "note": "Posible pausa o volumen bajo"
        })

# Ordenar por timestamp
vocal_events.sort(key=lambda e: e["timestamp"])

# Actualizar JSON
behavioral["vocal_events"] = vocal_events
behavioral["duration_seconds"] = round(duration, 1)
behavioral["status"] = "visual_vocal_complete — pendiente verbal (Whisper)"

with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(behavioral, f, indent=2, ensure_ascii=False)

print(f"\n[BEACON] Capa Vocal completada!")
print(f"   Eventos vocales detectados: {len(vocal_events)}")
print(f"   JSON actualizado: {JSON_OUT}")

# Resumen
pitch_events = [e for e in vocal_events if "pitch" in e["label"]]
energy_high = [e for e in vocal_events if "high_energy" in e["label"]]
pauses = [e for e in vocal_events if "pause" in e["label"]]

print(f"\n[BEACON] Resumen vocal:")
print(f"   Picos de pitch: {len(pitch_events)}")
print(f"   Alta energía: {len(energy_high)}")
print(f"   Pausas/bajo volumen: {len(pauses)}")

if pitch_events:
    print(f"\n   Muestra pitch spikes:")
    for e in pitch_events[:3]:
        print(f"   t={e['timestamp']:5.1f}s | f0={e['value_hz']:.0f}Hz (baseline={e['baseline_hz']:.0f}Hz)")
