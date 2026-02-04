"""
END-TO-END INTEGRATION TESTS
Tests the complete user journey following the app flow documented in README.md

Flow: User → Webhook → Gatekeeper → Agents → God View → Big Daddy → Response
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

# ===================================================================
# INTEGRATION TEST 1: Complete Betting Analysis Flow
# ===================================================================


class TestCompleteAnalysisFlow:
    """Test full user journey from WhatsApp message to bet recommendations"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_requests_bet_analysis_complete_flow(self):
        """
        COMPLETE FLOW TEST:
        User: "Analyze Argentina vs Brazil"
        Expected: Get 3 betting recommendations with full intelligence citation
        """
        from app import app
        from unittest.mock import patch

        # Mock incoming WhatsApp webhook payload
        webhook_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Analyze Argentina vs Brazil"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        with app.test_client() as client:
            # Mock all external dependencies
            with (
                patch("core.initializer.llm.query_llm") as mock_llm,
                patch(
                    "core.initializer.whatsapp.WhatsAppClient.send_message"
                ) as mock_send,
                patch("core.initializer.database.Database.save_memory") as mock_save,
                patch("core.initializer.database.Database.load_memory") as mock_load,
                patch("agents.logistics.api.open_meteo.fetch_weather_data"),
                patch("agents.tactics.api.sportmonks.fetch_team_stats") as mock_stats,
                patch("agents.market.api.the_odds_api.fetch_latest_odds") as mock_odds,
                patch("agents.narrative.api.google_news.fetch_headlines") as mock_news,
            ):
                # Setup mock responses for each component

                # Gatekeeper: Routes to BETTING
                # Logistics: Returns fatigue
                # Tactics: Returns xG
                # Market: Returns odds
                # Narrative: Returns sentiment
                # Big Daddy: Returns bets
                llm_responses = [
                    '{"intent": "BETTING", "confidence": 0.95}',  # Gatekeeper
                    json.dumps(
                        {"fatigue_score": 7, "primary_risk": "Altitude"}
                    ),  # Logistics
                    json.dumps(
                        {"xg_adjustment_a": 0.3, "xg_adjustment_b": -0.15}
                    ),  # Tactics
                    json.dumps(
                        {"value_score": "A-", "edge_percentage": 12.3}
                    ),  # Market
                    json.dumps(
                        {
                            "sentiment_score": 8.5,
                            "morale_impact": "Boost",
                            "narrative_adjustment": 0.15,
                        }
                    ),  # Narrative Home
                    json.dumps(
                        {
                            "sentiment_score": 4.2,
                            "morale_impact": "Drop",
                            "narrative_adjustment": -0.10,
                        }
                    ),  # Narrative Away
                    """# BET 1
💰 Argentina Win (@ 1.85)
📊 Intelligence:
• Tactics: xG 2.30 vs 0.81
• Market: 14% edge
• Logistics: Opponent fatigued
• Narrative: Home morale 8.5/10""",  # Big Daddy
                ]

                mock_llm.side_effect = llm_responses

                mock_stats.side_effect = [
                    {"name": "Argentina", "xg_for_avg": 1.85, "style": "High Press"},
                    {"name": "Brazil", "xg_for_avg": 1.50, "style": "Counter-Attack"},
                ]

                mock_odds.return_value = [
                    {
                        "home_team": "Argentina",
                        "away_team": "Brazil",
                        "bookmakers": [
                            {
                                "title": "DraftKings",
                                "markets": [
                                    {
                                        "key": "h2h",
                                        "outcomes": [
                                            {"name": "Argentina", "price": 1.85},
                                            {"name": "Brazil", "price": 4.20},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]

                mock_news.return_value = [
                    {"title": "Test news", "link": "http://test.com"}
                ]
                mock_load.return_value = {}

                # Make webhook request
                response = client.post(
                    "/webhook",
                    data=json.dumps(webhook_payload),
                    content_type="application/json",
                )

                # Give async tasks time to complete
                await asyncio.sleep(2)

                # Assertions
                assert response.status_code == 200

                # Verify God View was saved
                assert mock_save.call_count > 0

                # Verify betting recommendations were sent
                assert mock_send.call_count > 0
                sent_message = str(mock_send.call_args)
                assert "BET" in sent_message or "Argentina" in sent_message

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_button_flow_match_selection(self):
        """
        BUTTON FLOW TEST:
        User clicks "Show Schedule" → Selects match → Gets analysis
        """
        from services import GoalMineHandler
        from core.initializer.whatsapp import WhatsAppClient
        from core.initializer.database import Database

        wa = WhatsAppClient()
        db = Database()
        handler = GoalMineHandler(wa, db)

        with patch.object(wa, "send_interactive_message") as mock_send_interactive:
            # Step 1: User clicks "Show Schedule"
            await handler.handle_incoming_message(
                from_number="1234567890", msg_body="Show Schedule"
            )

            # Verify interactive list was sent
            assert mock_send_interactive.call_count > 0
            last_call = mock_send_interactive.call_args[0][1]
            assert last_call["type"] == "list"

        with (
            patch.object(wa, "send_message"),
            patch(
                "services.orchestrator.generate_betting_briefing",
                new_callable=AsyncMock,
            ) as mock_orchestrator,
            patch(
                "core.generate_bets.generate_bet_recommendations",
                new_callable=AsyncMock,
            ) as mock_bets,
        ):
            mock_orchestrator.return_value = {
                "match": "Argentina vs Brazil",
                "final_xg": {"home": 2.3, "away": 0.8},
                "quant": {"top_plays": []},
            }

            mock_bets.return_value = "BET 1: Argentina Win"

            # Step 2: User selects match from list
            message_obj = {
                "interactive": {
                    "type": "list_reply",
                    "list_reply": {"id": "analyze_argentina_vs_brazil"},
                }
            }

            await handler.handle_incoming_message(
                from_number="1234567890", msg_body="", message_obj=message_obj
            )

            # Verify orchestrator was called
            assert mock_orchestrator.call_count > 0

            # Verify bets were generated and sent
            assert mock_bets.call_count > 0


# ===================================================================
# INTEGRATION TEST 2: Multi-Agent Parallel Execution
# ===================================================================


class TestMultiAgentExecution:
    """Test that all agents execute successfully in parallel"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_agents_contribute_to_god_view(self):
        """
        Verify EVERY agent contributes data to God View:
        - Logistics
        - Tactics
        - Market
        - Narrative (x2)
        - Quant
        """
        from services.orchestrator import generate_betting_briefing

        match_info = {
            "home_team": "Argentina",
            "away_team": "Brazil",
            "venue": "Estadio Azteca, Mexico City",
            "venue_from": "MetLife Stadium, East Rutherford",
        }

        with patch("core.initializer.llm.query_llm") as mock_llm:
            # Mock responses for each agent
            mock_llm.side_effect = [
                json.dumps({"fatigue_score": 7}),  # Logistics
                json.dumps({"xg_adjustment_a": 0.3}),  # Tactics
                json.dumps({"value_score": "A-"}),  # Market
                json.dumps({"sentiment_score": 8.5}),  # Narrative Home
                json.dumps({"sentiment_score": 4.2}),  # Narrative Away
            ]

            with patch("agents.tactics.api.sportmonks.fetch_team_stats") as mock_stats:
                mock_stats.side_effect = [
                    {"name": "Argentina", "xg_for_avg": 1.85},
                    {"name": "Brazil", "xg_for_avg": 1.50},
                ]

                with patch(
                    "agents.market.api.the_odds_api.fetch_latest_odds"
                ) as mock_odds:
                    mock_odds.return_value = []

                    with patch(
                        "agents.narrative.api.google_news.fetch_headlines"
                    ) as mock_news:
                        mock_news.return_value = []

                        god_view = await generate_betting_briefing(match_info)

                        # Verify ALL components present
                        assert "match" in god_view
                        assert "logistics" in god_view
                        assert "tactics" in god_view
                        assert "market" in god_view
                        assert "narrative" in god_view
                        assert "quant" in god_view
                        assert "final_xg" in god_view
                        assert "meta" in god_view

                        # Verify metadata
                        assert god_view["meta"]["version"] == "2.0"
                        assert "agents_executed" in god_view["meta"]

                        # Verify xG adjustment chain
                        assert "xg_adjustment_chain" in god_view["meta"]
                        chain = god_view["meta"]["xg_adjustment_chain"]
                        assert "base_tactics" in chain
                        assert "narrative_adj" in chain
                        assert "logistics_penalty" in chain
                        assert "final" in chain

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parallel_execution_speed(self):
        """Verify agents run in parallel (fast) not sequential (slow)"""
        import time
        from services.orchestrator import generate_betting_briefing

        match_info = {
            "home_team": "Test A",
            "away_team": "Test B",
            "venue": "Test",
            "venue_from": "Test",
        }

        async def slow_agent_mock(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate 100ms per agent
            return {"branch": "test", "data": "test"}

        with (
            patch(
                "agents.logistics.logistics.LogisticsAgent.analyze",
                side_effect=slow_agent_mock,
            ),
            patch(
                "agents.tactics.tactics.TacticsAgent.analyze",
                side_effect=slow_agent_mock,
            ),
            patch(
                "agents.market.market.MarketAgent.analyze", side_effect=slow_agent_mock
            ),
            patch(
                "agents.narrative.narrative.NarrativeAgent.analyze",
                side_effect=slow_agent_mock,
            ),
        ):
            start = time.time()
            await generate_betting_briefing(match_info)
            elapsed = time.time() - start

            # If sequential: 5 agents × 0.1s = 0.5s+
            # If parallel: max(0.1s) ≈ 0.1-0.2s
            assert elapsed < 0.35  # Should be fast due to parallelization


# ===================================================================
# INTEGRATION TEST 3: Database Persistence & Follow-ups
# ===================================================================


class TestDatabasePersistence:
    """Test God View persistence enables follow-up questions"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_god_view_persisted_for_followups(self):
        """
        Test that God View is saved to DB and retrieved for follow-up Q&A
        """
        from core.initializer.database import Database
        from core.generate_bets import generate_strategic_advice

        db = Database()
        test_phone = "test_user_123"

        # Simulate God View being saved after analysis
        mock_god_view = {
            "match": "Argentina vs Brazil",
            "final_xg": {"home": 2.3, "away": 0.8},
            "logistics": {"fatigue_score": 7},
            "tactics": {"team_a_xg": 2.15},
            "market": {"best_odds": {"home": {"price": 1.85}}},
            "narrative": {"home": {"score": 8.5}, "away": {"score": 4.2}},
            "quant": {"top_plays": [{"market": "Argentina Win", "edge_percent": 14.0}]},
        }

        with patch.object(db.client.table("sessions"), "upsert") as mock_upsert:
            mock_upsert.return_value.execute.return_value = Mock()

            # Save God View
            db.save_memory(test_phone, mock_god_view)

            # Verify save was called
            assert mock_upsert.call_count > 0

        # Now test follow-up question retrieves God View
        with patch.object(db.client.table("sessions"), "select") as mock_select:
            mock_chain = Mock()
            mock_chain.eq.return_value.execute.return_value.data = [
                {"god_view": mock_god_view}
            ]
            mock_select.return_value = mock_chain

            with patch("core.initializer.llm.query_llm") as mock_llm:
                mock_llm.return_value = "Strategic advice based on God View"

                # User asks follow-up
                await generate_strategic_advice(
                    user_phone=test_phone, question="What's the best parlay strategy?"
                )

                # Verify God View was loaded
                mock_select.assert_called_once()

                # Verify LLM received God View data
                llm_call_args = str(mock_llm.call_args)
                assert "Argentina" in llm_call_args or "Brazil" in llm_call_args


# ===================================================================
# INTEGRATION TEST 4: Error Handling & Graceful Degradation
# ===================================================================


class TestErrorHandling:
    """Test system handles failures gracefully"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_single_agent_failure_doesnt_crash_system(self):
        """If one agent fails, others should continue"""
        from services.orchestrator import generate_betting_briefing

        match_info = {
            "home_team": "Test",
            "away_team": "Test",
            "venue": "Test",
            "venue_from": "Test",
        }

        # Make Logistics fail, but others succeed
        with patch("agents.logistics.logistics.LogisticsAgent.analyze") as mock_log:
            mock_log.side_effect = Exception("API Error")

            with patch(
                "agents.tactics.tactics.TacticsAgent.analyze", new_callable=AsyncMock
            ) as mock_tac:
                mock_tac.return_value = {
                    "branch": "tactics",
                    "team_a_xg": 2.0,
                    "team_b_xg": 1.0,
                }

                with patch(
                    "agents.market.market.MarketAgent.analyze", new_callable=AsyncMock
                ) as mock_mkt:
                    mock_mkt.return_value = {"branch": "market_sniper", "best_odds": {}}

                    with patch(
                        "agents.narrative.narrative.NarrativeAgent.analyze",
                        new_callable=AsyncMock,
                    ) as mock_nar:
                        mock_nar.return_value = {
                            "branch": "narrative",
                            "score": 5.0,
                            "adjustment": 0,
                        }

                        # Should NOT crash
                        god_view = await generate_betting_briefing(match_info)

                        # Logistics should have fallback data
                        assert (
                            god_view["logistics"]["fatigue_score"] == 5
                        )  # Default fallback
                        assert god_view["logistics"]["status"] == "FALLBACK"

                        # Other agents should have succeeded
                        assert god_view["tactics"]["team_a_xg"] == 2.0
                        assert god_view["meta"]["agents_executed"]["tactics"] == "OK"


# ===================================================================
# INTEGRATION TEST 5: WhatsApp Interactive Messages
# ===================================================================


class TestWhatsAppIntegration:
    """Test WhatsApp API integrations"""

    def test_interactive_list_message_format(self):
        """Test interactive list follows WhatsApp Cloud API format"""
        from core.initializer.whatsapp import WhatsAppClient

        wa = WhatsAppClient()

        test_list = {
            "type": "list",
            "header": {"type": "text", "text": "Select Match"},
            "body": {"text": "Choose a match"},
            "action": {
                "button": "View Matches",
                "sections": [
                    {
                        "title": "Upcoming",
                        "rows": [
                            {
                                "id": "match_1",
                                "title": "Argentina vs Brazil",
                                "description": "June 15",
                            }
                        ],
                    }
                ],
            },
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value = Mock(status_code=200)

            wa.send_interactive_message("1234567890", test_list)

            # Verify API call structure
            call_data = json.loads(mock_post.call_args[1]["data"])
            assert call_data["messaging_product"] == "whatsapp"
            assert call_data["type"] == "interactive"
            assert "interactive" in call_data


# ===================================================================
# RUN INTEGRATION TESTS
# ===================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration", "--tb=short"])
