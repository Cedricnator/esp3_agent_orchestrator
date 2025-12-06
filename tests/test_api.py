from unittest.mock import AsyncMock, patch
import os

# We need to set API_TOKEN in env BEFORE importing security or creating app in some cases,
# but our conftest usually handles client creation. We patch the verify_token or use a proper token.
# Here we'll simulate environment setup via fixture or os.environ.

def test_identify_no_token(client_with_mock_db):
    # Should fail 403/401
    response = client_with_mock_db.post("/identify-and-answer")
    assert response.status_code == 401  # HTTPBearer default

@patch("app.service.pp2_service.PP2Service.verify_parallel")
def test_identify_success(mock_verify, client_with_mock_db, valid_image_bytes):
    # Setup Env
    os.environ["API_TOKEN"] = "test-token"
    
    # Mock Service Response
    mock_verify.return_value = [{"agent_name": "Ana", "score": 0.95}]
    
    files = {"image": ("test.png", valid_image_bytes, "image/png")}
    headers = {"Authorization": "Bearer test-token"}
    
    response = client_with_mock_db.post(
        "/identify-and-answer", 
        files=files,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "identified"
    assert data["identity"]["name"] == "Ana"

def test_identify_invalid_mime(client_with_mock_db, valid_image_bytes):
    os.environ["API_TOKEN"] = "test-token"
    
    # Send as text/plain
    files = {"image": ("test.txt", valid_image_bytes, "text/plain")}
    headers = {"Authorization": "Bearer test-token"}
    
    response = client_with_mock_db.post(
        "/identify-and-answer", 
        files=files,
        headers=headers
    )
    
    assert response.status_code == 415
