import asyncio
import os
import time
import httpx
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

from app.db.mongo import MongoDB

load_dotenv()

TIMEOUT = float(os.getenv("HTTP_CLIENT_TIMEOUT_SECONDS", "3.0"))

class PP2Service:
    def __init__(self):
        self.db = MongoDB.get_db()

    async def get_active_agents(self) -> List[Dict]:
        """Fetch active agents from the 'config' collection."""
        cursor = self.db.config.find({"active": True})
        agents = await cursor.to_list(length=100)
        return agents

    async def verify_parallel(self, request_id: str, image_b64: str) -> List[Dict]:
        """
        Fan-out to all active agents in parallel.
        Returns a list of results (one per agent).
        Also writes raw logs to 'service_logs'.
        """
        agents = await self.get_active_agents()
        if not agents:
            return []

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            tasks = [
                self._call_agent(client, agent, request_id, image_b64)
                for agent in agents
            ]
            results = await asyncio.gather(*tasks)
            return results

    async def _call_agent(self, client: httpx.AsyncClient, agent: Dict, request_id: str, image_b64: str) -> Dict:
        start_time = time.time()
        url = agent.get("endpoint_verify")
        name = agent.get("name")
        
        log_entry = {
            "request_id": request_id,
            "ts": datetime.utcnow(),
            "service_type": "pp2",
            "service_name": name,
            "endpoint": url,
            "payload_size_bytes": len(image_b64),
            "timeout": False,
            "error": None,
            "result": None,
            "status_code": 0
        }

        try:
            response = await client.post(url, json={"image": image_b64})
            latency_ms = round((time.time() - start_time) * 1000, 3)
            
            log_entry["latency_ms"] = latency_ms
            log_entry["status_code"] = response.status_code
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("score", 0.0)
                log_entry["result"] = {"score": score, "raw": data}
                
                return {
                    "agent_name": name,
                    "score": score,
                    "raw": data,
                    "latency_ms": latency_ms
                }
            else:
                log_entry["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
                return {"agent_name": name, "score": 0.0, "error": str(response.status_code)}

        except httpx.TimeoutException:
            latency_ms = round((time.time() - start_time) * 1000, 3)
            log_entry["latency_ms"] = latency_ms
            log_entry["timeout"] = True
            log_entry["error"] = "Timeout"
            return {"agent_name": name, "score": 0.0, "error": "Timeout"}

        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 3)
            log_entry["latency_ms"] = latency_ms
            log_entry["error"] = str(e)
            return {"agent_name": name, "score": 0.0, "error": str(e)}

        finally:
            await self.db.service_logs.insert_one(log_entry)
