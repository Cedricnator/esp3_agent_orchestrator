import pytest
import uuid
from datetime import datetime
from app.db.mongo import MongoDB

@pytest.mark.asyncio
async def test_metrics_endpoints_real_db(async_client_with_real_db):
    """
    Integration test using REAL MongoDB to verify ALL Metrics Endpoints.
    """
    db = MongoDB.get_db()
    
    # --- SETUP UNIQUE DATA IDENTIFIER ---
    test_run_id = str(uuid.uuid4())
    test_route = f"/test-metrics-{test_run_id}"
    test_service_name = f"TestService-{test_run_id}"
    
    # 1. SETUP ACCESS LOGS (for summary, by-user-type, decisions)
    access_logs = [
        {
            "ts": datetime.utcnow(),
            "route": test_route,
            "decision": "identified",
            "timing_ms": 100.0,
            "status_code": 200,
            "user": {"type": "student"}
        },
        {
            "ts": datetime.utcnow(),
            "route": test_route,
            "decision": "unknown",
            "timing_ms": 50.0,
            "status_code": 200,
            "user": {"type": "student"}
        },
         {
            "ts": datetime.utcnow(),
            "route": test_route,
            "decision": "ambiguous",
            "timing_ms": 150.0,
            "status_code": 422,
            "user": {"type": "faculty"}
        }
    ]
    await db.access_logs.insert_many(access_logs)

    # 2. SETUP SERVICE LOGS (for services metrics)
    service_logs = [
        {
            "ts": datetime.utcnow(),
            "service_type": "pp2",
            "service_name": test_service_name,
            "latency_ms": 50.0,
            "timeout": False
        },
        {
            "ts": datetime.utcnow(),
            "service_type": "pp2",
            "service_name": test_service_name,
            "latency_ms": 2000.0,
            "timeout": True
        }
    ]
    await db.service_logs.insert_many(service_logs)

    try:
        # --- TEST 1: SUMMARY ---
        response = await async_client_with_real_db.get("/metrics/summary?days=1")
        assert response.status_code == 200
        data = response.json()
        
        routes = data.get("routes", [])
        identify_route = next((r for r in routes if r["route"] == test_route), None)
        assert identify_route is not None
        assert identify_route["count"] == 3
        assert 50 <= identify_route["p95"] <= 200

        # --- TEST 2: BY USER TYPE ---
        # Note: This endpoint aggregates ALL data, so we check if our inserted types exist or are counted.
        # Since we can't isolate by route in this endpoint (it groups by user.type), 
        # we can only assert the structure and that stats are returned.
        response = await async_client_with_real_db.get("/metrics/by-user-type?days=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check if 'student' type shows up (might include pre-existing data, but should exist)
        student_stats = next((item for item in data if item["_id"] == "student"), None)
        assert student_stats is not None
        assert student_stats["count"] >= 2

        # --- TEST 3: DECISIONS ---
        response = await async_client_with_real_db.get("/metrics/decisions?days=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        identified_stats = next((item for item in data if item["_id"] == "identified"), None)
        assert identified_stats is not None
        assert identified_stats["count"] >= 1

        # --- TEST 4: SERVICES ---
        response = await async_client_with_real_db.get("/metrics/services?days=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        test_service_stats = next((item for item in data if item["_id"] == test_service_name), None)
        assert test_service_stats is not None
        assert test_service_stats["queries"] == 2
        assert test_service_stats["timeouts"] == 1

    finally:
        # --- CLEANUP ---
        await db.access_logs.delete_many({"route": test_route})
        await db.service_logs.delete_many({"service_name": test_service_name})
