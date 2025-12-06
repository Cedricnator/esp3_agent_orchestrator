import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Defaults
THRESHOLD = float(os.getenv("THRESHOLD", "0.75"))
MARGIN = float(os.getenv("MARGIN", "0.10"))

class FusionService:
    def __init__(self):
        self.threshold = THRESHOLD
        self.margin = MARGIN

    def process_results(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Analyzes a list of result dictionaries from PP2 agents.
        """
        valid_results = [r for r in results if r.get("score", 0.0) > 0]
        sorted_results = sorted(valid_results, key=lambda x: x.get("score", 0.0), reverse=True)
        
        candidates = []
        for r in sorted_results[:5]:
            candidates.append({
                "name": r.get("agent_name"),
                "score": r.get("score")
            })

        if not sorted_results:
            return {
                "decision": "unknown",
                "identity": {"name": None, "score": 0.0},
                "candidates": []
            }

        top_match = sorted_results[0]
        max_score = top_match.get("score", 0.0)
        
        runner_up_score = 0.0
        if len(sorted_results) > 1:
            runner_up_score = sorted_results[1].get("score", 0.0)

        if max_score < self.threshold:
            decision = "unknown"
            identity_data = {"name": None, "score": max_score}
        else:
            if (max_score - runner_up_score) > self.margin:
                decision = "identified"
                identity_data = {"name": top_match.get("agent_name"), "score": max_score}
            else:
                decision = "ambiguous"
                identity_data = {"name": top_match.get("agent_name"), "score": max_score}

        return {
            "decision": decision,
            "identity": identity_data,
            "candidates": candidates
        }
