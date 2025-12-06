import pytest
from app.service.fusion_service import FusionService
import os

class TestFusionService:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Ensure default env vars for tests
        os.environ["FUSION_SCORE_THRESHOLD"] = "0.75"
        os.environ["FUSION_SCORE_MARGIN"] = "0.10"
        self.service = FusionService()

    def test_fusion_identified(self):
        # Clear winner
        results = [
            {"agent_name": "Ana", "score": 0.90},
            {"agent_name": "Luis", "score": 0.40},
            {"agent_name": "Pedro", "score": 0.10}
        ]
        decision = self.service.process_results(results)
        
        assert decision["decision"] == "identified"
        assert decision["identity"]["name"] == "Ana"
        assert decision["identity"]["score"] == 0.90

    def test_fusion_ambiguous(self):
        # Close race (Margin < 0.10)
        results = [
            {"agent_name": "Ana", "score": 0.85},
            {"agent_name": "Luis", "score": 0.80} # Diff is 0.05
        ]
        decision = self.service.process_results(results)
        
        assert decision["decision"] == "ambiguous"
        assert decision["identity"]["name"] == "Ana" # Top candidate still returned
    
    def test_fusion_unknown_low_score(self):
        # Winner below threshold (0.75)
        results = [
            {"agent_name": "Ana", "score": 0.60},
            {"agent_name": "Luis", "score": 0.50}
        ]
        decision = self.service.process_results(results)
        
        assert decision["decision"] == "unknown"
        assert decision["identity"]["name"] is None

    def test_fusion_empty_results(self):
        results = []
        decision = self.service.process_results(results)
        assert decision["decision"] == "unknown"
