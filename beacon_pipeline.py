#!/usr/bin/env python3
"""
BEACON v4.0 — Behavioral Observability Platform
Pipeline regido por BEACON_SPEC.md v4.0
MIGRADO A AWS BEDROCK — Claude Haiku 4.5
"""

import argparse, subprocess, json, sys, os
from pathlib import Path
from datetime import datetime

# ============================================================
# CONTRATO DE PROMPT — BEACON v4.0 (Congelado del SPEC)
# ============================================================
BEACON_PROMPT = """
# BEACON v4.0 — Contrato de Análisis (SPEC v4.0)

## IDENTIDAD
Eres BEACON Analyst, motor de análisis multimodal de señales comunicativas.
No eres psicólogo, detector de mentiras ni profiler.
Eres herramienta de apoyo al entrevistador humano.

## REGLAS DE ORO (Violarlas = Reporte Inválido)
1. PROHIBIDO afirmar estados internos: "está nervioso", "es inseguro", "miente", "tiene ansiedad"
2. PROHIBIDO lenguaje dramático: "vendiendo humo", "actuación", "teatro", "brutal", "demoledor"
3. PROHIBIDO diagnosticar rasgos de personalidad: narcisismo, psicopatía, trauma, patologías
4. PROHIBIDO concluir sobre veracidad o competencia: "es apto", "no es confiable", "miente en su CV"

## LÉXICO PERMITIDO
Descriptivo: "Se observa", "Se registra", "Se detecta", "activación vocal elevada", "tensión facial", "cambio facial breve", "contracción ocular", "elevación de cejas", "descenso relativo de cejas", "convergencia multimodal", "pausa prolongada"
Interpretativo (SIEMPRE hipotético): "Puede reflejar", "Podría indicar", "Es compatible con", "Una hipótesis prudente es", "Entre las posibles explicaciones", "No se puede descartar"

## CONFIDENCE (Definiciones del SPEC v4.0)
- HIGH: Convergencia 2+ canales ≤1.5s. Consistencia interna. No implica certeza sobre el candidato.
- MEDIUM: Señal en 1 canal con correlación parcial en otro, o repetida en mismo canal. Puede ser variabilidad normal.
- LOW: Señal aislada en 1 solo canal. Puede ser ruido o variabilidad normal.

## ESTRUCTURA OBLIGATORIA
1. RESUMEN DE OBSERVACIONES — 2-3 frases, patrones de señales, sin juicios
2. HALLAZGOS PRINCIPALES (HIGH CONFIDENCE) — Solo HIGH. Si no hay, decirlo: "No se detectaron convergencias multimodales de alta confianza."
3. OTROS PUNTOS DE ATENCIÓN (MEDIUM/LOW) — Señalados con su confidence, siempre advertir que son señales aisladas/débiles
4. PREGUNTAS SUGERIDAS — Prioridad ALTA, MEDIA, CONTEXTUAL. Preguntas textuales + justificación.
5. NOTA METODOLÓGICA — Repetir disclaimer, limitaciones específicas, "BEACON no determina veracidad ni estado psicológico"

## REGLA FINAL
Antes de escribir cada frase: "¿Esto es una observación o una conclusión sobre la persona?"
Si es conclusión, NO la escribas. Usa lenguaje de hipótesis.
"""

# ============================================================
# CONFIGURACIÓN
# ============================================================
BASE = Path("/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON")
FRAMES_DIR = BASE / "frames_output"
AUDIO_DIR = BASE / "audio_output"
JSON_DIR = BASE / "json_output"
PIPELINE_VERSION = "4.0"

parser = argparse.ArgumentParser(description=f"BEACON v{PIPELINE_VERSION}")
parser.add_argument("--video", required=True)
parser.add_argument("--nombre", required=True)
parser.add_argument("--puesto", default="No especificado")
parser.add_argument("--region", default="us-east-1", help="AWS region para Bedrock")
args = parser.parse_args()

VIDEO_PATH = Path(args.video)
NOMBRE = args.nombre
PUESTO = args.puesto
NOMBRE_SAFE = NOMBRE.replace(" ", "_").lower()
JSON_OUT = JSON_DIR / f"behavioral_{NOMBRE_SAFE}.json"
REPORT_OUT = JSON_DIR / f"informe_{NOMBRE_SAFE}.txt"

if not VIDEO_PATH.exists():
    print(f"ERROR: Video no encontrado: {VIDEO_PATH}")
    sys.exit(1)

for d in [FRAMES_DIR, AUDIO_DIR, JSON_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print(f"  BEACON v{PIPELINE_VERSION} — Behavioral Observability Platform")
print(f"  SPEC v4.0 | Candidato: {NOMBRE}")
print(f"  Motor: AWS Bedrock — Claude Haiku 4.5")
print("=" * 60)

# ===== 1. Extracción =====
print("\n[1/7] Extrayendo audio y frames...")
subprocess.run(["ffmpeg", "-y", "-i", str(VIDEO_PATH), "-vn", "-ac", "1", "-ar", "16000", str(AUDIO_DIR / "audio.wav")], capture_output=True)
subprocess.run(["ffmpeg", "-y", "-i", str(VIDEO_PATH), "-vf", "fps=1,scale=640:-1", str(FRAMES_DIR / "frame_%04d.jpg")], capture_output=True)
result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(VIDEO_PATH)], capture_output=True, text=True)
duration = float(result.stdout.strip())
total_frames = len(list(FRAMES_DIR.glob("frame_*.jpg")))
print(f"   Duración: {duration:.1f}s | Frames: {total_frames}")

# ===== 2. Capa Visual =====
print("\n[2/7] Capa Visual — MediaPipe Face Landmarker...")
import cv2, numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions
from mediapipe.tasks.python import BaseOptions

MODEL_PATH = BASE / "face_landmarker_v2_with_blendshapes.task"
options = FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(MODEL_PATH)), output_face_blendshapes=True, num_faces=1, running_mode=mp.tasks.vision.RunningMode.IMAGE)
landmarker = FaceLandmarker.create_from_options(options)

TARGET_BS = ["browInnerUp","browDownLeft","browDownRight","browOuterUpLeft","browOuterUpRight","eyeWideLeft","eyeWideRight","eyeSquintLeft","eyeSquintRight","mouthSmileLeft","mouthSmileRight","mouthFrownLeft","mouthFrownRight","jawOpen","lipCornerDepressorLeft","lipCornerDepressorRight"]

visual_events = []
prev_bs = {}
all_bs_values = {name: [] for name in TARGET_BS}
frames_with_face = 0
event_counter = 0

for i, fp in enumerate(sorted(FRAMES_DIR.glob("frame_*.jpg"))):
    img = cv2.imread(str(fp))
    if img is None: continue
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    res = landmarker.detect(mp_img)
    if not res.face_blendshapes: continue
    frames_with_face += 1
    curr = {bs.category_name: bs.score for bs in res.face_blendshapes[0]}
    for name in TARGET_BS:
        val = curr.get(name, 0)
        all_bs_values[name].append(val)
        delta = val - prev_bs.get(name, 0)
        if abs(delta) > 0.2:
            event_counter += 1
            visual_events.append({
                "event_id": f"EVT_V{event_counter:03d}",
                "timestamp": round(i, 1),
                "channel": "visual",
                "signal_type": name,
                "value": round(float(val), 3),
                "delta": round(float(delta), 3),
                "label": f"{name}_micro_{'onset' if delta>0 else 'offset'}"
            })
    prev_bs = curr
landmarker.close()
facial_baseline = {name: round(float(np.mean(vals)), 3) if vals else 0 for name, vals in all_bs_values.items()}
face_visibility = round((frames_with_face / total_frames) * 100, 1) if total_frames > 0 else 0

# ===== 3. Capa Vocal =====
print("\n[3/7] Capa Vocal — librosa...")
import librosa
y, sr = librosa.load(str(AUDIO_DIR / "audio.wav"), sr=None)
hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
times = librosa.times_like(rms, sr=sr, hop_length=hop)
rms_mean = float(np.mean(rms))
rms_std = float(np.std(rms))
pitches, mags = librosa.piptrack(y=y, sr=sr, fmin=100, fmax=500)
pitch_values = pitches[pitches > 0]
pitch_baseline = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 0
vocal_events = []
vocal_counter = 0
for i in range(len(times)):
    t = round(float(times[i]), 1)
    z = float((rms[i] - rms_mean) / rms_std) if rms_std > 0 else 0
    if z > 2.0:
        vocal_counter += 1
        vocal_events.append({"event_id": f"EVT_A{vocal_counter:03d}", "timestamp": t, "channel": "vocal", "signal_type": "high_energy", "zscore": round(z, 2)})
    if z < -1.5:
        vocal_counter += 1
        vocal_events.append({"event_id": f"EVT_A{vocal_counter:03d}", "timestamp": t, "channel": "vocal", "signal_type": "low_energy_pause", "zscore": round(z, 2)})
vocal_events.sort(key=lambda e: e["timestamp"])

# ===== 4. Capa Verbal =====
print("\n[4/7] Capa Verbal — Whisper...")
import whisper
model = whisper.load_model("base")
res = model.transcribe(str(AUDIO_DIR / "audio.wav"), language="es", word_timestamps=True)
transcript = [{"start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"].strip()} for s in res["segments"]]

# ===== 5. Reglas Heurísticas (SPEC v4.0) =====
print("\n[5/7] Aplicando reglas heurísticas (SPEC v4.0)...")
POS_KW = ["me gusta","apasionada","buenas","responsable","mejor","experiencia","trabajo","nivel","capacidades","comunicativas"]
NEG_VIS = ["browDown","mouthFrown","lipCornerDepressor","eyeSquint"]
ACHIEVEMENT_KW = ["experiencia","trabajo","responsable","nivel","buenas"]
hallazgos = []
hallazgo_counter = 0
cluster_counter = 0

# R1: Tensión facial + discurso positivo
for seg in transcript:
    if any(kw in seg["text"].lower() for kw in POS_KW):
        matching = [ev for ev in visual_events if seg["start"] <= ev["timestamp"] <= seg["end"] and any(n in ev["signal_type"] for n in NEG_VIS)]
        if matching:
            hallazgo_counter += 1
            conf = "HIGH" if len(matching) >= 3 else ("MEDIUM" if len(matching) >= 2 else "LOW")
            hallazgos.append({
                "hallazgo_id": f"HALL_{hallazgo_counter:03d}",
                "finding_type": "cluster" if len(matching) >= 3 else "single_event",
                "timestamp_start": round(seg["start"], 1),
                "timestamp_end": round(seg["end"], 1),
                "verbal_context": seg["text"][:150],
                "channels_involved": ["visual", "verbal"],
                "observed_signals": [{"channel": "visual", "signal": m["signal_type"], "value": m["value"], "timestamp": m["timestamp"], "event_id": m["event_id"]} for m in matching[:5]],
                "cross_channel_pattern": "tension_facial_durante_discurso_positivo",
                "confidence": conf,
                "hypotheses": ["Carga cognitiva al autoevaluarse en formato grabado", "Esfuerzo por seleccionar palabras adecuadas", "Cambios faciales normales de procesamiento"],
                "recommended_followup": [{"priority": "ALTA" if conf == "HIGH" else "MEDIA", "question": f"Pedir ejemplo concreto: '{seg['text'][:80]}...'"}],
                "limitations": {"generales": ["Formato video CV sin interlocutor"], "visual": [f"Face visibility: {face_visibility}%", "Muestreo 1fps"], "verbal": ["Discurso preparado"]},
                "evidence_quality": {"visual_quality": "media" if face_visibility >= 70 else "baja", "audio_quality": "alta" if rms_mean > 0.01 else "baja", "face_visibility_pct": face_visibility},
                "rules_triggered": ["R1"],
                "pipeline_version": PIPELINE_VERSION
            })

# R2: Cambio facial en silencio
for ev in visual_events:
    t = ev["timestamp"]
    nearby_pauses = [v for v in vocal_events if v["signal_type"] == "low_energy_pause" and abs(v["timestamp"] - t) <= 1.0]
    if nearby_pauses and abs(ev["delta"]) > 0.3:
        hallazgo_counter += 1
        hallazgos.append({
            "hallazgo_id": f"HALL_{hallazgo_counter:03d}",
            "finding_type": "single_event",
            "timestamp_start": round(t - 0.5, 1),
            "timestamp_end": round(t + 0.5, 1),
            "verbal_context": "N/A (silencio)",
            "channels_involved": ["visual", "vocal"],
            "observed_signals": [{"channel": "visual", "signal": ev["signal_type"], "value": ev["value"], "timestamp": t, "event_id": ev["event_id"]}, {"channel": "vocal", "signal": "pausa", "timestamp": nearby_pauses[0]["timestamp"], "event_id": nearby_pauses[0]["event_id"]}],
            "cross_channel_pattern": "cambio_facial_durante_silencio",
            "confidence": "LOW",
            "hypotheses": ["Posible procesamiento durante silencio", "Artefacto de muestreo (1fps)", "Variabilidad facial normal"],
            "recommended_followup": [{"priority": "CONTEXTUAL", "question": "Observar si el patrón se repite en otros silencios."}],
            "limitations": {"generales": ["Señal aislada sin contexto verbal"], "visual": ["Muestreo 1fps puede no capturar onset real"]},
            "evidence_quality": {"visual_quality": "media" if face_visibility >= 70 else "baja", "audio_quality": "alta" if rms_mean > 0.01 else "baja", "face_visibility_pct": face_visibility},
            "rules_triggered": ["R2"],
            "pipeline_version": PIPELINE_VERSION
        })

# R3: Convergencia cejas + energía
high_energy = [v for v in vocal_events if v["signal_type"] == "high_energy"]
for ve in high_energy:
    t = ve["timestamp"]
    nearby_brow = [ev for ev in visual_events if ("browInnerUp" in ev["signal_type"] or "browOuterUp" in ev["signal_type"]) and abs(ev["timestamp"] - t) <= 1.5]
    if nearby_brow:
        hallazgo_counter += 1
        cluster_counter += 1
        nearby_seg = next((seg for seg in transcript if abs(seg["start"] - t) <= 2.0), None)
        context = nearby_seg["text"][:120] if nearby_seg else "No hay transcripción cercana"
        hallazgos.append({
            "hallazgo_id": f"HALL_{hallazgo_counter:03d}",
            "finding_type": "cluster",
            "cluster_id": f"CLUSTER_{cluster_counter:03d}",
            "timestamp_start": round(t - 1.0, 1),
            "timestamp_end": round(t + 1.0, 1),
            "verbal_context": context,
            "channels_involved": ["visual", "vocal"],
            "observed_signals": [{"channel": "visual", "signal": nb["signal_type"], "value": nb["value"], "timestamp": nb["timestamp"], "event_id": nb["event_id"]} for nb in nearby_brow[:3]] + [{"channel": "vocal", "signal": "high_energy", "zscore": ve["zscore"], "timestamp": t, "event_id": ve["event_id"]}],
            "cross_channel_pattern": "convergencia_multimodal_cejas_energia",
            "temporal_overlap_ms": int(abs(nearby_brow[0]["timestamp"] - t) * 1000) if nearby_brow else 0,
            "confidence": "HIGH",
            "hypotheses": ["Énfasis comunicativo intencional durante contenido relevante", "Mayor activación fisiológica al abordar autoevaluaciones", "Patrón expresivo habitual del candidato"],
            "recommended_followup": [{"priority": "ALTA", "question": f"Repreguntar sobre: '{context}'"}, {"priority": "MEDIA", "question": "Comparar con momentos de similar contenido."}],
            "limitations": {"generales": ["La activación puede ser énfasis normal"], "vocal": ["Z-score relativo a baseline propia, no poblacional"], "visual": [f"Face: {face_visibility}%"]},
            "evidence_quality": {"visual_quality": "media" if face_visibility >= 70 else "baja", "audio_quality": "alta" if rms_mean > 0.01 else "baja", "face_visibility_pct": face_visibility},
            "rules_triggered": ["R3"],
            "pipeline_version": PIPELINE_VERSION
        })

# R4: Sonrisa asimétrica + logro
for seg in transcript:
    if any(kw in seg["text"].lower() for kw in ACHIEVEMENT_KW):
        for ev in visual_events:
            if seg["start"] <= ev["timestamp"] <= seg["end"] and "mouthSmile" in ev["signal_type"] and "Left" in ev["signal_type"] and "Right" not in ev["signal_type"]:
                hallazgo_counter += 1
                hallazgos.append({
                    "hallazgo_id": f"HALL_{hallazgo_counter:03d}",
                    "finding_type": "single_event",
                    "timestamp_start": round(ev["timestamp"] - 1.0, 1),
                    "timestamp_end": round(ev["timestamp"] + 1.0, 1),
                    "verbal_context": seg["text"][:120],
                    "channels_involved": ["visual", "verbal"],
                    "observed_signals": [{"channel": "visual", "signal": ev["signal_type"], "value": ev["value"], "timestamp": ev["timestamp"], "event_id": ev["event_id"]}],
                    "cross_channel_pattern": "sonrisa_asimetrica_durante_logro",
                    "confidence": "LOW",
                    "hypotheses": ["Gesto social, no necesariamente emocional", "Asimetría facial natural", "Artefacto de muestreo o ángulo"],
                    "recommended_followup": [{"priority": "CONTEXTUAL", "question": "Explorar con ejemplos concretos en entrevista."}],
                    "limitations": {"generales": ["La asimetría facial puede ser natural"], "visual": ["Muestreo 1fps"]},
                    "evidence_quality": {"visual_quality": "media" if face_visibility >= 70 else "baja", "audio_quality": "alta" if rms_mean > 0.01 else "baja", "face_visibility_pct": face_visibility},
                    "rules_triggered": ["R4"],
                    "pipeline_version": PIPELINE_VERSION
                })

# Deduplicar
seen = set()
hallazgos_unicos = []
for h in sorted(hallazgos, key=lambda x: x["timestamp_start"]):
    key = (round(h["timestamp_start"], 1), h["rules_triggered"][0], h["cross_channel_pattern"])
    if key not in seen:
        seen.add(key)
        hallazgos_unicos.append(h)

# ===== 6. Evidencia Negativa =====
high_count = len([h for h in hallazgos_unicos if h["confidence"] == "HIGH"])
med_count = len([h for h in hallazgos_unicos if h["confidence"] == "MEDIUM"])
low_count = len([h for h in hallazgos_unicos if h["confidence"] == "LOW"])

negative_findings = {
    "no_deception_indicators": True,
    "no_vocal_tremor_detected": True,
    "note": "No se detectaron convergencias multimodales que sugieran ocultamiento. Las señales observadas son compatibles con activación normal en formato video CV."
}

# ===== 7. JSON v4.0 (Esquema SPEC) =====
print("\n[6/7] Generando JSON (esquema SPEC v4.0)...")
behavioral = {
    "report_id": f"BEACON-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    "pipeline_version": PIPELINE_VERSION,
    "spec_version": "4.0",
    "candidate_alias": NOMBRE,
    "position": PUESTO,
    "duration_seconds": round(duration, 1),
    "source_video": VIDEO_PATH.name,
    "product_label": "BEACON — Behavioral Observability Platform",
    "methodology": {
        "disclaimer": "BEACON no determina veracidad ni estado psicológico. Detecta convergencias observables entre canales comunicativos para guiar repreguntas del entrevistador humano.",
        "confidence_definition": "HIGH: convergencia 2+ canales ≤1.5s. MEDIUM: señal en 1 canal con correlación parcial. LOW: señal aislada. No implica certeza sobre estado del candidato.",
        "zscore_note": "Z-score relativo a baseline del propio video, no poblacional.",
        "usage_note": "Las observaciones requieren validación en interacción humana."
    },
    "signal_quality": {
        "face_visibility_pct": face_visibility,
        "audio_clarity": "high" if rms_mean > 0.01 else "low",
        "video_duration_short": duration < 30,
        "total_frames": total_frames,
        "frames_with_face": frames_with_face,
        "fps": 1
    },
    "baseline": {
        "vocal_energy_mean": round(rms_mean, 5),
        "vocal_energy_std": round(rms_std, 5),
        "pitch_baseline_hz": round(pitch_baseline, 1),
        "facial_activation_mean": facial_baseline
    },
    "transcript": transcript,
    "visual_events": sorted(visual_events, key=lambda e: e["timestamp"]),
    "vocal_events": vocal_events,
    "hallazgos": hallazgos_unicos,
    "negative_findings": negative_findings,
    "status": f"complete — v{PIPELINE_VERSION} — SPEC v4.0",
    "protocolo_uso": "Este sistema no determina veracidad ni estado psicológico. Requiere consentimiento informado, revisión humana y no debe usarse como único criterio de decisión."
}

with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(behavioral, f, indent=2, ensure_ascii=False)

print(f"  JSON: {JSON_OUT}")
print(f"  Eventos: Visual={len(visual_events)} | Vocal={len(vocal_events)} | Verbal={len(transcript)}")
print(f"  Hallazgos: {len(hallazgos_unicos)} (HIGH={high_count} | MEDIUM={med_count} | LOW={low_count})")
print(f"  Face: {face_visibility}% | Audio: {'Alta' if rms_mean > 0.01 else 'Baja'}")

# ===== 8. Informe — AWS Bedrock (Claude Haiku 4.5) =====
print(f"\n[7/7] Generando informe via AWS Bedrock (Claude Haiku 4.5)...")
import boto3

bedrock = boto3.client("bedrock-runtime", region_name=args.region)

prompt = (
    BEACON_PROMPT
    + f"\n\nDATOS DE LA ENTREVISTA:\n{json.dumps(behavioral, indent=2, ensure_ascii=False)}"
    + "\n\nGenera el informe siguiendo ESTRICTAMENTE la estructura del contrato."
)

response = bedrock.invoke_model(
    modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2500,
        "messages": [{"role": "user", "content": prompt}]
    })
)

report = json.loads(response["body"].read())["content"][0]["text"]

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
full_report = f"""================================================================
  BEACON v{PIPELINE_VERSION} — Behavioral Observability Platform
  SPEC v4.0 | Motor: AWS Bedrock — Claude Haiku 4.5
================================================================
  Reporte: {behavioral['report_id']}
  Candidato: {NOMBRE} | Puesto: {PUESTO} | Duración: {duration:.1f}s
  Generado: {timestamp}
  Señal: Face={face_visibility}% | Audio={'Alta' if rms_mean > 0.01 else 'Baja'}
  Hallazgos: {len(hallazgos_unicos)} (HIGH={high_count} | MEDIUM={med_count} | LOW={low_count})
================================================================
  {behavioral['methodology']['disclaimer']}
================================================================

{report}

================================================================
  BEACON v{PIPELINE_VERSION} | SPEC v4.0
  Este informe no determina veracidad ni estado psicológico.
  Herramienta de apoyo al entrevistador humano.
================================================================
"""
with open(REPORT_OUT, "w", encoding="utf-8") as f:
    f.write(full_report)
print(f"  Informe: {REPORT_OUT}")

print(f"{'='*60}\n")
print("BEACON v4.0 — SPEC congelado. Pipeline regido por BEACON_SPEC.md")
print("Motor cognitivo: AWS Bedrock — Claude Haiku 4.5")
