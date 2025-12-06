import os
import motor.motor_asyncio
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "orchestrator_db")

class MongoDB:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    db = None

    @classmethod
    def get_db(cls):
        if cls.client is None:
            # tlsCAFile is often required for Atlas on some systems
            cls.client = motor.motor_asyncio.AsyncIOMotorClient(
                MONGO_URI,
                tlsCAFile=certifi.where()
            )
            cls.db = cls.client[DB_NAME]

        return cls.db

    @classmethod
    def close(cls):
        if cls.client:
            cls.client.close()
            cls.client = None
