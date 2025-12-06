# Project Context: PP3 - Orchestrator Agent with MCP & Analytics

## 1. Project Overview & Objective

**Role:** Central Orchestrator Service.
**Goal:** Act as an API Gateway and Logic Hub that receives an image and a question. It performs parallel identity verification by querying multiple external "PP2" agents, aggregates the results using a Scoring Logic (Threshold + Margin), and optionally queries a "PP1" RAG agent for answers if the person is identified and a question is present.
**Interfaces:** Exposes both a REST API (FastAPI) and an MCP Server (Model Context Protocol).
**Persistence:** Logs every request, service call, and decision to MongoDB for granular analytics.

## 2. Tech Stack & Constraints

*   **Language:** Python 3.11+
*   **Web Framework:** FastAPI (Async/Await required)
*   **HTTP Client:** `httpx` (Async client for parallel fan-out)
*   **Database:** MongoDB (Driver: `motor` async)
*   **Protocol:** MCP (Model Context Protocol) using `mcp` python SDK.
*   **Containerization:** Docker (Dockerfile + docker-compose).

-----

## 3. Data Models (MongoDB)

### Collection: `config` (PP2 Registry)
*Used to dynamically load the list of identity verification agents.*
```json
{
  "name": "string (e.g., 'Agent_Ana')",
  "endpoint_verify": "string (URL, e.g., 'https://.../verify')",
  "threshold": "float (0.0 - 1.0)",
  "active": "boolean"
}
```

### Collection: `access_logs` (Request Level)
*One document per incoming request to the Orchestrator.*
```json
{
  "request_id": "UUID (string)",
  "ts": "ISODate",
  "route": "string",
  "user": {
      "id": "string (hash/uuid from Header)",
      "type": "string (student|faculty|admin|external)",
      "role": "string"
  },
  "input_metadata": {
      "has_image": "bool",
      "has_question": "bool",
      "image_hash": "string (sha256)"
  },
  "decision": "enum('identified', 'ambiguous', 'unknown')",
  "identity": {
      "name": "string or null",
      "score": "float"
  },
  "pp2_summary": {
      "queried": "integer (count)",
      "timeouts": "integer (count)"
  },
  "pp1_used": "boolean",
  "timing_ms": "float",
  "status_code": "integer",
  "ip": "string (anonymized/hash)"
}
```

### Collection: `service_logs` (Sub-call Level)
*Multiple documents per request. Tracks performance of external dependencies (PP1/PP2).*
```json
{
  "request_id": "UUID (string, links to access_logs)",
  "ts": "ISODate",
  "service_type": "enum('pp2', 'pp1')",
  "service_name": "string (e.g., 'AnaPerezVerifier' or 'UFRO-RAG')",
  "endpoint": "string",
  "latency_ms": "float",
  "status_code": "integer",
  "timeout": "boolean",
  "error": "string or null",
  "result": "object (snapshot of specific service response)"
}
```

-----

## 4. Functional Requirements (FR)

### FR1: Parallel Identity Verification (Fan-Out)
*   **Input:** Image (URL or Base64).
*   **Logic:**
    1.  Fetch active agents from `config`.
    2.  Use `asyncio.gather` for concurrent POST to `/verify` of **all** agents.
    3.  **Timeout:** Hard cap of 3.0 seconds per agent.
    4.  **Resilience:** Timeouts count as score 0.0 (do not fail the main request).

### FR2: Decision Logic
*   **Algorithm:**
    *   Find `max_score` and `runner_up_score` among all responses.
    *   **Identified:** `max_score >= threshold` AND `(max_score - runner_up_score) > margin`.
    *   **Ambiguous:** `max_score >= threshold` BUT `(max_score - runner_up_score) < margin`.
    *   **Unknown:** `max_score < threshold`.

### FR3: RAG Integration
*   **Condition:** IF `decision == 'identified'` AND `question` is present.
*   **Action:** Call PP1 Agent (`/ask` endpoint).
*   **Output:** Return `text` and `citations`.

### FR4: Analytics & Metrics
*   **Endpoints Required:**
    *   `GET /metrics/summary`: Volume, Error Rates, Latency P50/P95.
    *   `GET /metrics/by-user-type`: Distribution by `user.type`.
    *   `GET /metrics/decisions`: Count of identified vs ambiguous vs unknown.
    *   `GET /metrics/services`: Top agents by timeout count and latency ranking.

-----

## 5. API Contract

### POST `/identify-and-answer`
*   **Headers:**
    *   `X-User-Id`: string (required)
    *   `X-User-Type`: string (required)
    *   `Authorization`: Bearer token
*   **Body (Multipart):** `image` (file), `question` (string, optional)
*   **Response (JSON):**
```json
{
  "decision": "identified",
  "identity": {"name": "Ana Pérez", "score": 0.88},
  "candidates": [
      {"name":"Ana Pérez","score":0.88},
      {"name":"Luis Soto","score":0.41}
  ],
  "normativa_answer": {
    "text": "Respuesta normativa...",
    "citations": [{"doc":"...","page":"..."}]
  },
  "timing_ms": 154.2,
  "request_id": "4b9d2c..."
}
```

-----

## 6. MCP Server Integration
*   Expose tool `identify_person(image_b64)` -> Returns same JSON structure as API.
*   Expose tool `ask_normativa(question)` -> Returns answer + citations.
*   Must use the same `OrchestratorService` logic and write to MongoDB logs.