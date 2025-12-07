import pytest
import shutil
import base64
from app.app import create_app
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
import httpx
from app.db.mongo import MongoDB

@pytest.fixture
def mock_mongo():
    # Mock the MongoDB client and db
    mock_db = MagicMock()
    mock_db.access_logs.insert_one = AsyncMock()
    mock_db.service_logs.insert_one = AsyncMock()
    mock_db.config.find = MagicMock(return_value=AsyncMock())
    
    # Patch the singleton
    MongoDB.db = mock_db
    yield mock_db
    # Teardown if needed (reset singleton)
    MongoDB.db = None

@pytest.fixture
def client_with_mock_db(mock_mongo):
    app = create_app()
    # Dependency Overrides could go here if needed
    with TestClient(app) as client:
        yield client

@pytest.fixture
def valid_token():
    return "secret-token-123" 

@pytest.fixture
def valid_image_bytes():
    # 1x1 white pixel PNG
    return base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
import pytest_asyncio

@pytest_asyncio.fixture
async def async_client_with_real_db():
    """
    Async Fixture that connects to the REAL database.
    Resolves 'different loop' errors by using AsyncClient.
    """
    # Force new connection in the current loop
    MongoDB.client = None 
    MongoDB.db = None
    
    app = create_app()
    
    # Use httpx.AsyncClient for ASGI app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client
    
    # Cleanup
    MongoDB.close()
