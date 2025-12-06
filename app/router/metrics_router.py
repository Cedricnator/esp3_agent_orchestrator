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
    Get summary metrics (volume, latency, timeouts) + per-route stats.
    """
    try:
        logger.info(f"[MetricsRouter] Fetching summary for last {days} days")
        db = MongoDB.get_db()
        start_date = get_start_date(days)
        
        # Faceted Aggregation: Overall Summary + Per Route
        # We need latencies array to calc p95 securely in Python
        pipeline = [
            {"$match": {"ts": {"$gte": start_date}}},
            {"$facet": {
                "overall": [
                    {"$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "avg_latency": {"$avg": "$timing_ms"},
                        "timeouts": {"$sum": "$pp2_summary.timeouts"}
                    }}
                ],
                "routes": [
                    {"$group": {
                        "_id": "$route",
                        "count": {"$sum": 1},
                        "latencies": {"$push": "$timing_ms"},
                        "avg_latency": {"$avg": "$timing_ms"}
                    }}
                ]
            }}
        ]
        
        cursor = db.access_logs.aggregate(pipeline)
        data = await cursor.to_list(length=1)
        
        if not data:
             return {"period_days": days, "total_requests": 0, "routes": []}
             
        facet_result = data[0]
        overall = facet_result["overall"][0] if facet_result["overall"] else {"total_requests": 0, "avg_latency": 0.0, "timeouts": 0}
        routes_raw = facet_result["routes"]
        
        # Calculate Percentiles per route
        routes_processed = []
        import statistics
        
        for r in routes_raw:
            latencies = sorted(r["latencies"])
            count = len(latencies)
            # Simple percentile calculation
            def get_percentile(data, p):
                 if not data: return 0
                 k = (len(data)-1) * p
                 f = int(k)
                 c = int(k) + 1
                 if c >= len(data): return data[-1]
                 return data[f] * (c-k) + data[c] * (k-f)

            p50 = get_percentile(latencies, 0.50)
            p95 = get_percentile(latencies, 0.95)
            
            routes_processed.append({
                "route": r["_id"],
                "count": r["count"],
                "avg_latency": round(r["avg_latency"], 3),
                "p50": round(p50, 3),
                "p95": round(p95, 3)
            })

        return {
            "period_days": days,
            "total_requests": overall["total_requests"],
            "avg_latency": round(overall["avg_latency"], 3),
            "timeouts": overall["timeouts"],
            "routes": routes_processed
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
