from mcp.server.fastmcp import FastMCP
from app.model.api_models import IdentifyResponse, Identity, NormativaAnswer
from app.service.pp2_service import PP2Service
from app.service.fusion_service import FusionService
from app.service.pp1_service import PP1Service
from app.db.mongo import MongoDB
import asyncio
from uuid import uuid4
import base64
import httpx
from datetime import datetime

# Initialize FastMCP Server
mcp = FastMCP("Orchestrator Agent")



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
    
    # 1. Verify
    pp2_results = await pp2.verify_parallel(request_id, image_b64)
    
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
