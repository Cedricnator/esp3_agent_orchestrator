import multiprocessing
import os

host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "33201")
bind = f"{host}:{port}"

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

tmeout = 120
keepalive = 5

loglevel = "info"
accesslog = "-" 
errorlog = "-"
