from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router.app_router import app_router
from app.utils.logger import Logger

load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(title="Orchestrator Agent", version="1.0.0")
    logger = Logger()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware added")

    app.include_router(app_router)
    logger.info("FastAPI routers added")

    logger.info("FastAPI application initialized")
    return app
