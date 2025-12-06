from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app.db.mongo import MongoDB
from app.utils.logger import Logger

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = Logger()

# Helper to parse "days"
def get_start_date(days: int = 7) -> datetime:
    return datetime.utcnow() - timedelta(days=days)

@router.get("/summary")
async def get_summary(days: int = 7):
    """
    Get summary metrics (volume, latency, timeouts).
    """
    try:
        logger.info(f"[MetricsRouter] Fetching summary for last {days} days")
        db = MongoDB.get_db()
        start_date = get_start_date(days)
        
        # Volume & Error Rate
        pipeline = [
            {"$match": {"ts": {"$gte": start_date}}},
            {"$group": {
                "_id": None,
                "total_requests": {"$sum": 1},
                "avg_latency": {"$avg": "$timing_ms"},
                "timeouts": {"$sum": "$pp2_summary.timeouts"}
            }}
        ]
        cursor = db.access_logs.aggregate(pipeline)
        summary = await cursor.to_list(length=1)
        result = summary[0] if summary else {"total_requests": 0, "avg_latency": 0, "timeouts": 0}
        
        return {
            "period_days": days,
            **result
        }
    except Exception as e:
        logger.error(f"[MetricsRouter] Error fetching summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-user-type")
async def get_by_user_type(days: int = 7):
    """
    Get traffic distribution by user type.
    """
    try:
        logger.info(f"[MetricsRouter] Fetching user stats for last {days} days")
        db = MongoDB.get_db()
        start_date = get_start_date(days)
        
        pipeline = [
            {"$match": {"ts": {"$gte": start_date}}},
            {"$group": {
                "_id": "$user.type",
                "count": {"$sum": 1},
                "avg_latency": {"$avg": "$timing_ms"}
            }},
             {"$sort": {"count": -1}}
        ]
        cursor = db.access_logs.aggregate(pipeline)
        return await cursor.to_list(length=100)
    except Exception as e:
        logger.error(f"[MetricsRouter] Error fetching user stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decisions")
async def get_decisions(days: int = 7):
    """
    Get decision distribution (identified/ambiguous/unknown).
    """
    try:
        logger.info(f"[MetricsRouter] Fetching decisions for last {days} days")
        db = MongoDB.get_db()
        start_date = get_start_date(days)
        
        pipeline = [
            {"$match": {"ts": {"$gte": start_date}}},
            {"$group": {
                "_id": "$decision",
                "count": {"$sum": 1}
            }}
        ]
        cursor = db.access_logs.aggregate(pipeline)
        return await cursor.to_list(length=100)
    except Exception as e:
        logger.error(f"[MetricsRouter] Error fetching decisions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services")
async def get_services(days: int = 7):
    """
    Get PP2 service performance stats.
    """
    try:
        logger.info(f"[MetricsRouter] Fetching service stats for last {days} days")
        db = MongoDB.get_db()
        start_date = get_start_date(days)
        
        pipeline = [
            {"$match": {"ts": {"$gte": start_date}, "service_type": "pp2"}},
            {"$group": {
                "_id": "$service_name",
                "queries": {"$sum": 1},
                "timeouts": {"$sum": {"$cond": ["$timeout", 1, 0]}},
                "avg_latency": {"$avg": "$latency_ms"}
            }},
            {"$sort": {"timeouts": -1}}
        ]
        cursor = db.service_logs.aggregate(pipeline)
        return await cursor.to_list(length=100)
    except Exception as e:
        logger.error(f"[MetricsRouter] Error fetching service services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
