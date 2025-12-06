## Project Info

“Agente Orquestador MCP con Analítica en MongoDB: identifica quién es y contesta su consulta”
Formato de entrega: repositorio (Git) + README + informe breve + demo endpoint (FastAPI/Flask) + MCP server + workflow n8n (JSON) + MongoDB (Atlas o Docker local).
Tecnologías mínimas: Python 3.11+, FastAPI (o Flask), httpx (async), MongoDB (pymongo/motor), YAML/JSON, gunicorn, (opcional: Nginx), MCP (server simple en Python), n8n (self-host), Docker (opcional).
Tiempo estimado: 20 horas efectivas.
Modalidad: trabajoo:duplas o equipos pequeños., entrega individual

0) ¿Qué problema resuelve? (visión didáctica)
Un servicio maestro que, dada una imagen y (opcional) una pregunta, hace dos tareas:

Identifica a la persona consultando todos los verificadores personales del PP2 (uno por estudiante).

Responde la pregunta sobre normativa UFRO usando el Chatbot RAG del PP1 (con citas).

Además, registra cada acceso y todos los eventos en MongoDB para:

Analítica por tipo de usuario (por ejemplo: estudiante, docente, admin…).

Métricas operativas (latencia p50/p95, tasa de identified/ambiguous/unknown, timeouts por servicio PP2, volumen por ruta).

Auditoría ligera con retención limitada y minimización de datos.

1) Objetivo (1 frase)
Construir un agente orquestador que expone API REST y tools MCP para identificar (PP2) y responder normativa(PP1), dejando trazas y analítica en MongoDB y una implementación alternativa con n8n.

2) Enunciado detallado
Desarrolla un microservicio maestro que:

Integra PP2: llama en paralelo a /verify de cada estudiante; decide identidad con umbral y margen (δ).

Integra PP1: si hay question, invoca al endpoint del RAG UFRO y devuelve citas.

Persiste en MongoDB:

access_logs (cada request/response, tiempos, usuario, ruta, resultado).

service_logs (llamadas a cada PP2/PP1 con latencias/estado).

users (catálogo mínimo: user_id, user_type, role, flags).

config (registro de PP2: name, endpoint_verify, threshold).

Ofrece dos superficies:

API REST (POST /identify-and-answer, GET /metrics/..., GET /healthz).

MCP server con tools: identify_person(image_url|b64) y ask_normativa(question).

Variante n8n: un workflow equivalente (Webhook → HTTP Request → agregación → MongoDB → Respond).

3) Arquitectura
flowchart LR
  Client[Cliente (curl/Front/LLM)] -- imagen + pregunta --> Orq[Agente Orquestador PP3]
  Orq -- paralelo --> V1[PP2: Verificador Ana /verify]
  Orq -- paralelo --> V2[PP2: Verificador Luis /verify]
  Orq -- paralelo --> Vn[PP2: Verificador ... /verify]
  Orq -- pregunta --> RAG[PP1: Chatbot UFRO /ask]
  Orq -- escribe --> MDB[(MongoDB)]
  Orq <-- tools --> MCP[MCP Server: identify_person / ask_normativa]
  n8n[n8n (Variante)]
  n8n <-- Webhook/HTTP --> Orq
  n8n -- insert/aggregate --> MDB
FastAPI + httpx para concurrencia limpia.

MongoDB con índices por ts, route, user_type, decision, service_name.

TTL para datos sensibles (hashes de imágenes).

4) Contratos de API (maestro)
4.1 POST /identify-and-answer
multipart/form-data

image (image/jpeg|png, ≤ 5 MB) obligatorio

question (string) opcional
Headers (sugeridos para analítica):

X-User-Id: ID lógico del usuario (hash o UUID).

X-User-Type: student|faculty|admin|external (normalizado).

Authorization: Bearer <TOKEN> (simple).

200 OK — ejemplo

{
  "decision": "identified",
  "identity": {"name": "Ana Pérez", "score": 0.88},
  "candidates": [{"name":"Ana Pérez","score":0.88},{"name":"Luis Soto","score":0.41}],
  "normativa_answer": {
    "text": "Puedes retractarte dentro de 10 días corridos...",
    "citations": [
      {"doc":"Reglamento Académico","page":"12","url":"https://..."},
      {"doc":"Calendario 2025","section":"4.2","url":"https://..."}
    ]
  },
  "timing_ms": 154.2,
  "request_id": "4b9d2c..."
}
Errores: 400 (faltan campos), 413 (tamaño), 422 (sin rostro), 504 (timeouts múltiples).
Decisiones: "identified" | "ambiguous" | "unknown".

4.2 GET /metrics/summary?days=7
Retorna volumen por ruta, latencia p50/p95, tasa de errores, top timeouts.

4.3 GET /metrics/by-user-type?days=7
Distribución por user_type (volumen, éxito, latencias).

4.4 GET /metrics/decisions?days=7
Recuento de identified/ambiguous/unknown.

4.5 GET /metrics/services?days=7
Ranking de PP2 por latencia media, timeouts, errores.

4.6 GET /healthz
Estado del servicio, conteo de PP2 registrados, conectividad Mongo.

5) Capa MCP (tools)
Tool 1 — identify_person

input: { "image_url": "string", "image_b64": "string", "timeout_s": number } (uno de image_url/image_b64).

output: { "decision": "...", "identity": {...}, "candidates":[...], "timing_ms": number, "request_id": "..." }

Tool 2 — ask_normativa

input: { "question": "string" }

output: { "text": "string", "citations": [{"doc":"string","page":"string","url":"string"}] }

El MCP server solo “envuelve” a los clientes PP2/PP1 y registra en Mongo igual que la API.

6) MongoDB — modelo de datos, índices y analítica
6.1 Colecciones y documentos (sugeridos)
access_logs (1 doc por request maestro)

{
  "_id": "ObjectId",
  "request_id": "uuid4",
  "ts": "2025-10-03T14:22:31.123Z",
  "route": "/identify-and-answer",
  "user": {"id": "hash/uuid", "type": "student", "role": "basic"},
  "input": {"has_image": true, "has_question": true, "image_hash": "sha256:abc...", "size_bytes": 183245},
  "decision": "identified",        // o ambiguous/unknown
  "identity": {"name": "Ana Pérez", "score": 0.88},
  "timing_ms": 154.2,
  "status_code": 200,
  "errors": null,
  "pp2_summary": {"queried": 12, "timeouts": 1},
  "pp1_used": true,
  "ip": "anonymized/iphash"
}
service_logs (1..N por request; cada llamada a PP2/PP1)

{
  "request_id": "uuid4",
  "ts": "2025-10-03T14:22:31.130Z",
  "service_type": "pp2|pp1",
  "service_name": "AnaPerezVerifier|UFRO-RAG",
  "endpoint": "https://.../verify",
  "latency_ms": 72.4,
  "status_code": 200,
  "payload_size_bytes": 183245,
  "result": {"is_me": true, "score": 0.88},
  "timeout": false,
  "error": null
}
users (catálogo mínimo, opcional)

{"user_id":"uuid/hash", "user_type":"student|faculty|admin|external", "role":"basic|power|admin"}
config (roster PP2 y thresholds)

{"name":"Ana Pérez","endpoint_verify":"https://.../verify","threshold":0.75,"active":true}
6.2 Índices recomendados
access_logs:

{ ts: -1 } (recientes)

{ "user.type": 1, ts: -1 }

{ route: 1, ts: -1 }

{ decision: 1, ts: -1 }

service_logs:

{ service_name: 1, ts: -1 }

{ service_type: 1, ts: -1 }

{ status_code: 1, ts: -1 }

TTL (privacidad): index TTL sobre access_logs.input.image_hash_ts si decides borrar hashes en 7 días.

6.3 Consultas de analítica (ejemplos)
Volumen por tipo de usuario (últimos N días)

db.access_logs.aggregate([
  {$match: {ts: {$gte: ISODate("2025-09-26")}}},
  {$group: {_id: "$user.type", requests: {$sum: 1}}},
  {$sort: {requests: -1}}
])
Decisiones (identified/ambiguous/unknown)

db.access_logs.aggregate([
  {$match: {ts: {$gte: ISODate("2025-09-26")}}},
  {$group: {_id: "$decision", total: {$sum:1}}}
])
Latencia p50/p95 por ruta

db.access_logs.aggregate([
  {$match: {ts: {$gte: ISODate("2025-09-26")}}},
  {$group: {_id: "$route", latencias: {$push:"$timing_ms"}}},
  {$project:{
    p50: {$percentile: {input:"$latencias", p:[0.5]}},
    p95: {$percentile: {input:"$latencias", p:[0.95]}}
  }}
])
Top PP2 por timeouts

db.service_logs.aggregate([
  {$match: {ts: {$gte: ISODate("2025-09-26")}, service_type:"pp2"}},
  {$group: {_id: "$service_name", timeouts: {$sum: {$cond:["$timeout",1,0]}}}},
  {$sort: {timeouts:-1}}, {$limit: 5}
])
Uso PP1 vs sin pregunta

db.access_logs.aggregate([
  {$match: {ts: {$gte: ISODate("2025-09-26")}}},
  {$group: {_id: "$pp1_used", total: {$sum:1}}}
])
Puedes exponer estas consultas como endpoints /metrics/... y/o dashboards (p. ej., Grafana/Loki más adelante).

7) Variante n8n (con MongoDB)
Webhook (Trigger) recibe image + question + headers (user).

HTTP Request (fan-out) a PP2 /verify (en paralelo) → Code para fusión τ/δ.

IF: unknown/ambiguous → responde; si identified, HTTP Request a PP1 /ask.

MongoDB node: inserta access_logs y múltiples service_logs.

MongoDB Aggregate node: métricas (por user_type, decisiones, latencias).

Respond to Webhook: JSON final.

8) Plan de trabajo (20 horas)
H1 – Setup (0.5 h)
Repo ufro-master/, venv, requirements.txt, .env.example (THRESHOLD, MARGIN, TIMEOUT, PP1_URL, MONGO_URI, DB_NAME).
H2 – MongoDB (0.5 h)
Atlas free o Docker local; crear BD y índices (script db/ensure_indexes.py).
H3–H4 – Cliente PP2 (2 h)
orchestrator/pp2_client.py (httpx async, timeouts, trazas a service_logs).
H5 – Fusión (1 h)
orchestrator/fuse.py (τ y δ, reglas unknown/ambiguous/identified).
H6 – Cliente PP1 (1 h)
orchestrator/pp1_client.py, normalización de citas.
H7 – API REST (1.5 h)
FastAPI POST /identify-and-answer, GET /healthz; validaciones; logging a Mongo en access_logs.
H8 – Métricas REST (1 h)
GET /metrics/summary, /by-user-type, /decisions, /services (aggregations Mongo).
H9–H10 – MCP server (2 h)
mcp_server/server.py con tools identify_person y ask_normativa; logging en Mongo.
H11 – Seguridad (1 h)
Token simple, filtrado MIME/MB, hash de imágenes, TTL opcional de hashes, anonimización IP.
H12–H13 – Pruebas (2 h)
pytest (mocks PP2/PP1), curl/Postman reales, ver métricas en Mongo.
H14–H15 – Despliegue (2 h)
EC2, gunicorn, (opcional Nginx). Variables .env, healthz.
H16–H17 – Variante n8n (2 h)
Workflow con Webhook, fan-out, Code, MongoDB (insert/aggregate), Respond. Export JSON.
H18 – Observabilidad (1 h)
Request-ID, logs JSON; endpoint /metrics/health con últimas p95.
H19 – Informe (1 h)
2–3 págs.: diseño, analítica por tipo de usuario, resultados, riesgos/ética.
H20 – Pulido (1 h)
README, ejemplos curl, screenshots de métricas, limpieza.

