import os
import hashlib
from typing import Annotated
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

security_scheme = HTTPBearer()

async def verify_token(credentials: Annotated[HTTPAuthorizationCredentials, Security(security_scheme)]):
    """
    Verifies that the Bearer token matches the API_TOKEN env var.
    """
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Security Misconfiguration, API_TOKEN not setup"
        )
    
    if credentials.credentials != api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

def hash_data(data: bytes) -> str:
    """
    Returns SHA256 hash of the data (hex digest).
    Used for logging distinct images without storing Personal Data.
    """
    return hashlib.sha256(data).hexdigest()
