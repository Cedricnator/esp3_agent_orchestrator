# Agente Orquestador (PP3)

Microservicio maestro que identifica personas (usando más de 20 agentes PP2) y responde preguntas (usando PP1 RAG).

## Arquitectura
- **Orquestador**: FastAPI + Gunicorn
- **Base de Datos**: MongoDB (Atlas/Local)
- **Agentes Externos**: PP2 (Estudiantes) y PP1 (RAG)

## Configuración

1.  **Entorno**:
    ```bash
    uv sync
    cp .env.example .env
    # Edita .env con tu MONGO_URI y API_TOKEN
    ```

2.  **Poblar BD**:
    ```bash
    uv run python -m app.db.seed
    ```

3.  **Ejecutar Localmente (Dev)**:
    ```bash
    uv run uvicorn app.main:app --reload --port 33201
    ```

4.  **Ejecutar Pruebas**:
    ```bash
    uv run pytest
    ```

5.  **Ejecutar Pruebas de Integración**:
    ```bash
    uv run python -m pytest tests/integration/test_metrics.py
    ```

## Despliegue (Docker)

1.  **Construir**:
    ```bash
    docker build -t orchestrator-agent .
    ```

2.  **Ejecutar**:
    ```bash
    docker run -p 8000:8000 --env-file .env orchestrator-agent
    ```

## Uso de la API

**POST /identify-and-answer**
- Encabezados: `Authorization: Bearer <API_TOKEN>`
- Datos del Formulario: `image` (Archivo), `question` (Texto)

## Seguridad
- Autenticación Bearer requerida.
- Imágenes fuertemente hasheadas para registros de privacidad.
- Verificaciones estrictas de tipo MIME (JPEG/PNG).

## Política de abstención y consideraciones (vigencia normativa y privacidad)

- Abstención: El asistente debe abstenerse de responder cuando:
  - No encuentra evidencia suficiente en los documentos indexados para sustentar una respuesta.
  - La consulta solicita asesoramiento legal, médico, financiero o decisiones con impacto legal que requieren juicio humano.
  - La pregunta pide datos personales sensibles o identificar a personas concretas.

- Mensaje de abstención sugerido:

  "No puedo responder con seguridad a esa consulta con la información disponible. Le recomiendo consultar el documento oficial o contactar a la unidad responsable."

- Vigencia normativa: Documente la fecha de vigencia encontrada en la fuente y preséntela junto a respuestas normativas. Si la vigencia es posterior o anterior a la consulta, advierta al usuario.

  Ejemplo de inclusión en respuestas:

  "Referencia: Reglamento de Admisión — vigencia 27-09-2025. Ver fuente para detalles y última versión." 

- Privacidad: Evite exponer información personal o sensible almacenada en las fuentes. Si las fuentes contienen datos personales, aplique redacción/anonimización y limite el contexto que se inserta en prompts.

## Tabla de trazabilidad (doc_id → URL / página / vigencia)

La siguiente tabla mapea los documentos usados en el índice a su ruta local, URL pública y fecha de vigencia (extraída de `data/sources.csv`).

| doc_id | nombre | ruta local | URL pública | fecha / vigencia |
|---|---|---|---|---|
| 01 | Reglamento Régimen de Estudios de Pregrado | `data/raw/01-Reglamento-de-Regimen-de-Estudios-2023.pdf` | https://www.ufro.cl/wp-content/uploads/2025/04/01-Reglamento-de-Regimen-de-Estudios-2023.pdf | 27-09-2025 |
| 02 | Reglamento de Admisión | `data/raw/02-Res-Ex-3542-2022-Reglamento-de-Admision-para-carreras-de-Pregrado.pdf` | https://www.ufro.cl/wp-content/uploads/2025/04/02-Res-Ex-3542-2022-Reglamento-de-Admision-para-carreras-de-Pregrado.pdf | 27-09-2025 |
| 03 | Reglamento de Obligaciones Financieras | `data/raw/03-resex-2022326308-obligaciones-financieras.pdf` | https://www.ufro.cl/wp-content/uploads/2025/04/03-resex-2022326308-obligaciones-financieras.pdf | 27-09-2025 |
| 04 | Reglamento de Convivencia Universitaria Estudiantil | `data/raw/04-Reglamento-Convivencia-rex.pdf` | https://www.ufro.cl/wp-content/uploads/2025/04/04-Reglamento-Convivencia-rex.pdf | 27-09-2025 |