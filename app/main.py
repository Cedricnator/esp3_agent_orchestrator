import uvicorn
from app.app import create_app

app = create_app()

def main():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=33205,
        log_level="info",
        reload=True,      # only in dev
    )

if __name__ == "__main__":
    main()
