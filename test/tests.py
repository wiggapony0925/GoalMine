import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json

# Import Agents directly
from agents.gatekeeper.gatekeeper import Gatekeeper
from agents.tactics.tactics import TacticsAgent
from agents.market.market import MarketAgent
from agents.logistics.logistics import LogisticsAgent
from services import orchestrator

class TestGoalMineSystem(unittest.TestCase):

    # --- 1. GATEKEEPER TESTS ---
    def test_gatekeeper_off_topic(self):
        """ Test handling of non-betting prompts (Cooking/Coding) """
        print("\n🔒 Testing Gatekeeper Firewall...")
        
        # We mock the internal Async classification strictly for the return value
        # But in a real Integration Test, this hits the LLM. 
        # For unit testing speed, we assume the LLM works (tested via Prompt Engineering).
        # We manually verify the Logic flow.
        
        # Simulate LLM returning 'OFF_TOPIC' for "Bake a cake"
        with patch('agents.gatekeeper.gatekeeper.query_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "OFF_TOPIC"
            
            intent, _ = Gatekeeper.classify_intent("How do I bake a chocolate cake?")
            self.assertEqual(intent, "OFF_TOPIC")
            print("✅ Gatekeeper blocked 'Cooking' request.")

    def test_gatekeeper_betting(self):
        with patch('agents.gatekeeper.gatekeeper.query_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "BETTING"
            
            intent, text = Gatekeeper.classify_intent("Analyze France vs USA")
            self.assertEqual(intent, "BETTING")
            self.assertEqual(text, "Analyze France vs USA")
            print("✅ Gatekeeper allowed 'Betting' request.")

    # --- 2. ORCHESTRATOR & ENTITY EXTRACTION ---
    def test_entity_extraction(self):
        """ Test identifying teams from text """
        print("\n🧠 Testing Entity Extraction...")
        with patch('services.orchestrator.query_llm', new_callable=AsyncMock) as mock_llm:
            mock_json = json.dumps({
                "home_team": "Brazil",
                "away_team": "Spain",
                "venue_from": "MetLife_NY",
                "venue_to": "Azteca_Mexico"
            })
            mock_llm.return_value = mock_json
            
            data = asyncio.run(orchestrator.extract_match_details_from_text("Predict bets for Brazil vs Spain"))
            self.assertEqual(data['home_team'], "Brazil")
            print("✅ Orchestrator extracted 'Brazil vs Spain'.")

    # --- 3. AGENT FALLBACKS (Unit Level) ---
    def test_market_agent_fallback(self):
        """ Test Market Agent handles API failure gracefully """
        print("\n📉 Testing Market Agent Fallback...")
        agent = MarketAgent()
        
        # Force API Exception
        with patch('agents.market.market.fetch_latest_odds', side_effect=Exception("API Down")):
             with patch('agents.market.market.query_llm', new_callable=AsyncMock) as mock_llm:
                 mock_llm.return_value = "Estimated Odds: France -150"
                 
                 res = asyncio.run(agent.analyze(odds_data=None))
                 self.assertEqual(res['data_source'], "VEGAS_ESTIMATOR_FALLBACK")
                 print("✅ Market Agent switched to VEGAS_FALLBACK on API failure.")

    def test_tactics_agent_live_awareness(self):
        """ Test Tactics Agent identifies Half-Time context """
        print("\n♟️ Testing Tactics Agent Live Logic...")
        agent = TacticsAgent()
        
        # Mocking the LLM response to confirm it sees the context
        with patch('agents.tactics.tactics.query_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "{\"game_state\": \"HT\", \"ht_recommendation\": \"Bet Over\"}"
            
            # We bypass the API call mock for this logic test and pass mock data directly if method allowed
            # Since analyze() calls API internally, we mock the API function
            mock_api_data = {
                "name": "France", 
                "live_status": "HT", 
                "minute": 45, 
                "current_score": "0-1",
                "roster_sample": [], "recent_form": []
            }
            
            with patch('agents.tactics.tactics.fetch_team_stats', return_value=mock_api_data):
                res = asyncio.run(agent.analyze("1", "2"))
                self.assertIn("HT", res['tactical_analysis'])
                print("✅ Tactics Agent acknowledged Half-Time context.")

if __name__ == '__main__':
    unittest.main()
