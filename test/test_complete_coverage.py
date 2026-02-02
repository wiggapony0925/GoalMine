"""
COMPREHENSIVE TEST SUITE FOR GOALMINE
100% Coverage Strategy

This test suite validates EVERY component documented in README.md:
1. Core Infrastructure (initializer/)
2. All 6 Agents (Gatekeeper, Logistics, Tactics, Market, Narrative, Quant)
3. God View System
4. Orchestrator
5. Big Daddy (generate_bets.py)
6. Both Conversation Flows
7. Database Operations
8. Configuration System

Run with: pytest test/test_complete_coverage.py -v
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import os

# ===================================================================
# TEST 1: CORE INFRASTRUCTURE (/core/initializer/)
# ===================================================================

class TestCoreInfrastructure:
    """Tests for llm.py, whatsapp.py, database.py"""
    
    @pytest.mark.asyncio
    async def test_llm_query_basic(self):
        """Test llm.py can make basic OpenAI call"""
        from core.initializer.llm import query_llm
        
        with patch('core.initializer.llm.client.chat.completions.create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test response"))]
            mock_create.return_value = mock_response
            
            result = await query_llm(
                system_prompt="You are a test",
                user_content="Hello",
                config_key="gatekeeper"
            )
            
            assert result == "Test response"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_llm_config_routing(self):
        """Test llm.py correctly routes model configs from settings.json"""
        from core.initializer.llm import query_llm
        from core.config import settings
        
        # Test gatekeeper gets gpt-4o-mini
        gatekeeper_config = settings.get('llm.gatekeeper')
        assert gatekeeper_config['model'] == 'gpt-4o-mini'
        assert gatekeeper_config['temperature'] == 0.1
        
        # Test closer (Big Daddy) gets gpt-4o
        closer_config = settings.get('llm.closer')
        assert closer_config['model'] == 'gpt-4o'
        assert closer_config['temperature'] == 0.5
    
    @pytest.mark.asyncio
    async def test_llm_json_mode(self):
        """Test llm.py JSON mode validation"""
        from core.initializer.llm import query_llm
        
        with patch('core.initializer.llm.client.chat.completions.create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content='{"test": "data"}'))]
            mock_create.return_value = mock_response
            
            result = await query_llm(
                system_prompt="Return JSON",
                user_content="Test",
                json_mode=True
            )
            
            # Should be valid JSON
            parsed = json.loads(result)
            assert parsed['test'] == 'data'
    
    @pytest.mark.asyncio
    async def test_llm_retry_logic(self):
        """Test llm.py retry on failure"""
        from core.initializer.llm import query_llm
        
        with patch('core.initializer.llm.client.chat.completions.create') as mock_create:
            # Fail twice, then succeed
            mock_create.side_effect = [
                Exception("API Error"),
                Exception("API Error"),
                Mock(choices=[Mock(message=Mock(content="Success"))])
            ]
            
            result = await query_llm(
                system_prompt="Test",
                user_content="Test"
            )
            
            assert result == "Success"
            assert mock_create.call_count == 3  # 2 retries + 1 success
    
    def test_whatsapp_client_init(self):
        """Test WhatsApp client initialization"""
        from core.initializer.whatsapp import WhatsAppClient
        
        client = WhatsAppClient()
        assert client.api_url is not None
        assert "messages" in client.api_url
    
    def test_whatsapp_send_text(self):
        """Test WhatsApp send_message"""
        from core.initializer.whatsapp import WhatsAppClient
        
        client = WhatsAppClient()
        
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {"success": True})
            
            client.send_message("1234567890", "Test message")
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "Test message" in str(call_args)
    
    def test_whatsapp_send_interactive_list(self):
        """Test WhatsApp interactive list message"""
        from core.initializer.whatsapp import WhatsAppClient
        
        client = WhatsAppClient()
        
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": "Select Match"},
            "body": {"text": "Choose a match to analyze"},
            "action": {
                "button": "View Matches",
                "sections": [{
                    "title": "Upcoming",
                    "rows": [{"id": "match_1", "title": "Argentina vs Brazil"}]
                }]
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)
            
            client.send_interactive_message("1234567890", interactive_obj)
            
            mock_post.assert_called_once()
    
    def test_database_save_memory(self):
        """Test database.py save_memory for God View"""
        from core.initializer.database import Database
        
        db = Database()
        
        test_god_view = {
            "match": "Test vs Test",
            "final_xg": {"home": 2.0, "away": 1.0}
        }
        
        with patch.object(db.client.table('sessions'), 'upsert') as mock_upsert:
            mock_upsert.return_value.execute.return_value = Mock()
            
            db.save_memory("1234567890", test_god_view)
            
            mock_upsert.assert_called_once()
            call_args = mock_upsert.call_args[0][0]
            assert call_args['phone'] == "1234567890"
            assert call_args['god_view'] == test_god_view
    
    def test_database_load_memory(self):
        """Test database.py load_memory for God View retrieval"""
        from core.initializer.database import Database
        
        db = Database()
        
        mock_god_view = {"match": "Test vs Test"}
        
        with patch.object(db.client.table('sessions'), 'select') as mock_select:
            mock_chain = Mock()
            mock_chain.eq.return_value.execute.return_value.data = [{"god_view": mock_god_view}]
            mock_select.return_value = mock_chain
            
            result = db.load_memory("1234567890")
            
            assert result == mock_god_view


# ===================================================================
# TEST 2: AGENT SWARM (All 6 Agents)
# ===================================================================

class TestAgentSwarm:
    """Tests for all AI agents"""
    
    @pytest.mark.asyncio
    async def test_gatekeeper_intent_classification(self):
        """Test Gatekeeper routes BETTING intent"""
        from agents.gatekeeper.gatekeeper import GatekeeperAgent
        
        agent = GatekeeperAgent()
        
        with patch('core.initializer.llm.query_llm') as mock_llm:
            mock_llm.return_value = '{"intent": "BETTING", "confidence": 0.95}'
            
            result = await agent.classify_intent("Analyze Argentina vs Brazil")
            
            assert result['intent'] == 'BETTING'
            assert result['confidence'] > 0.9
    
    @pytest.mark.asyncio
    async def test_logistics_fatigue_calculation(self):
        """Test Logistics Agent calculates fatigue correctly"""
        from agents.logistics.logistics import LogisticsAgent
        
        agent = LogisticsAgent()
        
        with patch('core.initializer.llm.query_llm') as mock_llm:
            mock_llm.return_value = json.dumps({
                "fatigue_score": 7,
                "primary_risk": "Altitude",
                "stamina_impact": "Severe"
            })
            
            result = await agent.analyze(
                "MetLife Stadium, East Rutherford",
                "Estadio Azteca, Mexico City"
            )
            
            assert result['fatigue_score'] == 7
            assert result['distance_km'] > 2000  # Long distance
            assert 'altitude' in result['risk'].lower()
    
    @pytest.mark.asyncio
    async def test_tactics_xg_baseline(self):
        """Test Tactics Agent generates baseline xG"""
        from agents.tactics.tactics import TacticsAgent
        
        agent = TacticsAgent()
        
        with patch('agents.tactics.api.sportmonks.fetch_team_stats') as mock_stats:
            mock_stats.side_effect = [
                {"name": "Argentina", "xg_for_avg": 1.85, "xg_against_avg": 1.20, "style": "High Press"},
                {"name": "Brazil", "xg_for_avg": 1.50, "xg_against_avg": 1.35, "style": "Counter-Attack"}
            ]
            
            with patch('core.initializer.llm.query_llm') as mock_llm:
                mock_llm.return_value = json.dumps({
                    "xg_adjustment_a": 0.3,
                    "xg_adjustment_b": -0.15
                })
                
                result = await agent.analyze("Argentina", "Brazil")
                
                assert result['team_a_xg'] > 0
                assert result['team_b_xg'] > 0
                assert 'matchup_styles' in result
    
    @pytest.mark.asyncio
    async def test_market_odds_aggregation(self):
        """Test Market Agent finds best odds across books"""
        from agents.market.market import MarketAgent
        
        agent = MarketAgent()
        
        mock_odds = [{
            "home_team": "Argentina",
            "away_team": "Brazil",
            "bookmakers": [{
                "title": "DraftKings",
                "markets": [{
                    "key": "h2h",
                    "outcomes": [
                        {"name": "Argentina", "price": 1.85},
                        {"name": "Brazil", "price": 4.20},
                        {"name": "Draw", "price": 3.40}
                    ]
                }]
            }]
        }]
        
        with patch('core.initializer.llm.query_llm') as mock_llm:
            mock_llm.return_value = json.dumps({"value_score": "A-", "edge_percentage": 12.3})
            
            result = await agent.analyze("Argentina", "Brazil", odds_data=mock_odds)
            
            assert result['best_odds'] is not None
            assert result['market_math']['vig'] is not None
    
    @pytest.mark.asyncio
    async def test_narrative_sentiment_analysis(self):
        """Test Narrative Agent analyzes morale"""
        from agents.narrative.narrative import NarrativeAgent
        
        agent = NarrativeAgent()
        
        with patch('agents.narrative.api.google_news.fetch_headlines') as mock_news:
            mock_news.return_value = [
                {"title": "Messi returns to training", "link": "http://test.com"}
            ]
            
            with patch('agents.narrative.api.reddit_api.RedditScanner.scan_team_sentiment') as mock_reddit:
                mock_reddit.return_value = {"headlines": []}
                
                with patch('core.initializer.llm.query_llm') as mock_llm:
                    mock_llm.return_value = json.dumps({
                        "sentiment_score": 8.5,
                        "morale_impact": "Boost",
                        "narrative_adjustment": 0.15
                    })
                    
                    result = await agent.analyze("Argentina")
                    
                    assert result['score'] == 8.5
                    assert result['morale'] == 'Boost'
                    assert result['adjustment'] == 0.15
    
    def test_quant_dixon_coles_matrix(self):
        """Test Quant Engine Dixon-Coles probability calculation"""
        from agents.quant.quant import dixon_coles_matrix
        
        result = dixon_coles_matrix(lambda_a=2.3, lambda_b=0.8)
        
        # Basic probability validation
        assert result['a_win'] > 0
        assert result['draw'] > 0
        assert result['b_win'] > 0
        
        # Probabilities should sum to 1
        total = result['a_win'] + result['draw'] + result['b_win']
        assert 0.99 < total < 1.01  # Account for floating point
    
    def test_quant_kelly_criterion(self):
        """Test Quant Engine Kelly stake calculation"""
        from agents.quant.quant import run_quant_engine
        
        best_odds = {
            "home": {"price": 1.85, "book": "DraftKings"},
            "draw": {"price": 3.40, "book": "BetMGM"},
            "away": {"price": 4.20, "book": "FanDuel"}
        }
        
        result = run_quant_engine(
            adjusted_xg_a=2.3,
            adjusted_xg_b=0.8,
            best_odds=best_odds,
            user_budget=100,
            team_a_name="Argentina",
            team_b_name="Brazil"
        )
        
        assert 'probabilities' in result
        assert 'top_plays' in result
        
        # Check for value bets
        if result['top_plays']:
            bet = result['top_plays'][0]
            assert 'stake' in bet
            assert 'edge_percent' in bet
            assert bet['stake'] <= 100  # Never more than budget


# ===================================================================
# TEST 3: GOD VIEW SYSTEM
# ===================================================================

class TestGodViewSystem:
    """Tests for God View construction and usage"""
    
    def test_godview_builder_structure(self):
        """Test godview_builder.py creates correct JSON structure"""
        from data.scripts.godview_builder import build_god_view
        
        mock_logistics = {"branch": "logistics", "fatigue_score": 7}
        mock_tactics = {"branch": "tactics", "team_a_xg": 2.15}
        mock_market = {"branch": "market_sniper", "best_odds": {}}
        mock_narrative_home = {"team": "Argentina", "score": 8.5}
        mock_narrative_away = {"team": "Brazil", "score": 4.2}
        mock_quant = {"probabilities": {"team_a_win": 58.7}}
        
        god_view = build_god_view(
            home_team="Argentina",
            away_team="Brazil",
            match_key="argentina_vs_brazil",
            logistics_data=mock_logistics,
            tactics_data=mock_tactics,
            market_data=mock_market,
            narrative_home=mock_narrative_home,
            narrative_away=mock_narrative_away,
            quant_data=mock_quant,
            final_xg_home=2.30,
            final_xg_away=0.81,
            base_xg_home=2.15,
            base_xg_away=1.05,
            narrative_adj_home=0.15,
            narrative_adj_away=-0.10,
            logistics_penalty=0.85
        )
        
        # Validate structure
        assert god_view['match'] == "Argentina vs Brazil"
        assert 'timestamp' in god_view
        assert 'logistics' in god_view
        assert 'tactics' in god_view
        assert 'market' in god_view
        assert 'narrative' in god_view
        assert 'quant' in god_view
        assert 'final_xg' in god_view
        assert 'meta' in god_view
        
        # Validate metadata
        assert god_view['meta']['version'] == "2.0"
        assert 'xg_adjustment_chain' in god_view['meta']
    
    def test_godview_no_duplicates(self):
        """Test God View has no duplicate raw_analysis fields"""
        from data.scripts.godview_builder import build_god_view
        
        mock_narrative = {
            "team": "Test",
            "score": 5.0,
            "raw_analysis": {"should_not_appear": True}  # Should be filtered out
        }
        
        god_view = build_god_view(
            "Home", "Away", "key",
            {}, {}, {}, mock_narrative, mock_narrative,
            {}, 2.0, 1.0, 2.0, 1.0, 0, 0, 1.0
        )
        
        # raw_analysis should NOT be in output
        assert 'raw_analysis' not in god_view['narrative']['home']
        assert 'raw_analysis' not in god_view['narrative']['away']


# ===================================================================
# TEST 4: ORCHESTRATOR
# ===================================================================

class TestOrchestrator:
    """Tests for services/orchestrator.py"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_parallel_execution(self):
        """Test orchestrator runs agents in parallel"""
        from services import orchestrator
        
        match_info = {
            "home_team": "Argentina",
            "away_team": "Brazil",
            "venue": "Estadio Azteca, Mexico City",
            "venue_from": "MetLife Stadium, East Rutherford"
        }
        
        # Mock all agent outputs
        with patch('agents.logistics.logistics.LogisticsAgent.analyze', new_callable=AsyncMock) as mock_log, \
             patch('agents.tactics.tactics.TacticsAgent.analyze', new_callable=AsyncMock) as mock_tac, \
             patch('agents.market.market.MarketAgent.analyze', new_callable=AsyncMock) as mock_mkt, \
             patch('agents.narrative.narrative.NarrativeAgent.analyze', new_callable=AsyncMock) as mock_nar:
            
            mock_log.return_value = {"branch": "logistics", "fatigue_score": 7}
            mock_tac.return_value = {"branch": "tactics", "team_a_xg": 2.15, "team_b_xg": 1.05}
            mock_mkt.return_value = {"branch": "market_sniper", "best_odds": {}}
            mock_nar.return_value = {"branch": "narrative", "score": 8.5, "adjustment": 0.15}
            
            result = await orchestrator.generate_betting_briefing(match_info)
            
            # Verify all agents called
            mock_log.assert_called_once()
            mock_tac.assert_called_once()
            mock_mkt.assert_called_once()
            assert mock_nar.call_count == 2  # Called for home and away
            
            # Verify God View structure
            assert 'logistics' in result
            assert 'tactics' in result
            assert 'market' in result
            assert 'narrative' in result
            assert 'quant' in result
            assert 'final_xg' in result
    
    @pytest.mark.asyncio
    async def test_orchestrator_cache(self):
        """Test orchestrator caches God View for reuse"""
        from services import orchestrator
        
        match_info = {
            "home_team": "Argentina",
            "away_team": "Brazil",
            "venue": "Test",
            "venue_from": "Test"
        }
        
        # First call - should generate
        with patch('agents.logistics.logistics.LogisticsAgent.analyze', new_callable=AsyncMock) as mock:
            mock.return_value = {"branch": "logistics", "fatigue_score": 5}
            
            result1 = await orchestrator.generate_betting_briefing(match_info)
            first_call_count = mock.call_count
        
        # Second call - should use cache
        with patch('agents.logistics.logistics.LogisticsAgent.analyze', new_callable=AsyncMock) as mock:
            result2 = await orchestrator.generate_betting_briefing(match_info)
            second_call_count = mock.call_count
        
        # Cache should prevent second agent call
        assert first_call_count > 0
        assert second_call_count == 0  # Cached!


# ===================================================================
# TEST 5: BIG DADDY (core/generate_bets.py)
# ===================================================================

class TestBigDaddy:
    """Tests for the Big Daddy bet synthesizer"""
    
    @pytest.mark.asyncio
    async def test_big_daddy_bet_generation(self):
        """Test generate_bets.py synthesizes God View into bets"""
        from core.generate_bets import generate_bet_recommendations
        
        mock_god_view = {
            "match": "Argentina vs Brazil",
            "final_xg": {"home": 2.30, "away": 0.81},
            "logistics": {"fatigue_score": 7},
            "tactics": {"team_a_xg": 2.15},
            "market": {"best_odds": {"home": {"price": 1.85}}},
            "narrative": {"home": {"score": 8.5}, "away": {"score": 4.2}},
            "quant": {"top_plays": []}
        }
        
        with patch('core.initializer.database.Database.load_memory') as mock_load:
            mock_load.return_value = mock_god_view
            
            with patch('core.initializer.llm.query_llm') as mock_llm:
                mock_llm.return_value = """
                # BET 1
                💰 Argentina Win (@ 1.85)
                
                # BET 2  
                💰 Under 2.5 Goals
                
                # BET 3
                💰 Argentina -0.5 AH
                """
                
                result = await generate_bet_recommendations(num_bets=3, user_phone="1234567890")
                
                assert "Argentina Win" in result
                assert "# BET" in result
                mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_big_daddy_uses_correct_prompt(self):
        """Test Big Daddy uses BET_GENERATOR_PROMPT for standard mode"""
        from core.generate_bets import generate_bet_recommendations
        from prompts.system_prompts import BET_GENERATOR_PROMPT
        
        mock_god_view = {"match": "Test", "final_xg": {}, "quant": {"top_plays": []}}
        
        with patch('core.initializer.database.Database.load_memory', return_value=mock_god_view):
            with patch('core.initializer.llm.query_llm') as mock_llm:
                mock_llm.return_value = "Test bets"
                
                await generate_bet_recommendations(num_bets=3, user_phone="test")
                
                # Check that BET_GENERATOR_PROMPT was used
                call_args = mock_llm.call_args
                assert "GoalMine Intelligence Chief" in str(call_args)  # From the prompt
    
    @pytest.mark.asyncio
    async def test_big_daddy_conversational_mode(self):
        """Test Big Daddy handles follow-up questions"""
        from core.generate_bets import generate_strategic_advice
        
        mock_god_view = {"match": "Test", "quant": {"top_plays": []}}
        
        with patch('core.initializer.database.Database.load_memory', return_value=mock_god_view):
            with patch('core.initializer.llm.query_llm') as mock_llm:
                mock_llm.return_value = "Strategic advice response"
                
                result = await generate_strategic_advice(
                    user_phone="test",
                    question="What's the best parlay strategy?"
                )
                
                assert "Strategic advice" in result or len(result) > 0


# ===================================================================
# TEST 6: CONVERSATION FLOWS
# ===================================================================

class TestConversationFlows:
    """Tests for both button and conversational flows"""
    
    @pytest.mark.asyncio
    async def test_button_flow_schedule_display(self):
        """Test button flow shows schedule with interactive list"""
        from services.buttonConversationalFlow.button_conversation import ButtonConversationHandler
        from core.initializer.whatsapp import WhatsAppClient
        from core.initializer.database import Database
        
        wa = WhatsAppClient()
        db = Database()
        handler = ButtonConversationHandler(wa, db)
        
        with patch.object(wa, 'send_interactive_message') as mock_send:
            await handler._send_schedule_list("1234567890")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args['type'] == 'list'
            assert 'sections' in call_args['action']
    
    @pytest.mark.asyncio
    async def test_conversational_flow_context_retention(self):
        """Test conversational flow remembers match context"""
        from services.conversationalFlow.conversation import ConversationHandler
        from core.initializer.whatsapp import WhatsAppClient
        
        wa = WhatsAppClient()
        handler = ConversationHandler(wa)
        
        # Mock database to return context
        with patch('core.initializer.database.Database.load_memory') as mock_load:
            mock_load.return_value = {
                "match": {"home_team": "Argentina", "away_team": "Brazil"},
                "god_view": {"final_xg": {"home": 2.3}}
            }
            
            with patch('core.initializer.llm.query_llm') as mock_llm:
                mock_llm.return_value = '{"intent": "CONV"}'
                
                with patch.object(wa, 'send_message'):
                    await handler.handle_incoming_message("1234567890", "Tell me more about this match")
                    
                    # Should use existing context
                    mock_load.assert_called()


# ===================================================================
# TEST 7: CONFIGURATION SYSTEM
# ===================================================================

class TestConfiguration:
    """Tests for settings.json configuration"""
    
    def test_settings_load(self):
        """Test settings.json loads correctly"""
        from core.config import settings
        
        # Validate key sections exist
        assert settings.get('app.interaction_mode') in ['CONVERSATIONAL', 'BUTTON_STRICT']
        assert settings.get('llm.default_model') is not None
        assert settings.get('strategy.default_budget') > 0
    
    def test_agent_toggle_settings(self):
        """Test agent toggle configuration"""
        from core.config import settings
        
        # All agents should be configurable
        assert isinstance(settings.get('agents.logistics', True), bool)
        assert isinstance(settings.get('agents.tactics', True), bool)
        assert isinstance(settings.get('agents.market', True), bool)
        assert isinstance(settings.get('agents.narrative', True), bool)
        assert isinstance(settings.get('agents.quant', True), bool)
    
    def test_llm_agent_configs(self):
        """Test each agent has LLM config"""
        from core.config import settings
        
        agents = ['gatekeeper', 'logistics', 'tactics', 'market', 'narrative', 'closer']
        
        for agent in agents:
            config = settings.get(f'llm.{agent}')
            if config:  # May not exist in minimal config
                assert 'model' in config or settings.get('llm.default_model')


# ===================================================================
# TEST 8: DATA & UTILITIES
# ===================================================================

class TestDataUtilities:
    """Tests for data loading and utilities"""
    
    def test_schedule_load(self):
        """Test schedule.json loads match data"""
        from data.scripts.data import get_next_matches
        
        matches = get_next_matches()
        assert isinstance(matches, list)
        if matches:
            match = matches[0]
            assert 'home_team' in match or 'homeTeam' in match
    
    def test_venue_data_load(self):
        """Test venues.json loads stadium data"""
        from data.scripts.data import get_venue_info
        
        venue_name, venue_data = get_venue_info("Estadio Azteca, Mexico City")
        
        assert venue_data is not None
        assert 'lat' in venue_data
        assert 'lon' in venue_data
        assert 'elevation' in venue_data
    
    def test_bet_types_load(self):
        """Test bet_types.json loads market catalog"""
        from data.scripts.data import BET_TYPES
        
        assert isinstance(BET_TYPES, list)
        if BET_TYPES:
            bet_type = BET_TYPES[0]
            assert 'market' in bet_type or 'name' in bet_type


# ===================================================================
# RUN ALL TESTS
# ===================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
