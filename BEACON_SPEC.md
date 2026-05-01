# BEACON v4.0 — Especificación Formal

## 1. Identidad del Sistema

**Nombre:** BEACON — Behavioral Expression & Communication Observation Network  
**Product Label:** Behavioral Observability Platform  
**Versión:** 4.0  
**Propósito:** Plataforma de apoyo a entrevistas basada en análisis multimodal de señales comunicativas.

**BEACON no determina veracidad ni estado psicológico. Detecta convergencias observables entre canales comunicativos para guiar repreguntas del entrevistador humano.**

---

## 2. Taxonomía Operativa (Congelada)

| Término | Definición | Scope |
|---------|------------|-------|
| **Señal** | Unidad mínima de observación: un blendshape, un z-score, un segmento de transcripción | Input |
| **Evento** | Señal que supera un umbral predefinido en un canal específico (ej: browInnerUp > 0.2 delta en 1 frame) | Detección |
| **Convergencia** | Coincidencia temporal de 2+ eventos de canales distintos dentro de una ventana de 1500ms | Análisis |
| **Cluster** | Agrupación de 3+ eventos en ventana ≤3000ms que comparten contexto verbal | Agregación |
| **Hallazgo** | Unidad de análisis: cluster o evento aislado con hipótesis, confidence, followup y limitaciones | Output |
| **Confidence** | Consistencia interna de señales en este video. HIGH=convergencia 2+ canales ≤1500ms. MEDIUM=señal en 1 canal con correlación parcial. LOW=señal aislada. | Scoring |
| **Baseline** | Promedio de activación del candidato en este video. Toda desviación es relativa a su propia baseline. | Normalización |
| **Activación** | Incremento relativo de energía vocal o intensidad de expresión facial respecto a la baseline del propio video | Descriptivo |
| **Tensión facial** | Contracción sostenida o repetida de músculos orbitales o bucales detectada por blendshapes | Descriptivo |
| **Carga cognitiva** | Esfuerzo de procesamiento inferido por pausas, titubeos o cambios faciales durante tareas verbales complejas | Interpretativo |

---

## 3. Catálogo de Reglas Heurísticas

### R1 — Tensión Facial en Discurso Positivo
- **ID:** R1
- **Condición:** `eyeSquint OR browDown OR mouthFrown OR lipCornerDepressor` durante segmento verbal con keywords positivas
- **Keywords positivas:** "me gusta", "apasionada", "buenas", "responsable", "mejor", "experiencia", "trabajo", "nivel", "capacidades", "comunicativas"
- **Confidence:** HIGH si ≥3 eventos visuales en el segmento, MEDIUM si 2, LOW si 1
- **Tipo:** `tension_facial_durante_discurso_positivo`

### R2 — Microexpresión en Silencio
- **ID:** R2
- **Condición:** Cualquier blendshape con |delta| > 0.3 coincidente con pausa vocal (z-score < -1.5) en ventana ±1.0s
- **Confidence:** LOW (señal aislada, sin contexto verbal)
- **Tipo:** `cambio_facial_durante_silencio`

### R3 — Convergencia Multimodal Cejas-Energía
- **ID:** R3
- **Condición:** `browInnerUp OR browOuterUp` coincidente con `high_energy` (z-score > 2.0) en ventana ≤1.5s
- **Confidence:** HIGH (convergencia de 2 canales)
- **Tipo:** `convergencia_multimodal_cejas_energia`

### R4 — Sonrisa Asimétrica en Declaración de Logro
- **ID:** R4
- **Condición:** `mouthSmileLeft` presente Y `mouthSmileRight` ausente durante segmento con keywords de logro
- **Keywords de logro:** "experiencia", "trabajo", "responsable", "nivel", "buenas"
- **Confidence:** LOW (señal visual aislada, posible asimetría natural)
- **Tipo:** `sonrisa_asimetrica_durante_logro`

---

## 4. Esquema JSON Formal

### 4.1 Evento Base
```json
{
  "event_id": "EVT_001",
  "timestamp": 14.4,
  "channel": "visual",
  "signal_type": "browInnerUp",
  "value": 0.801,
  "delta": 0.283,
  "label": "browInnerUp_micro_onset"
}

json
{
  "cluster_id": "CLUSTER_001",
  "type": "multimodal_cluster",
  "timestamp_start": 28.5,
  "timestamp_end": 31.1,
  "events": ["EVT_014", "EVT_015", "EVT_016"],
  "channels_involved": ["visual", "vocal"],
  "cross_channel_pattern": "convergencia_multimodal_cejas_energia",
  "temporal_overlap_ms": 870,
  "verbal_context": "...creo que soy muy responsable..."
}

json
{
  "hallazgo_id": "HALL_014",
  "finding_type": "cluster",
  "source": "CLUSTER_001",
  "confidence": "HIGH",
  "confidence_definition": "Convergencia de 2+ canales con señales claras y alineación temporal ≤1.5s. No implica certeza sobre estado del candidato.",
  "observed_signals": [
    {"channel": "visual", "signal": "browInnerUp", "value": 0.81, "timestamp": 28.0},
    {"channel": "vocal", "signal": "high_energy", "zscore": 3.37, "timestamp": 28.2}
  ],
  "hypotheses": [
    "Énfasis comunicativo intencional durante contenido relevante",
    "Mayor activación fisiológica al abordar autoevaluaciones",
    "Patrón expresivo habitual del candidato al hablar de temas que considera importantes"
  ],
  "recommended_followup": [
    {"priority": "ALTA", "question": "Pedir ejemplo concreto de responsabilidad"},
    {"priority": "MEDIA", "question": "Comparar con momentos similares del discurso"}
  ],
  "limitations": {
    "generales": ["Formato video CV sin interlocutor"],
    "visual": ["Visibilidad facial 79.2%", "Muestreo 1fps"],
    "vocal": ["Z-score relativo a baseline del propio video, no poblacional"],
    "verbal": ["Discurso preparado, no conversacional"]
  },
  "evidence_quality": {
    "visual_quality": "medium",
    "audio_quality": "high",
    "face_visibility_pct": 79.2
  },
  "rules_triggered": ["R3"]
}

5. Definición de Confidence Levels
HIGH CONFIDENCE
Definición: Convergencia de 2+ canales con señales claras y alineación temporal ≤1.5s. Consistencia interna de las señales en este video.

No implica: Certeza sobre estado del candidato, probabilidad de engaño, diagnóstico psicológico.

Uso: Priorizar exploración en entrevista.

MEDIUM CONFIDENCE
Definición: Señal presente en un canal con correlación parcial en otro canal, o señal repetida en un mismo canal en contexto relevante.

No implica: Confirmación de patrón. Puede ser variabilidad normal.

Uso: Punto de atención secundario.

LOW CONFIDENCE
Definición: Señal aislada en un solo canal, sin correlación con otros canales.

No implica: Nada. Puede ser ruido, artefacto de grabación, variabilidad normal, asimetría natural.

Uso: No se recomienda seguimiento específico salvo que se repita.

6. Protocolo de Uso Responsable
Usos Soportados
✅ Apoyo a entrevistador humano para priorizar áreas de exploración

✅ Identificación de convergencias observables entre canales comunicativos

✅ Sugerencia de repreguntas basadas en patrones detectados

✅ Análisis exploratorio en contextos de investigación con consentimiento

Usos NO Soportados
❌ Filtro automático de candidatos

❌ Detección de mentiras o veracidad

❌ Diagnóstico psicológico o psiquiátrico

❌ Perfilado de personalidad

❌ Toma de decisiones sin intervención humana

❌ Uso sin consentimiento informado del candidato

Requisitos Mínimos de Uso
Consentimiento informado del candidato

Revisión humana de todos los hallazgos

No usar como único criterio de decisión

El entrevistador tiene la última palabra

7. Léxico Permitido y Prohibido
Permitido (Descriptivo)
"Se observa", "Se registra", "Se detecta"

"Activación vocal elevada", "Tensión facial"

"Convergencia multimodal", "Pausa prolongada"

"Cambio facial breve", "Contracción ocular"

"Elevación de cejas", "Descenso relativo de cejas"

Permitido (Interpretativo Hipotético)
"Puede reflejar", "Podría indicar", "Es compatible con"

"Una hipótesis prudente es", "Entre las posibles explicaciones"

"No se puede descartar"

PROHIBIDO
Estados internos: "está nervioso", "es inseguro", "miente", "tiene ansiedad"

Rasgos de personalidad: "narcisista", "manipulador", "psicópata"

Conclusiones: "es apto", "no es confiable", "miente en su CV"

Drama: "vendiendo humo", "actuación", "teatro", "brutal", "demoledor"

Diagnósticos: cualquier término clínico o patológico

8. Glosario de Términos Técnicos
Término	Definición
Blendshape	Valor 0-1 que indica activación de un músculo o grupo muscular facial según MediaPipe Face Landmarker
Z-score	Desviaciones estándar de la energía vocal respecto a la media del propio video. Z > 2.0 = alta energía. Z < -1.5 = pausa
Delta	Cambio en valor de blendshape entre frames consecutivos (1fps)
FPS	Frames por segundo muestreados. BEACON usa 1fps para análisis facial
Baseline	Promedio de activación del candidato calculado sobre todos los frames/voz del video
Face visibility	Porcentaje de frames donde MediaPipe detectó un rostro sobre el total de frames extraídos
9. Versionado
Versión	Fecha	Cambios
v1.0	2026-05-01	MVP: pipeline end-to-end funcional
v2.0	2026-05-01	Confidence levels, disclaimer metodológico
v2.1	2026-05-01	Hallazgos estructurados, baseline, reliability metadata
v3.0	2026-05-01	Contrato de prompt blindado, taxonomía, hipótesis múltiples
v4.0	2026-05-01	SPEC formal congelado, esquema JSON, catálogo de reglas, protocolo de uso
*BEACON v4.0 SPEC — Congelado el 2026-05-01*
Este documento rige todas las versiones posteriores del sistema.

## 10. Errata v4.1 — Hardening de Coherencia Semántica

### 10.1 Corrección: "Microexpresión" → "Cambio facial breve"
- A 1fps, BEACON no puede sostener el término "microexpresión" (que requiere resolución temporal fina).
- Todas las referencias en reglas, labels y reportes usan "cambio facial breve" o "delta".
- Labels técnicos: `{blendshape}_delta_onset` / `{blendshape}_delta_offset`

### 10.2 Corrección: R1 alineada con definición de HIGH
- R1 ahora asigna:
  - **HIGH**: ≥2 eventos visuales + convergencia con high_energy vocal en el mismo segmento
  - **MEDIUM**: ≥2 eventos visuales sin convergencia vocal
  - **LOW**: 1 evento visual aislado
- Esto alinea R1 con la definición general de HIGH (convergencia 2+ canales ≤1.5s)

### 10.3 Nueva entidad: Cluster
- **Cluster** es ahora una colección independiente en el JSON (`clusters[]`), no solo un campo dentro del hallazgo.
- Cada cluster tiene: `cluster_id`, `events[]` (lista de event_ids), `channels_involved`, `cross_channel_pattern`, `verbal_context`.
- Los hallazgos referencian al cluster mediante `source: "CLUSTER_XXX"`.

### 10.4 Corrección: `negative_findings` eliminado
- Reemplazado por `analysis_summary`, que describe los hallazgos sin lenguaje de engaño.
- BEACON no afirma capacidad de detectar veracidad, ni siquiera en negativo.

### 10.5 Corrección: `confidence_definition` → `confidence_rationale`
- La definición normativa de confidence vive en `methodology.confidence_levels` (global).
- Cada hallazgo incluye `confidence_rationale` (específico del caso), no la definición completa.
- Esto reduce redundancia y mejora trazabilidad.

### 10.6 Corrección: `audio_quality` → `audio_signal_level`
- La métrica global se llama `audio_signal_level` (basada en RMS).
- Se reserva `audio_quality` para futuras métricas robustas (SNR, clipping, voice activity).
- En `evidence_quality` por hallazgo se usa `audio_clarity`.

### 10.7 Mejora: Aislamiento de runs
- Cada ejecución crea subcarpetas: `frames_output/{run_id}/` y `audio_output/{run_id}/`.
- Se limpian automáticamente los frames/audio viejos de ejecuciones anteriores.
- Esto evita contaminación entre corridas.

echo "BEACON_SPEC.md creado."
