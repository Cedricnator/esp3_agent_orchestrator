from mcp.server.fastmcp import FastMCP
from app.service.pp2_service import PP2Service
from app.service.fusion_service import FusionService
from app.service.pp1_service import PP1Service
from app.db.mongo import MongoDB
from uuid import uuid4
import base64
import io
from datetime import datetime

# Initialize FastMCP Server
mcp = FastMCP("Orchestrator Agent")

class MockUploadFile:
    def __init__(self, data: bytes, filename: str = "image.jpg", content_type: str = "image/jpeg"):
        self.file = io.BytesIO(data)
        self.filename = filename
        self.content_type = content_type

    async def read(self, size: int = -1) -> bytes:
        return self.file.read(size)

    async def seek(self, offset: int) -> None:
        self.file.seek(offset)

    async def close(self) -> None:
        self.file.close()

def detect_image_info(data: bytes) -> tuple[str, str]:
    if data.startswith(b'\xff\xd8\xff'):
        return "image.jpg", "image/jpeg"
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image.png", "image/png"
    elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return "image.gif", "image/gif"
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return "image.webp", "image/webp"
    return "image.jpg", "image/jpeg"

pp2 = PP2Service()
fusion = FusionService()
pp1 = PP1Service()
mongo = MongoDB()

@mcp.tool()
async def identify_person(image_b64: str, timeout_s: float = 3.0) -> str:
    """
    Identifies a person from a base64 encoded image string.
    """
    request_id = str(uuid4())
    
    # Handle data URI scheme if present
    if "," in image_b64:
        image_b64 = image_b64.split(",")[1]

    try:
        image_bytes = base64.b64decode(image_b64)
        if not image_bytes:
            return "Error: Decoded image is empty."
            
        filename, content_type = detect_image_info(image_bytes)
        mock_file = MockUploadFile(image_bytes, filename=filename, content_type=content_type)
    except Exception as e:
        return f"Error decoding image: {str(e)}"
    
    # 1. Verify
    pp2_results = await pp2.verify_parallel(request_id, mock_file)
    
    # 2. Fuse
    fusion_result = fusion.process_results(pp2_results)
    decision = fusion_result["decision"]
    identity_data = fusion_result["identity"]
    
    # Log logic duplicated here for simple tool usage as requested in plan
    log_entry = {
         "request_id": request_id,
         "ts": datetime.utcnow(),
         "route": "mcp:identify_person",
         "user": {"id": "mcp-user", "type": "mcp"},
         "input_metadata": {"has_image": True, "size_bytes": len(image_b64)},
         "decision": decision,
         "identity": identity_data,
         "pp2_summary": {"queried": len(pp2_results)},
         "status_code": 200,
         "pp1_used": False
    }
    db = mongo.get_db()
    # Ensure logs collection exists or is written
    await db.access_logs.insert_one(log_entry)
    
    if decision == "identified":
        return f"Identified as {identity_data['name']} (Score: {identity_data['score']:.2f})"
    elif decision == "ambiguous":
        return f"Ambiguous result. Top candidate: {identity_data['name']} ({identity_data['score']:.2f})"
    else:
        return "Unknown person."

@mcp.tool()
async def ask_normativa(question: str) -> str:
    """
    Asks a question about university regulations.
    """
    request_id = str(uuid4())
    result = await pp1.ask_normativa(request_id, question)
    
    if result:
        text = result['text']
        citations = [f"- {c.get('doc')} (Page {c.get('page')})" for c in result.get('citations', [])]
        citations_str = "\n".join(citations)
        return f"Answer: {text}\n\nCitations:\n{citations_str}"
    else:
        return "Could not retrieve an answer at this time."

if __name__ == "__main__":
    mcp.run()
