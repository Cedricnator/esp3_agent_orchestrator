# ESP3 Agent Orchestrator


## Instrucciones

### Instalar:
1. Activar entorno virtual
```bash
python3 -m venv .venv
```

2. Instalar dependencias
```bash
pip install -r requirements.txt
```

# UV

## Running the Service

**Development mode:**
```bash
uv run uvicorn app.main:app --reload --port 33205
```

**Production mode:**
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 33205
```

## Installation

Install all dependencies:
```bash
uv sync
```