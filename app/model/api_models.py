from typing import List, Optional
from pydantic import BaseModel
from app.model.common import DecisionEnum, Identity

class NormativaAnswer(BaseModel):
    text: str
    # citations: List[Citation]

class IdentifyResponse(BaseModel):
    decision: DecisionEnum
    identity: Identity
    candidates: List[Identity]
    normativa_answer: Optional[NormativaAnswer] = None
    timing_ms: float
    request_id: str
