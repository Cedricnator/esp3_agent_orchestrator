from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, UploadFile, Header, Request, HTTPException

from app.model.api_models import IdentifyResponse
from app.service.orchestrator_service import OrchestratorService
from app.utils.logger import Logger

router = APIRouter()
logger = Logger()

# Instantiate Service
orchestrator_service = OrchestratorService()

@router.post("/identify-and-answer", response_model=IdentifyResponse)
async def identify_and_answer(
    request: Request,
    image: Annotated[UploadFile, File(...)],
    question: Annotated[Optional[str], Form()] = None,
    x_user_id: Annotated[Optional[str], Header()] = None,
    x_user_type: Annotated[Optional[str], Header()] = None,
):
    """
    Process an identification request and optionally answer a question.
    """
    try:
        logger.info(f"[OrchestratorRouter] Received identify request from user_id={x_user_id} type={x_user_type}")
        
        # Construct Context
        user_context = {
            "id": x_user_id,
            "type": x_user_type,
            "role": "basic"
        }

        image_bytes = await image.read()

        # Delegate to Service
        response = await orchestrator_service.handle_identify_request(
            image_bytes=image_bytes,
            question=question,
            user_context=user_context,
            request_obj=request
        )
        
        return response

    except HTTPException as e:
        logger.error(f"[OrchestratorRouter] HTTP Exception: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"[OrchestratorRouter] Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
