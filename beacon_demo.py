import anthropic
import json

BEHAVIORAL_JSON = {
    "interview_id": "BEACON-TEST-001",
    "candidate_alias": "Candidato A",
    "duration_seconds": 185,
    "position": "Senior Backend Engineer",
    "transcript": [
        {"start": 0.0, "end": 8.5, "text": "Buenas tardes, gracias por recibirme. Tengo ocho años de experiencia en backend."},
        {"start": 9.0, "end": 22.0, "text": "En mi último proyecto lideré la migración de un monolito a microservicios, reduciendo latencia en un 40%."},
        {"start": 23.0, "end": 35.0, "text": "Trabajé con Kafka, Docker, Kubernetes y PostgreSQL. Fue un desafío técnico importante."},
        {"start": 45.0, "end": 58.0, "text": "Bueno, el trabajo en equipo siempre fue complicado para mí... digo, fue un reto que superamos juntos."},
        {"start": 70.0, "end": 85.0, "text": "¿Manejo de presión? Sí, absolutamente. Me crezco bajo presión. Siempre entrego."},
        {"start": 100.0, "end": 115.0, "text": "El conflicto con el PM fue resuelto profesionalmente. No hubo problema real."},
        {"start": 130.0, "end": 142.0, "text": "Mi mayor debilidad... soy demasiado perfeccionista, a veces me quedo hasta tarde puliendo detalles."},
        {"start": 155.0, "end": 170.0, "text": "¿Por qué dejé mi último trabajo? Fue una decisión mutua. Crecimiento profesional."}
    ],
    "visual_events": [
        {"timestamp": 23.5, "label": "micro_frown", "confidence": 0.87, "context_utterance": "Trabajé con Kafka, Docker, Kubernetes..."},
        {"timestamp": 45.2, "label": "micro_smile_asymmetry", "confidence": 0.73, "context_utterance": "...el trabajo en equipo siempre fue complicado para mí..."},
        {"timestamp": 46.1, "label": "self_touch", "confidence": 0.91, "context_utterance": "...digo, fue un reto que superamos juntos."},
        {"timestamp": 70.8, "label": "micro_brow_raise", "confidence": 0.84, "context_utterance": "¿Manejo de presión? Sí, absolutamente."},
        {"timestamp": 100.5, "label": "micro_frown_lip_depress", "confidence": 0.81, "context_utterance": "El conflicto con el PM fue resuelto profesionalmente..."},
        {"timestamp": 131.0, "label": "head_tilt", "confidence": 0.89, "context_utterance": "Mi mayor debilidad..."},
        {"timestamp": 156.3, "label": "micro_smile_eyes", "confidence": 0.76, "context_utterance": "¿Por qué dejé mi último trabajo?"}
    ],
    "vocal_events": [
        {"timestamp": 22.0, "label": "pitch_increase_62%", "context_utterance": "...reduciendo latencia en un 40%."},
        {"timestamp": 45.0, "label": "rate_decrease_37%", "context_utterance": "Bueno, el trabajo en equipo siempre fue complicado para mí..."},
        {"timestamp": 46.5, "label": "hesitation", "context_utterance": "...digo, fue un reto que superamos juntos."},
        {"timestamp": 70.5, "label": "pitch_increase_73%", "context_utterance": "¿Manejo de presión? Sí, absolutamente."},
        {"timestamp": 100.0, "label": "rate_increase_23%", "context_utterance": "El conflicto con el PM fue resuelto profesionalmente."},
        {"timestamp": 156.0, "label": "vocal_tension", "context_utterance": "¿Por qué dejé mi último trabajo? Fue una decisión mutua..."}
    ],
    "discrepancy_flags": [
        {"timestamp": 45.0, "verbal": "fue un reto que superamos juntos", "visual": "micro_smile_asymmetry + self_touch", "vocal": "speech_rate_drop + hesitation", "suggestion": "Explorar más sobre la experiencia real de trabajo en equipo."},
        {"timestamp": 70.5, "verbal": "Me crezco bajo presión. Siempre entrego.", "visual": "micro_brow_raise (sorpresa/alerta)", "vocal": "pitch_increase_73%", "suggestion": "Preguntar por un ejemplo concreto de presión y resultado."},
        {"timestamp": 100.0, "verbal": "No hubo problema real.", "visual": "micro_frown_lip_depress (supresión)", "vocal": "speech_rate_increase (aceleración)", "suggestion": "Indagar naturaleza real del conflicto con el PM."},
        {"timestamp": 156.0, "verbal": "Fue una decisión mutua. Crecimiento profesional.", "visual": "micro_smile_eyes (posible ironía/ambivalencia)", "vocal": "vocal_tension (jitter)", "suggestion": "Verificar circunstancias de salida del empleo anterior."}
    ]
}

PROMPT = f"""Eres un asistente técnico de análisis de entrevistas para el sistema BEACON. Tu función es resumir de forma NEUTRAL y OBJETIVA los eventos conductuales detectados.

REGLAS ESTRICTAS:
- No afirmes que el candidato mintió o es deshonesto.
- No recomiendes contratar o descartar al candidato.
- No uses lenguaje de diagnóstico psicológico.
- Describe OBSERVACIONES, no conclusiones.
- Las discrepancias entre capas son "puntos a explorar", nunca acusaciones.
- Usa timestamps concretos en formato [mm:ss].
- Sé conciso y accionable para el entrevistador.

DATOS DE LA ENTREVISTA:
{json.dumps(BEHAVIORAL_JSON, indent=2, ensure_ascii=False)}

Responde EXACTAMENTE con estas 4 secciones numeradas en español:

1. EVENTOS VISUALES DESTACADOS
2. EVENTOS VOCALES DESTACADOS
3. PUNTOS DE DISCREPANCIA ENTRE CAPAS
4. MOMENTOS SUGERIDOS PARA REPREGUNTA"""


def run_beacon():
    print("=" * 60)
    print("  BEACON — Behavioral Analysis System")
    print("  BEACON-TEST-001 | Candidato A | Senior Backend")
    print("=" * 60)
    print()

    api_key = input("Ingresa tu Anthropic API Key: ").strip()

    client = anthropic.Anthropic(api_key=api_key)

    print("\n[ Analizando con Claude Sonnet... ]\n")

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1200,
        messages=[{"role": "user", "content": PROMPT}]
    )

    result = message.content[0].text

    print("=" * 60)
    print("  ANÁLISIS BEACON — RESULTADO")
    print("=" * 60)
    print()
    print(result)
    print()
    print("=" * 60)
    print("  Guardrails activos: sin juicios de contratación")
    print("  Sin diagnóstico psicológico | Análisis neutral")
    print("=" * 60)


if __name__ == "__main__":
    run_beacon()
