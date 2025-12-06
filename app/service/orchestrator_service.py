from datetime import datetime
from uuid import uuid4
import base64
import time
from typing import Optional, Dict

from fastapi import HTTPException

from app.db.mongo import MongoDB
from app.service.pp2_service import PP2Service
from app.service.pp1_service import PP1Service
from app.service.fusion_service import FusionService
from app.model.api_models import IdentifyResponse, Identity, NormativaAnswer
from app.model.common import DecisionEnum

class OrchestratorService:
    def __init__(self):
        self.pp2 = PP2Service()
        self.pp1 = PP1Service()
        self.fusion = FusionService()
        self.mongo = MongoDB()

    async def handle_identify_request(
        self,
        image_bytes: bytes,
        question: Optional[str],
        user_context: Dict,
        request_obj=None,
        image_hash: str = None
    ) -> IdentifyResponse:
        
        start_time = time.time()
        request_id = str(uuid4())
        
        # Image -> B64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        # 1. PP2 Fan-Out
        pp2_results = await self.pp2.verify_parallel(request_id, image_b64)

        # Check for Multiple Timeouts/Errors
        # "send an error if more than one service pp2 fails to respond properly"
        error_count = sum(1 for r in pp2_results if r.get("error"))
        if error_count > 1:
             # Log the failure before raising exception so we have a record
             raise HTTPException(
                 status_code=504, 
                 detail=f"Multiple PP2 services failed. Errors: {error_count}/{len(pp2_results)}"
             )

        # 2. Fusion
        fusion_result = self.fusion.process_results(pp2_results)
        decision = fusion_result["decision"] # Str
        identity_data = fusion_result["identity"]
        candidates = fusion_result["candidates"]

        # 3. PP1 (RAG)
        normativa_answer = None
        pp1_used = False
        if decision == "identified" and question:
            pp1_used = True
            rag_result = await self.pp1.ask_normativa(request_id, question)
            if rag_result:
                normativa_answer = NormativaAnswer(**rag_result)

        timing_ms = round((time.time() - start_time) * 1000, 3)

        # 4. Log to Access Logs
        await self._log_access(
            request_id=request_id,
            user_context=user_context,
            input_meta={
                "has_image": True, 
                "has_question": bool(question), 
                "size_bytes": len(image_bytes),
                "image_hash": image_hash
            },
            decision=decision,
            identity=identity_data,
            pp2_summary={"queried": len(pp2_results), "timeouts": sum(1 for r in pp2_results if r.get("error") == "Timeout")},
            pp1_used=pp1_used,
            timing_ms=timing_ms,
            ip=request_obj.client.host if request_obj and request_obj.client else "unknown"
        )
        
        return IdentifyResponse(
            decision=DecisionEnum(decision),
            identity=Identity(**identity_data),
            candidates=[Identity(**c) for c in candidates],
            normativa_answer=normativa_answer,
            timing_ms=timing_ms,
            request_id=request_id
        )

    async def _log_access(self, request_id, user_context, input_meta, decision, identity, pp2_summary, pp1_used, timing_ms, ip):
        log_entry = {
            "request_id": request_id,
            "ts": datetime.utcnow(),
            "route": "/identify-and-answer",
            "user": user_context,
            "input_metadata": input_meta,
            "decision": decision,
            "identity": identity,
            "pp2_summary": pp2_summary,
            "pp1_used": pp1_used,
            "timing_ms": timing_ms,
            "status_code": 200,
            "ip": ip
        }
        db = self.mongo.get_db()
        await db.access_logs.insert_one(log_entry)
