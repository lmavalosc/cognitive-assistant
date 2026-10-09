# INFORME TÉCNICO COMPLETO — ARQUITECTURA MATEMÁTICA APLICADA Y FUNCIONES
Proyecto de Tesis: Asistente Cognitivo Modular (JARVIS 0.0)
Documento: `TR-COG-2026-MATH-V1.0` / `DATA/INFORMES/INFORME_MATEMATICAS_APLICADAS.md`
Rama Git: `semana1-tronco-encefalico`
Fecha: 08 de Octubre, 2026
Autor: Moisés
Fuentes: `Arquitectura de un Cerebro Digital` (pipeline de 10 capas) + `TR-COG-2026-ARCH-V2.0` (8 Capas Funcionales y 3 Planos Transversales de JARVIS 0.0)

---

## 1. Resumen Ejecutivo

Este informe consolida **todas las operaciones matemáticas, factores y parámetros** que intervienen en el funcionamiento del Asistente Cognitivo Modular, y establece la **función exacta** que cada una cumple dentro del pipeline deliberativo. El documento demuestra que el sistema no es un conjunto de llamadas a APIs, sino una **cadena de transformaciones algebraicas, probabilísticas y de optimización** sobre espacios vectoriales de alta dimensión, trazables desde la Capa 1 (Percepción) hasta la Capa 8 (Efectores), y auditables mediante los 7 Escenarios Experimentales de la tesis.

Las matemáticas se agrupan en **seis bloques funcionales**:
1. **Bloque I — Operaciones núcleo del pipeline** (vectorización, convolución, recurrencia, atención, similitud, no linealidades, decodificación).
2. **Bloque II — Estabilidad y posición** (RMSNorm, LayerNorm, residuales, RoPE).
3. **Bloque III — Pérdida y optimización** (entropía cruzada, divergencia KL, AdamW).
4. **Bloque IV — Ingeniería y cuantización** (precisión flotante, INT8/INT4, Roofline, paralelismo).
5. **Bloque V — Inferencia y decodificación** (batch size, top-k, top-p, penalización por repetición).
6. **Bloque VI — Factores críticos y restricciones** (dimensionalidad, gradientes, complejidad, KV-cache).

---

## 2. Objetivo, Alcance y Metodología

- **Objetivo:** Documentar la función de cada fórmula del marco matemático y su correspondencia con un módulo ejecutable del repositorio `cognitive-assistant`.
- **Alcance:** Las 10 capas del cerebro digital mapeadas a las 8 Capas Funcionales + 3 Planos Transversales de JARVIS 0.0, y a los 7 Escenarios Experimentales.
- **Metodología:** Por cada operación se declara: (a) fórmula, (b) función matemática, (c) rol en el sistema cognitivo, (d) aplicación en JARVIS (capa/archivo), (e) parámetros a controlar.

---

## 3. BLOQUE I — Operaciones Matemáticas Núcleo del Pipeline Cognitivo

### 3.1. Proyección Lineal y Vectorización (Capas 1–2 → C1/C2/C5)

$$z = W \cdot x + b, \quad W \in \mathbb{R}^{m \times n}, \; b \in \mathbb{R}^{m}$$

- **Función matemática:** Transformación lineal que proyecta un vector de entrada $x$ (señal cruda tokenizada) a un nuevo espacio de dimensión $m$ mediante la matriz de pesos $W$ y el sesgo $b$. Es el "cambio de base" que convierte datos heterogéneos en embeddings operables.
- **Rol en el sistema cognitivo:** Es la operación de **traducción sensorial**: sin ella, texto, audio o telemetría no existirían como objetos geométricos comparables.
- **Aplicación en JARVIS:** Generación de embeddings en Capa 5 (`modules/c5_memory/`, `retriever.py`) con dimensión 768 (SentenceTransformers local) o 1536 (API remota); tokenización interna del Plano A (`shared/infrastructure/llm.py`).
- **Parámetros:** dimensión $d_{model}$ (capacidad expresiva vs. costo); inicialización y norma de $W$.

### 3.2. Convolución Discreta — Extracción de Rasgos Espaciales (CNN)

$$(f * g)(i,j) = \sum_{m}\sum_{n} f(m,n) \cdot g(i-m, \, j-n)$$

- **Función matemática:** Producto punto local deslizante entre un kernel $f$ y la señal $g$; detecta correlaciones jerárquicas locales (bordes, formantes, n-gramas) y las compone en estructuras complejas.
- **Rol en el sistema cognitivo:** Actúa como la **lupa perceptual**: agrupa patrones simples en rasgos abstractos antes de cualquier razonamiento.
- **Aplicación en JARVIS:** Internamente en el modelo de STT de Capa 1 (`modules/c1_perception/stt/whisper_engine.py`), donde la convolución opera sobre el espectrograma de audio; conceptualmente en la extracción de firmas locales del cortafuegos (`c3_governance/prompt_guard.py`, patrones sintácticos).
- **Parámetros:** tamaño y paso del kernel; profundidad de apilamiento; cuantización INT8 del modelo (ver §6.2).

### 3.3. Transición Recurrente — Memoria Temporal (RNN)

$$h_t = \tanh(W_h \cdot h_{t-1} + W_x \cdot x_t + b)$$

- **Función matemática:** El estado oculto $h_t$ condensa recursivamente todo el historial anterior ($h_{t-1}$) fusionado con la entrada actual $x_t$; la no linealidad $\tanh$ acota el estado al intervalo $(-1, 1)$.
- **Rol en el sistema cognitivo:** Es la **memoria de trabajo matemática**: garantiza que el orden y la cadencia de la información condicionen la interpretación presente.
- **Aplicación en JARVIS:** Equivalente funcional explícito en Capa 4: `modules/c4_executive/working_memory.py` (`WorkingMemoryManager`), donde $h_t$ es el `WorkingMemoryState` persistido en Redis bajo `session:{session_id}:working_memory` con ventana deslizante de 6 turnos; se inyecta como `dialogue_history` en `graph.py`.
- **Parámetros:** longitud de ventana (6 turnos), TTL (24 h), latencia de lectura/escrita (< 20 ms, Escenario 1).

### 3.4. Atención Escalada — Ponderación Dinámica de Relevancia

$$\text{Attention}(Q, K, V) = \text{softmax}\!\left(\frac{Q K^{\mathsf{T}}}{\sqrt{d_k}}\right) V$$

- **Función matemática:** Calcula la afinidad geométrica entre consultas $Q$ y claves $K$, la normaliza con softmax y la usa para promediar valores $V$. El factor $\sqrt{d_k}$ reescala el producto punto para evitar gradientes desvanecidos en softmax cuando $d_k$ es grande.
- **Rol en el sistema cognitivo:** Es el **mecanismo de selección atencional**: asigna mayor cómputo a las partes críticas del dato y descarta redundancias contextuales.
- **Aplicación en JARVIS:** Núcleo de inferencia del Plano A (`LLMGateway` → LiteLLM) en cada llamada de `deliberate_and_plan_node`; en Capa 1, el clasificador de saliencia (`AttentionResult`: `intent`, `urgency`, `relevance`) es una proyección semántica de esta ponderación.
- **Parámetros:** $d_k$ (escala); longitud de contexto $N$ (costo cuadrático, ver §8.3); temperatura del softmax de salida (§3.7).

### 3.5. Similitud Vectorial — Memoria Asociativa y Recuperación

$$\text{Similitud Coseno}(u, v) = \frac{u \cdot v}{\lVert u \rVert \, \lVert v \rVert}$$

- **Función matemática:** Mide el ángulo entre dos vectores independientemente de su magnitud; valor en $[-1, 1]$. Junto a la distancia euclídea ($\leftrightarrow$ en pgvector), define la geometría de búsqueda en la base vectorial.
- **Rol en el sistema cognitivo:** Es el **hipocampo matemático**: permite que "recordar" sea una operación geométrica de vecindad, no una búsqueda textual.
- **Aplicación en JARVIS:** Capa 5 (`modules/c5_memory/retriever.py`, `service.py`) sobre PostgreSQL 16 + pgvector con índice HNSW (`vector_cosine_ops`); validado en `tests/test_pgvector_db.py` (puerto 5433) y en el Escenario 2 (Recall@5 > 0.85, citas exactas, umbral anti-alucinación `similarity_score < 0.70` → declarar desconocimiento).
- **Parámetros:** dimensión del embedding; umbral de relevancia (0.70); $k$ de recuperación (5); métrica (coseno vs. L2).

### 3.6. No Linealidades — Curvatura del Espacio de Decisión

$$\text{GELU}(x) = x \cdot \Phi(x), \quad \Phi = \text{CDF de } \mathcal{N}(0,1)$$

- **Función matemática:** Multiplica la entrada por su probabilidad acumulada gaussiana; produce una transición suave y diferenciable que permite separar variedades no lineales (familia ReLU/GELU/Swish).
- **Rol en el sistema cognitivo:** Sin no linealidades, todo el pipeline sería una única transformación lineal compuesta; GELU es lo que habilita **abstracción jerárquica real**.
- **Aplicación en JARVIS:** Interna a los transformadores servidos por el Plano A y por los modelos locales (Ollama); no se implementa directamente, pero condiciona la selección de modelo en `settings.py` (`DEFAULT_LLM_MODEL`).
- **Parámetros:** familia de activación del modelo elegido; estabilidad numérica en FP16/BF16.

### 3.7. Decodificación Probabilística — Softmax con Temperatura

$$P(y_i) = \frac{e^{z_i / T}}{\sum_j e^{z_j / T}}$$

- **Función matemática:** Convierte logits $z$ en una distribución de probabilidad normalizada; $T$ regula la entropía: $T \to 0$ colapsa la distribución (greedy determinista), $T > 1$ la aplana (diversidad).
- **Rol en el sistema cognitivo:** Es el **umbral de decisión consciente**: transforma tensión numérica en elección discreta de token/acción.
- **Aplicación en JARVIS:** Plano A (`llm.py`, parámetro `LLM_TEMPERATURE=0.2` en `.env`); política por tarea: $T=0.0$ para salidas JSON estructuradas (saliencia Capa 1, contratos Capa 2), $T=0.2$ conversación (Capa 4/8), $T=0.7$ redacción creativa (Capa 6 ResearchAgent).
- **Parámetros:** $T$; combinación con top-k/top-p (§7).

---

## 4. BLOQUE II — Matemáticas de Estabilidad, Normalización y Posición

### 4.1. RMSNorm — Normalización por Raíz Cuadrática Media

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_{i=1}^{d} x_i^2 + \epsilon}} \odot \gamma$$

- **Función:** Reescala el vector por su energía cuadrática media (sin centrar en media); acelera el cómputo respecto a LayerNorm manteniendo estabilidad de varianza.
- **Rol:** Controla la **homeostasis de activaciones** entre capas profundas.
- **Aplicación en JARVIS:** Interna a los LLM del Plano A; análogo funcional en Capa 2: normalización y sanitización de estímulos (`c3_governance/sanitizer.py`: NFKC, remoción de caracteres de control, límite 8 000 caracteres) como "normalización perimétrica" del vector de entrada.
- **Parámetros:** $\epsilon$ (estabilidad numérica); $\gamma$ (ganancia aprendida).

### 4.2. LayerNorm — Estandarización con Media y Varianza

$$\text{LayerNorm}(x) = \gamma \odot \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta$$

- **Función:** Centra y estandariza cada vector de activación; $\gamma, \beta$ restauran capacidad expresiva.
- **Rol:** Evita deriva de escala entre subcapas; condición necesaria para convergencia.
- **Aplicación en JARVIS:** Interna al modelo; justifica la elección de arquitecturas modernas en el Plano A.
- **Parámetros:** $\mu, \sigma^2$ por muestra; $\epsilon$.

### 4.3. Conexiones Residuales

$$x + \text{SubLayer}(x)$$

- **Función:** Suma la entrada a la salida de la subcapa; crea un camino identitario que preserva el gradiente en profundidad.
- **Rol:** Previene **degradación de señal** en pipelines profundos (mitiga gradiente desvanecido).
- **Aplicación en JARVIS:** Patrón arquitectónico análogo: el `CognitiveState` de LangGraph acumula campos (`dialogue_history`, `tool_results`) sin destruir el estado previo; auditoría aditiva del Plano B.
- **Parámetros:** profundidad efectiva del grafo; número de nodos.

### 4.4. RoPE — Incrustaciones Posicionales Rotatorias

$$R_{\Theta}(m): \text{rotación del par } (x_{2i}, x_{2i+1}) \text{ en ángulo } m \cdot \theta_i, \quad \theta_i = 10000^{-2i/d}$$

- **Función:** Aplica matrices de rotación en subespacios ortogonales de 2D dependientes de la posición temporal $m$; la atención pura es permutation-invariante, RoPE le inyecta **orden**.
- **Rol:** Codifica la **cronología** sin romper la geometría del espacio latente.
- **Aplicación en JARVIS:** Interna al modelo; equivalente funcional en Capa 4: el orden cronológico de `recent_turns` (`TurnRecord.timestamp`) y la numeración de pasos del `CognitivePlan` (`plan.py`, DAG acíclico con `dependencies`).
- **Parámetros:** frecuencia base $\theta_i$; longitud máxima de secuencia soportada.

---

## 5. BLOQUE III — Métricas de Pérdida, Información y Optimización

### 5.1. Entropía Cruzada — Distancia entre Distribuciones

$$L = -\sum_i y_i \log(\hat{y}_i)$$

- **Función:** Cuantifica el desacuerdo entre la distribución real $y$ y la predicha $\hat{y}$; es el funcional que el descenso de gradiente minimiza.
- **Rol:** Es la **calificación del error**: sin ella no hay aprendizaje, solo inferencia estática.
- **Aplicación en JARVIS:** Marco de validación del clasificador de saliencia (Semana 3, exactitud ≥ 90 % sobre 20 casos) y del Plano C (`consolidation_worker.py`, Día 36): la consolidación offline minimiza el desacuerdo entre el estilo esperado del usuario y el estilo emitido (Escenario 6).
- **Parámetros:** etiquetas de referencia; tasa de aprendizaje del ajuste.

### 5.2. Divergencia de Kullback–Leibler — Sesgo de Información Relativa

$$D_{KL}(P \lVert Q) = \sum_x P(x) \log \frac{P(x)}{Q(x)}$$

- **Función:** Mide información perdida al aproximar $P$ con $Q$; asimétrica, no es una métrica distancia.
- **Rol:** Permite **auditar desviación** entre representaciones o políticas (modelo profesor/alumno, perfil antiguo/nuevo).
- **Aplicación en JARVIS:** Plano C: comparación entre el perfil de usuario previo y el consolidado (`UserProfile`); Capa 6: `CriticVerifierAgent` contrasta la distribución de la respuesta intermedia contra la evidencia recuperada para detectar alucinaciones.
- **Parámetros:** suavizado de ceros; umbral de divergencia aceptable.

### 5.3. AdamW — Optimización con Momentos y Decaimiento Desacoplado

$$m_t = \beta_1 m_{t-1} + (1-\beta_1) g_t, \quad v_t = \beta_2 v_{t-1} + (1-\beta_2) g_t^2, \quad \text{decay } \lambda w_t$$

- **Función:** Promedios móviles exponenciales del gradiente (primer momento $m_t$) y de su cuadrado (segundo momento $v_t$) para adaptar el paso por coordenada; el weight decay $\lambda w_t$ se aplica desacoplado del gradiente.
- **Rol:** Es el **motor de adaptación continua** del sistema.
- **Aplicación en JARVIS:** Cualquier ajuste local/fine-tuning futuro y, conceptualmente, el update atómico del `UserProfile` en Plano C (Día 36) y el `decay_manager.py` (Día 37, olvido y decaimiento cognitivo).
- **Parámetros:** $\beta_1 \approx 0.9$, $\beta_2 \approx 0.999$, $\lambda$, learning rate.

---

## 6. BLOQUE IV — Factores de Ingeniería y Cuantización Numérica

### 6.1. Precisión de Punto Flotante (FP32 / FP16 / BF16)

- **Función:** Define ancho de banda de memoria y precisión aritmética por peso/activación.
- **Rol:** Determina cuánta "resolución numérica" tiene el cerebro por byte.
- **Aplicación en JARVIS:** Selección de formato de modelos en Plano A y Ollama; `halfvec` en pgvector para reducir huella de embeddings.
- **Parámetros:** bits por elemento; rango dinámico (BF16 vs FP16).

### 6.2. Cuantización Lineal (INT8 / INT4)

$$q = \text{round}(x / S) + Z, \quad \hat{x} = S \cdot (q - Z)$$

- **Función:** Mapea reales a enteros mediante factor de escala $S$ y punto cero $Z$; la dequantización reconstruye $\hat{x}$.
- **Rol:** **Compresión cognitiva**: reduce memoria y acelera inferencia en hardware limitado con pérdida acotada.
- **Aplicación en JARVIS:** Capa 1: `faster-whisper` en modo CPU cuantizado `int8` (Día 12, fallback sin GPU); modelos locales Ollama (Q4_K_M); embeddings compactos en Capa 5.
- **Parámetros:** $S$, $Z$; bits (8/4); métrica de degradación (WER en STT, Recall@5 en RAG).

### 6.3. Roofline Model — Límite de Memoria por Operación

- **Función:** Relaciona FLOPS del dispositivo con ancho de banda de memoria; clasifica cada capa como **compute-bound** (matmul grandes) o **memory-bound** (atención, activaciones, búsquedas).
- **Rol:** Es la **física del hardware cognitivo**: dice qué cuellos de botella son inevitables.
- **Aplicación en JARVIS:** Decisiones de ingeniería: ingestas por lotes en `scripts/seed_knowledge.py` (Día 33) para volver compute-bound la indexación; límites del sandbox Docker (`mem_limit='256m'`, `cpu_quota=50000`, Día 26–27); objetivo de latencia p95 < 30 ms en ruta básica y < 20 ms en Redis.
- **Parámetros:** FLOPS pico; ancho de banda; intensidad aritmética de cada operación.

### 6.4. Paralelismo y Partición Tensorial

- **Función:** Divide las capas entre procesadores (paralelismo de capas) o las matrices por columnas/filas (paralelismo tensorial).
- **Rol:** Escala el cerebro horizontalmente cuando un solo nodo satura.
- **Aplicación en JARVIS:** Decisión arquitectónica documentada (ADR): monolito modular hexagonal en un nodo durante las 8 semanas; el paralelismo funcional se expresa como concurrencia asíncrona (`asyncio`, pools de `asyncpg` y Redis) y como orquestación multiagente en Capa 6 (`orchestrator.py`).
- **Parámetros:** número de shards; costo de comunicación (all-reduce); tamaño de pool (10 en `db.py`).

---

## 7. BLOQUE V — Factores de Inferencia y Decodificación

### 7.1. Tamaño del Lote (Batch Size)

- **Función:** Número de secuencias procesadas simultáneamente; amortiza costo fijo de kernel y mejora utilización vectorial.
- **Aplicación en JARVIS:** Ingesta de 500 vectores (Día 32) y consolidación batch nocturna (Día 36, Plano C); batch = 1 en conversación interactiva para minimizar latencia.
- **Parámetros:** 64–128 en ingesta; 1 en inferencia interactiva.

### 7.2. Top-k — Truncamiento Duro

- **Función:** Conserva únicamente los $k$ logits más altos; el resto se elimina antes del muestreo.
- **Aplicación en JARVIS:** Parámetro `top_k` del Plano A; $k=1$ (greedy) en contratos JSON de Capa 1/2/3.
- **Parámetros:** $k \approx 40$ conversación; $k=1$ estructurado.

### 7.3. Top-p (Nucleus Sampling) — Truncamiento Dinámico

$$\sum_{i \in V(p)} P(y_i) \geq p, \quad V(p) \text{ mínimo}$$

- **Función:** Selecciona el subconjunto más pequeño de tokens cuya probabilidad acumulada supera $p$; el núcleo se adapta a la confianza de cada paso.
- **Aplicación en JARVIS:** Parámetro `top_p` del Plano A (0.9 conversación, 0.95 redacción Capa 6, 1.0 estructurado).
- **Parámetros:** $p \in [0.9, 0.95]$.

### 7.4. Penalización por Repetición

$$z_i \leftarrow z_i - \alpha \quad \text{si } y_i \text{ fue seleccionado previamente}$$

- **Función:** Resta un factor constante $\alpha$ a logits ya emitidos; rompe bucles y muletillas.
- **Aplicación en JARVIS:** Plano A (`repeat_penalty`/`frequency_penalty`); crítico en resúmenes rodantes (Día 8) y síntesis RAG (Día 34) para evitar pegado repetitivo de chunks.
- **Parámetros:** $\alpha \approx 1.1\text{–}1.2$.

---

## 8. BLOQUE VI — Factores Críticos y Restricciones de Diseño

### 8.1. Dimensionalidad de los Espacios ($d_{model}$, $d_k$)
- Baja dimensión → subajuste; alta → costo cuadrático en atención. **Decisión JARVIS:** 768 (local) / 1536 (remoto) para embeddings RAG; $d_k$ heredado del modelo del Plano A.

### 8.2. Propagación del Gradiente y Estabilidad Numérica
- Gradiente desvanecido/explosivo controlado con LayerNorm/RMSNorm y residuales. **Decisión JARVIS:** validación empírica mediante métricas de escenario (WER, Recall@5, exactitud de saliencia) en lugar de entrenamiento profundo local.

### 8.3. Complejidad Asintótica y KV-cache
- Atención: $O(N^2)$ en longitud de secuencia; matmul: $O(n^3)$ (o $O(n^{2.81})$ con algoritmos rápidos). El KV-cache almacena claves/valores de inferencias secuenciales y consume VRAM.
- **Decisión JARVIS:** ventana deslizante de 6 turnos + *rolling summary* (Día 8) como gestión explícita de "KV-cache conversacional" en Redis; timeouts estrictos (navegación 5 s, sandbox 15 s) para acotar $N$ efectivo.

---

## 9. Matriz de Trazabilidad: Fórmula → Función → Capa JARVIS → Módulo → Escenario

| # | Fórmula | Función principal | Capa / Plano JARVIS | Módulo / Archivo | Escenario / Hito |
|---|---|---|---|---|---|
| 1 | $z=Wx+b$ | Vectorizar / traducir | C5, Plano A | `c5_memory/retriever.py`, `llm.py` | Etapa 7 (RAG) |
| 2 | $(f*g)$ | Detectar rasgos locales | C1, C3 | `whisper_engine.py`, `prompt_guard.py` | Etapa 3 (WER, saliencia) |
| 3 | $h_t=\tanh(\dots)$ | Memoria temporal | C4 | `working_memory.py`, `graph.py` | Escenario 1 (< 20 ms) |
| 4 | $\text{softmax}(QK^{\mathsf{T}}/\sqrt{d_k})V$ | Ponderar relevancia | Plano A, C1 | `llm.py`, clasificador saliencia | Escenarios 1 y 2 |
| 5 | $\cos(u,v)$ | Recuperar por vecindad | C5 | `retriever.py` (pgvector HNSW) | Escenario 2 (Recall@5 > 0.85) |
| 6 | GELU | Separar variedades | Plano A | modelo servido | — |
| 7 | $e^{z_i/T}/\sum e^{z_j/T}$ | Decidir con entropía | Plano A | `llm.py` (`LLM_TEMPERATURE`) | Todas las respuestas |
| 8 | RMSNorm / LayerNorm | Estabilizar varianza | Plano A, C2/C3 | modelo; `sanitizer.py` (análogo) | — |
| 9 | $x+\text{SubLayer}(x)$ | Preservar gradiente/estado | C4, Plano B | `state.py`, auditoría aditiva | Escenario 7 |
| 10 | RoPE | Codificar orden | C4, Plano A | `working_memory.py` (orden turnos) | Escenario 1 |
| 11 | $-\sum y \log \hat{y}$ | Calificar error | C1, Plano C | saliencia; `consolidation_worker.py` | Escenario 6 |
| 12 | $D_{KL}(P\lVert Q)$ | Auditar desviación | C6, Plano C | `CriticVerifierAgent`, `UserProfile` | Escenario 6 |
| 13 | AdamW | Adaptar continuamente | Plano C | `consolidation_worker.py` | Escenario 6 |
| 14 | $q=\text{round}(x/S)+Z$ | Comprimir precisión | C1, C5, Plano A | whisper int8, halfvec, Ollama Q4 | Etapa 3 (CPU sin GPU) |
| 15 | Roofline | Clasificar cuello de botella | C7, C5 | sandbox Docker, `seed_knowledge.py` | Escenario 3 (15 s) |
| 16 | top-k / top-p / $-\alpha$ | Filtrar muestreo | Plano A | `llm.py` kwargs | JSON determinista vs. creativo |

---

## 10. Configuración Matemática Recomendada para JARVIS 0.0

| Parámetro | Símbolo / clave | Valor recomendado | Justificación |
|---|---|---|---|
| Temperatura conversación | `LLM_TEMPERATURE` | 0.2 | Entropía baja, tono de asistente serio |
| Temperatura estructurado | — | 0.0 ($k=1$, $p=1$) | Determinismo para JSON/contratos |
| Temperatura redacción | — | 0.7 ($p=0.95$) | Fluidez en ResearchAgent |
| Top-k / Top-p | `top_k`, `top_p` | 40 / 0.9 | Balance diversidad-coherencia |
| Penalización repetición | $\alpha$ | 1.15 | Anti-bucles en resúmenes y RAG |
| Umbral anti-alucinación RAG | similitud | 0.70 | Declarar desconocimiento bajo umbral |
| Meta de recuperación | Recall@5 | > 0.85 | Criterio Escenario 2 |
| Ventana de memoria | turnos | 6 (+ rolling summary) | Control de KV-cache conversacional |
| Umbral de riesgo | `risk_score` | ≥ 0.7 → bloqueo 403 | Criterio Escenario 4 |
| Umbral metacognitivo | confianza | < 0.65 → clarificación | Suspensión deliberada |
| Cuantización STT | int8 | faster-whisper CPU | Operatividad sin GPU |
| Batch de ingesta | — | 64–128 | Roofline compute-bound |
| Latencias objetivo | — | Redis < 20 ms; p95 < 30 ms; sandbox 15 s | Escenarios 1 y 3 |

---

## 11. Conclusiones

1. El pipeline de JARVIS 0.0 es una **realización ejecutable** del cerebro digital de 10 capas: cada fórmula del marco matemático tiene un módulo, un parámetro y un criterio de validación experimental concretos.
2. La **memoria de trabajo en Redis** es el análogo funcional explícito de la recurrencia $h_t$, y la **base vectorial pgvector + HNSW** es el análogo de la similitud coseno asociativa; ambos se validan con los Escenarios 1 y 2.
3. Las matemáticas de **estabilidad y decodificación** (normas, temperatura, top-k/p, penalización) no son detalles: son los controles que garantizan determinismo donde se requiere (gobernanza, contratos) y diversidad donde aporta (redacción, investigación).
4. Los factores de **ingeniería numérica** (cuantización, Roofline, batch) son los que hacen viable el sistema en hardware real sin GPU, y fundamentan las decisiones de latencia y confinamiento de los Escenarios 3 y 4.
5. La **entropía cruzada, KL y AdamW** constituyen el sustrato del aprendizaje offline (Plano C), cerrando el ciclo: el asistente no solo infiere, sino que **minimiza su error futuro** (Escenario 6).

## 12. Referencias

- `Arquitectura de un Cerebro Digital` (pipeline de 10 capas y arquitectura matemática).
- `TR-COG-2026-ARCH-V2.0` — Taxonomía de 8 Capas Funcionales y 3 Planos Transversales.
- `PLAN_DE_TRABAJO_8_SEMANAS.md` — Cronograma maestro y matriz de 7 escenarios.
- `INFORME_AVANCE_DIA_1.md` / `INFORME_AVANCE_DIA_2.md` — Estado real de integración y pruebas.