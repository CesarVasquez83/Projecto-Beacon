BEACON v4.1 — Behavioral Observability Platform

BEACON es una plataforma de apoyo a entrevistas basada en análisis multimodal 
de señales comunicativas. Procesa video y extrae tres capas de información:

- Capa Visual: cambios faciales breves detectados con MediaPipe Face Landmarker
- Capa Vocal: energía y pausas analizadas con librosa
- Capa Verbal: transcripción con timestamps mediante OpenAI Whisper

Un motor de reglas heurísticas (R1-R4) detecta convergencias entre canales 
y genera hallazgos estructurados con:
- Confidence levels (HIGH/MEDIUM/LOW)
- Hipótesis múltiples (nunca narrativa única)
- Limitaciones específicas por hallazgo
- Preguntas sugeridas priorizadas (ALTA/MEDIA/CONTEXTUAL)

BEACON no determina veracidad ni estado psicológico. 
Es una herramienta de apoyo al entrevistador humano.
