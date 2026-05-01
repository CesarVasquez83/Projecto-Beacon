import json
from pathlib import Path

BASE = Path("/mnt/c/Users/a2000/Desktop/PROYECTO_BEACON")
JSON_PATH = BASE / "json_output" / "behavioral_camila.json"
REPORT_PATH = BASE / "json_output" / "informe_camila.txt"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    BEHAVIORAL_JSON = json.load(f)

import anthropic
from datetime import datetime

print("=" * 60)
print("  BEACON — Behavioral Expression & Communication Observation Network")
print(f"  {BEHAVIORAL_JSON['interview_id']} | {BEHAVIORAL_JSON['candidate_alias']} | {BEHAVIORAL_JSON['position']}")
print(f"  Capas: Visual={len(BEHAVIORAL_JSON['visual_events'])} | Vocal={len(BEHAVIORAL_JSON['vocal_events'])} | Verbal={len(BEHAVIORAL_JSON['transcript'])} segmentos | Flags={len(BEHAVIORAL_JSON['discrepancy_flags'])}")
print("=" * 60)

api_key = input("\nIngresa tu Anthropic API Key: ").strip()
if not api_key:
    print("ERROR: API Key requerida")
    exit(1)

client = anthropic.Anthropic(api_key=api_key)

prompt = f"""Eres un analista conductual directo y sin filtros para el sistema BEACON. Tu trabajo es decirle al entrevistador EXACTAMENTE lo que los datos muestran, sin suavizarlo.

REGLAS:
- Llama a las cosas por su nombre. Si hay señales de inseguridad, dilo. Si hay indicios de ocultamiento, dilo. Si el patrón sugiere mentira, dilo.
- No uses "posible", "podría", "tal vez" a menos que realmente haya duda.
- Cuando veas discrepancia entre lo que dice la boca y lo que dice el cuerpo, señálalo CLARO.
- Prioriza PATRONES REPETIDOS sobre eventos aislados.
- Usa un tono directo, de colega a colega. Sin corrección política.
- NO recomiendes contratar o descartar. De eso se encarga el humano.

ESTRUCTURA DE RESPUESTA — exactamente estas 4 secciones:

1. RESUMEN EJECUTIVO
[2-3 frases directas: ¿qué muestra este candidato? ¿es confiable? ¿hay algo que no cuadra?]

2. SEÑALES DE ALERTA
[Lista las discrepancias más fuertes, sin eufemismos. Si detectas patrones de ansiedad, ocultamiento o posible engaño, dilo.]

3. LÍNEA DE TIEMPO CONDUCTUAL
[Recorre el video en orden cronológico. Para cada momento clave, di qué pasó en cada capa y qué significa.]

4. PREGUNTAS PARA ROMPER EL DISCURSO
[Preguntas directas para el entrevistador, diseñadas para presionar donde los datos muestran fisuras. No preguntas genéricas.]

DATOS DE LA ENTREVISTA:
{json.dumps(BEHAVIORAL_JSON, indent=2, ensure_ascii=False)}"""

print("\n[ Analizando con Claude Sonnet — modo sin filtros ]\n")

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1800,
    messages=[{"role": "user", "content": prompt}]
)

report = message.content[0].text

# Guardar informe
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
full_report = f"""================================================================
  BEACON — INFORME DE ANÁLISIS CONDUCTUAL
================================================================
  Entrevista: {BEHAVIORAL_JSON['interview_id']}
  Candidato: {BEHAVIORAL_JSON['candidate_alias']}
  Posición:  {BEHAVIORAL_JSON['position']}
  Duración:  {BEHAVIORAL_JSON['duration_seconds']}s
  Generado:  {timestamp}
  Capas:     Visual={len(BEHAVIORAL_JSON['visual_events'])} | Vocal={len(BEHAVIORAL_JSON['vocal_events'])} | Verbal={len(BEHAVIORAL_JSON['transcript'])} | Flags={len(BEHAVIORAL_JSON['discrepancy_flags'])}
================================================================

{report}

================================================================
  BEACON v1.0 | Análisis conductual directo
  Guardrails: sin juicios de contratación
================================================================
"""

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(full_report)

print("=" * 60)
print("  ANÁLISIS BEACON — RESULTADO")
print("=" * 60)
print()
print(report)
print()
print("=" * 60)
print(f"  Informe guardado en: {REPORT_PATH}")
print("=" * 60)
