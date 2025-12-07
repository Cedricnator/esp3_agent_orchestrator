from typing import Annotated, Optional
from fastapi import APIRouter, File, Form, UploadFile, Header, Request, HTTPException, Depends
from app.model.api_models import IdentifyResponse
from app.service.orchestrator_service import OrchestratorService
from app.utils.logger import Logger
from app.utils.security import verify_token, hash_data

from app.service.validation_service import ValidationService

router = APIRouter()
logger = Logger()

# Instantiate Services
orchestrator_service = OrchestratorService()
validation_service = ValidationService()

@router.post("/identify-and-answer", response_model=IdentifyResponse, dependencies=[Depends(verify_token)])
async def identify_and_answer(
    request: Request,
    image: Annotated[UploadFile, File(...)],
    question: Annotated[Optional[str], Form()] = None,
    x_user_id: Annotated[Optional[str], Header()] = None,
    x_user_type: Annotated[Optional[str], Header()] = None,
):
    """
    Process an identification request and optionally answer a question.
    Requires Bearer Token authentication.
    """
    try:
        logger.info(f"[OrchestratorRouter] Received identify request from user_id={x_user_id} type={x_user_type}")
        
        image_bytes = await image.read()

        # 1. Validation
        validation_service.validate_image(image, image_bytes)

        # 2. Metadata (Hashing)
        image_hash = hash_data(image_bytes)

        # Construct Context
        user_context = {
            "id": x_user_id,
            "type": x_user_type,
            "role": "basic"
        }

        # Delegate to Service
        response = await orchestrator_service.handle_identify_request(
            image=image,
            image_bytes=image_bytes,
            question=question,
            user_context=user_context,
            request_obj=request,
            image_hash=image_hash
        )
        
        return response

    except HTTPException as e:
        logger.error(f"[OrchestratorRouter] HTTP Exception: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"[OrchestratorRouter] Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
