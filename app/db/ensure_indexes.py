import asyncio
from app.db.mongo import MongoDB

async def ensure_indexes():
    db = MongoDB.get_db()
    
    # 1. Access Logs Indexes
    # { ts: -1 } (recientes)
    await db.access_logs.create_index([("ts", -1)])
    # { "user.type": 1, ts: -1 }
    await db.access_logs.create_index([("user.type", 1), ("ts", -1)])
    # { route: 1, ts: -1 }
    await db.access_logs.create_index([("route", 1), ("ts", -1)])
    # { decision: 1, ts: -1 }
    await db.access_logs.create_index([("decision", 1), ("ts", -1)])

    # 2. Service Logs Indexes
    # { service_name: 1, ts: -1 }
    await db.service_logs.create_index([("service_name", 1), ("ts", -1)])
    # { service_type: 1, ts: -1 }
    await db.service_logs.create_index([("service_type", 1), ("ts", -1)])
    # { status_code: 1, ts: -1 }
    await db.service_logs.create_index([("status_code", 1), ("ts", -1)])

    print("Indexes created successfully.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ensure_indexes())
