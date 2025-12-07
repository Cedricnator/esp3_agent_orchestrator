from pydantic import BaseModel

class ApiResponse(BaseModel):
   response: str