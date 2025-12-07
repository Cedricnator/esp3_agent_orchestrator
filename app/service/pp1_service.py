import os
import time
from app.utils.logger import Logger
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from app.db.mongo import MongoDB

load_dotenv()

PP1_URL = os.getenv("PP1_URL", "http://localhost:8001")
TIMEOUT = float(os.getenv("PP1_CLIENT_TIMEOUT_SECONDS", "40.0"))

class PP1Service:
    def __init__(self):
        self.db = MongoDB.get_db()
        self.logger = Logger()

    async def ask_normativa(self, request_id: str, question: str) -> Optional[Dict[str, Any]]:
        """
        Calls PP1 RAG agent.
        Logs interaction to 'service_logs'.
        """
        url = f"{PP1_URL}/ask"
        start_time = time.time()
        
        log_entry = {
            "request_id": request_id,
            "ts": datetime.utcnow(),
            "service_type": "pp1",
            "service_name": "UFRO-RAG",
            "endpoint": url,
            "payload_size_bytes": len(question),
            "timeout": False,
            "error": None,
            "result": None,
            "status_code": 0
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                payload = {
                    "message": question,
                    "use_rag": True,
                    "top_k": 5
                }

                response = await client.post(url, json=payload)
                latency_ms = round((time.time() - start_time) * 1000, 3)
                
                log_entry["latency_ms"] = latency_ms
                log_entry["status_code"] = response.status_code

                if response.status_code == 200:
                    data = response.json()
                    self.logger.info(f"[PP1Service] Received response from PP1: {data}")
                    log_entry["result"] = data
                    
                    return {
                        "text": data.get("response", ""),
                        "citations": data.get("citations", [])
                    }
                else:
                    log_entry["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
                    return None

            except httpx.TimeoutException:
                log_entry["latency_ms"] = round((time.time() - start_time) * 1000, 3)
                log_entry["timeout"] = True
                log_entry["error"] = "Timeout"
                return None
            
            except Exception as e:
                log_entry["latency_ms"] = round((time.time() - start_time) * 1000, 3)
                log_entry["error"] = str(e)
                return None
            
            finally:
                await self.db.service_logs.insert_one(log_entry)
