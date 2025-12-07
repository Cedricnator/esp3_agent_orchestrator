from typing import Optional
from pydantic import BaseModel
from enum import Enum

class DecisionEnum(str, Enum):
    identified = "identified"
    ambiguous = "ambiguous"
    unknown = "unknown"

class Identity(BaseModel):
    name: Optional[str]
    score: float

class Citation(BaseModel):
    doc: str
    page: Optional[str] = None
    url: Optional[str] = None
