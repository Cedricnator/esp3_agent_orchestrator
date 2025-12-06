from app.db.mongo import MongoDB

async def seed_db():
    """
    Run on startup to ensure a consistent dev environment.
    """
    db = MongoDB.get_db()
    
    # 1. Clear existing data
    await db.config.delete_many({})
    await db.access_logs.delete_many({})
    await db.service_logs.delete_many({})
    
    # 2. Seed Data
    dummy_agents = [
        {
            "name": "Agent Alpha (Mock)",
            "endpoint_verify": "http://mock-pp2-alpha/verify",
            "threshold": 0.85,
            "active": True
        },
        {
            "name": "Agent Beta (Mock)",
            "endpoint_verify": "http://mock-pp2-beta/verify",
            "threshold": 0.75,
            "active": True
        },
        {
             "name": "Agent Gamma (Inactive)",
             "endpoint_verify": "http://mock-pp2-gamma/verify",
             "threshold": 0.60,
             "active": False
        }
    ]
    
    await db.config.insert_many(dummy_agents)
    print(f"[Seed] Reset 'config' collection with {len(dummy_agents)} dummy agents.")

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(seed_db())
