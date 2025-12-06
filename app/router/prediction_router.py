from fastapi import APIRouter, HTTPException

from app.dto.api_response import ApiResponse
from app.utils.logger import Logger 

router_logger = Logger()

prediction_router = APIRouter()

@prediction_router.get("/test", response_model=ApiResponse)
def test():
   try:
      router_logger.info('[Prediction] Test endpoint called')

      return {
         "response": 'Successfully started test process'
      }
   except ValueError as e:
      router_logger.error(f'[Prediction] Validation error: {str(e)}')
      raise HTTPException(status_code=400, detail=str(e))
   except Exception as e:
      router_logger.error(f'[Prediction] Error processing query: {str(e)}')
      raise HTTPException(
         status_code=500, 
         detail="Lo sentimos, ha ocurrido un error procesando tu consulta."
      )