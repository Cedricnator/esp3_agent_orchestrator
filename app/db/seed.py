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
    agents = [
        {
            "name": "Eduardo Arévalo",
            "endpoint_verify": "http://localhost:33210/verify",
            "threshold": 0.75,
            "active": True
        },
        {
            "name": "Cedric Kirmayr",
            "endpoint_verify": "http://localhost:33211/verify",
            "threshold": 0.75,
            "active": True
        },
    ]
    
    await db.config.insert_many(agents)
    print(f"[Seed] Successfully added seed data, agents: {len(agents)}")

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(seed_db())
