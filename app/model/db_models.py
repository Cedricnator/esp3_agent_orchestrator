from pydantic import BaseModel
from typing import Optional

class AgentConfig(BaseModel):
    name: str
    endpoint_verify: str
    threshold: float
    active: bool
