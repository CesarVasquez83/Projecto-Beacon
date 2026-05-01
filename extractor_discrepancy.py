import json
from pathlib import Path

BASE = Path("/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON")
JSON_IN = BASE / "json_output" / "behavioral_camila.json"
JSON_OUT = BASE / "json_output" / "behavioral_camila.json"

# Cargar JSON
with open(JSON_IN, "r", encoding="utf-8") as f:
    behavioral = json.load(f)

visual = behavioral["visual_events"]
vocal = behavioral["vocal_events"]
transcript = behavioral["transcript"]

discrepancy_flags = []

# ===== REGLA 1: Micro-ceño + discurso positivo =====
# Si hay browDown (ceño fruncido) mientras el discurso es positivo, flag
positive_keywords = ["me gusta", "apasionada", "buenas", "responsable", "mejor", "nuevas experiencias"]
negative_visual = ["browDown", "mouthFrown", "lipCornerDepressor", "eyeSquint"]

for seg in transcript:
    seg_start = seg["start"]
    seg_end = seg["end"]
    text_lower = seg["text"].lower()
    
    # ¿El discurso es positivo?
    is_positive = any(kw in text_lower for kw in positive_keywords)
    
    if is_positive:
        # Buscar eventos visuales negativos en este segmento
        for ev in visual:
            if seg_start <= ev["timestamp"] <= seg_end:
                if any(neg in ev["blendshape"] for neg in negative_visual):
                    discrepancy_flags.append({
                        "timestamp": ev["timestamp"],
                        "segment": seg["text"],
                        "verbal": "positivo",
                        "visual": f"{ev['blendshape']} ({ev['label']})",
                        "vocal": "pendiente",
                        "layers_mismatch": ["verbal-positive", f"visual-{ev['blendshape']}"],
                        "suggestion": "Explorar si hay tensión oculta detrás del discurso positivo."
                    })

# ===== REGLA 2: Pausa + microexpresión intensa =====
for ev in visual:
    t = ev["timestamp"]
    # Buscar pausas vocales cercanas (±1s)
    nearby_pauses = [v for v in vocal if "pause" in v["label"] and abs(v["timestamp"] - t) <= 1.0]
    if nearby_pauses and abs(ev["delta"]) > 0.3:
        # Solo si el delta es grande (cambio facial intenso)
        discrepancy_flags.append({
            "timestamp": t,
            "segment": "N/A (pausa)",
            "verbal": "silencio",
            "visual": f"{ev['blendshape']} (delta={ev['delta']:.2f})",
            "vocal": "pausa detectada",
            "layers_mismatch": ["verbal-silence", f"visual-{ev['blendshape']}", "vocal-pause"],
            "suggestion": "Microexpresión intensa durante silencio. Posible procesamiento emocional."
        })

# ===== REGLA 3: Alta energía vocal + microexpresión de cejas arriba (sorpresa/alerta) =====
high_energy_events = [v for v in vocal if "high_energy" in v["label"]]
for ve in high_energy_events:
    t = ve["timestamp"]
    # Buscar browInnerUp/OuterUp cercanos
    nearby_brow_up = [ev for ev in visual 
                      if "browInnerUp" in ev["blendshape"] or "browOuterUp" in ev["blendshape"]
                      if abs(ev["timestamp"] - t) <= 1.5]
    if nearby_brow_up:
        discrepancy_flags.append({
            "timestamp": t,
            "segment": "Ver transcripción cercana",
            "verbal": "por verificar",
            "visual": "brow raise (sorpresa/alerta)",
            "vocal": "high_energy",
            "layers_mismatch": ["vocal-arousal", "visual-alert"],
            "suggestion": "Elevación de cejas + alta energía vocal. Posible énfasis o ansiedad."
        })

# ===== REGLA 4: mouthSmile asimétrico + discurso de logro =====
achievement_keywords = ["experiencia", "trabajo", "responsable", "nivel", "buenas"]
for seg in transcript:
    seg_start = seg["start"]
    seg_end = seg["end"]
    text_lower = seg["text"].lower()
    
    has_achievement = any(kw in text_lower for kw in achievement_keywords)
    
    if has_achievement:
        for ev in visual:
            if seg_start <= ev["timestamp"] <= seg_end:
                if "mouthSmile" in ev["blendshape"] and "Left" in ev["blendshape"] and "Right" not in ev["blendshape"]:
                    discrepancy_flags.append({
                        "timestamp": ev["timestamp"],
                        "segment": seg["text"],
                        "verbal": "logro/experiencia",
                        "visual": "smile_asimetrico (posible sonrisa social)",
                        "vocal": "por verificar",
                        "layers_mismatch": ["verbal-positive", "visual-asymmetric_smile"],
                        "suggestion": "Sonrisa asimétrica al mencionar logro. Puede ser gesto social, no emocional."
                    })

# Eliminar duplicados (mismo timestamp + misma sugerencia)
seen = set()
unique_flags = []
for flag in sorted(discrepancy_flags, key=lambda f: f["timestamp"]):
    key = (flag["timestamp"], flag["suggestion"])
    if key not in seen:
        seen.add(key)
        unique_flags.append(flag)

# Actualizar JSON
behavioral["discrepancy_flags"] = unique_flags
behavioral["status"] = "complete — all layers + discrepancy analysis"

with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(behavioral, f, indent=2, ensure_ascii=False)

print(f"[BEACON] Análisis de discrepancias completado!")
print(f"   Discrepancias detectadas: {len(unique_flags)}")
print(f"   JSON final: {JSON_OUT}")

if unique_flags:
    print(f"\n[BEACON] Banderas de discrepancia:")
    for i, flag in enumerate(unique_flags, 1):
        print(f"\n   #{i} | t={flag['timestamp']:.1f}s")
        print(f"   Verbal: {flag['verbal']}")
        print(f"   Visual: {flag['visual']}")
        print(f"   Sugerencia: {flag['suggestion']}")
