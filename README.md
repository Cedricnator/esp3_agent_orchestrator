# Orchestrator Agent (PP3)

Microservice master that identifies people (using 20+ PP2 agents) and answers questions (using PP1 RAG).

## Architecture
- **Orchestrator**: FastAPI + Gunicorn
- **Database**: MongoDB (Atlas/Local)
- **External Agents**: PP2 (Students) & PP1 (RAG)

## Setup

1.  **Environment**:
    ```bash
    uv sync
    cp .env.example .env
    # Edit .env with your MONGO_URI and API_TOKEN
    ```

2.  **Seed DB**:
    ```bash
    uv run python -m app.db.seed
    ```

3.  **Run Locally (Dev)**:
    ```bash
    uv run uvicorn app.main:app --reload --port 33201
    ```

4.  **Run Tests**:
    ```bash
    uv run pytest
    ```

5.  **Run Integration Tests**:
    ```bash
    uv run python -m pytest tests/integration/test_metrics.py
    ```

## Deployment (Docker)

1.  **Build**:
    ```bash
    docker build -t orchestrator-agent .
    ```

2.  **Run**:
    ```bash
    docker run -p 8000:8000 --env-file .env orchestrator-agent
    ```

## API Usage

**POST /identify-and-answer**
- Headers: `Authorization: Bearer <API_TOKEN>`
- Form Data: `image` (File), `question` (Text)

## Security
- Bearer Auth required.
- Images hashed heavily for privacy logs.
- Strict MIME type checks (JPEG/PNG).