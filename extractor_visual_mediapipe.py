import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions
from mediapipe.tasks.python import BaseOptions
import json
from pathlib import Path

BASE = Path("/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON")
FRAMES_DIR = BASE / "frames_output"
JSON_IN = BASE / "json_output" / "behavioral_camila.json"
JSON_OUT = BASE / "json_output" / "behavioral_camila.json"

# Cargar JSON existente
with open(JSON_IN, "r", encoding="utf-8") as f:
    behavioral = json.load(f)

# Crear FaceLandmarker con blendshapes activados
options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON/face_landmarker_v2_with_blendshapes.task"),  # Usa el modelo por defecto
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=False,
    num_faces=1,
    running_mode=mp.tasks.vision.RunningMode.IMAGE
)
landmarker = FaceLandmarker.create_from_options(options)

# Blendshapes que nos interesan para microexpresiones
TARGET_BLENDSHAPES = [
    "browInnerUp", "browDownLeft", "browDownRight", "browOuterUpLeft", "browOuterUpRight",
    "eyeWideLeft", "eyeWideRight", "eyeSquintLeft", "eyeSquintRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthPressLeft", "mouthPressRight", "jawOpen", "mouthClose",
    "lipCornerDepressorLeft", "lipCornerDepressorRight"
]

visual_events = []
prev_blendshapes = {}

# Procesar cada frame
frame_files = sorted(FRAMES_DIR.glob("frame_*.jpg"))
print(f"[BEACON] Procesando {len(frame_files)} frames con MediaPipe Face Landmarker...")

for i, frame_path in enumerate(frame_files):
    image_bgr = cv2.imread(str(frame_path))
    if image_bgr is None:
        continue
    
    # Convertir BGR a RGB y crear MediaPipe Image
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    
    # Detectar rostro y blendshapes
    result = landmarker.detect(mp_image)
    
    if not result.face_blendshapes or len(result.face_blendshapes) == 0:
        continue
    
    # Extraer blendshapes actuales del primer rostro
    current_blendshapes = {}
    for bs in result.face_blendshapes[0]:
        current_blendshapes[bs.category_name] = bs.score
    
    timestamp = round(i, 1)
    
    # Detectar microexpresiones (cambios rápidos entre frames)
    for bs_name in TARGET_BLENDSHAPES:
        current_val = current_blendshapes.get(bs_name, 0)
        prev_val = prev_blendshapes.get(bs_name, 0)
        delta = current_val - prev_val
        
        if abs(delta) > 0.2:
            event_type = "micro_onset" if delta > 0 else "micro_offset"
            visual_events.append({
                "timestamp": timestamp,
                "frame": frame_path.name,
                "label": f"{bs_name}_{event_type}",
                "blendshape": bs_name,
                "value": round(current_val, 3),
                "delta": round(delta, 3),
                "confidence": 0.85
            })
    
    prev_blendshapes = current_blendshapes.copy()

landmarker.close()
cv2.destroyAllWindows()

# Actualizar JSON
behavioral["visual_events"] = sorted(visual_events, key=lambda e: e["timestamp"])
behavioral["status"] = "visual_layer_complete — pendiente vocal (librosa) + verbal (Whisper)"

with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(behavioral, f, indent=2, ensure_ascii=False)

print(f"\n[BEACON] Capa Visual completada!")
print(f"   Eventos detectados: {len(visual_events)}")
print(f"   JSON actualizado: {JSON_OUT}")

if visual_events:
    print("\n[BEACON] Muestra de eventos detectados:")
    for ev in visual_events[:5]:
        direccion = "↑" if ev["delta"] > 0 else "↓"
        print(f"   t={ev['timestamp']:5.1f}s | {direccion} {ev['blendshape']:30s} = {ev['value']:.3f}")
