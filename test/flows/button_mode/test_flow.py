# ruff: noqa: E402
import unittest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

load_dotenv()
from services import GoalMineHandler
from prompts.messages_prompts import ButtonResponses


class TestButtonConversationFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.wa_mock = MagicMock()
        self.db_mock = MagicMock()
        # Mock session info to avoid TypeError with age check
        self.db_mock.get_session_info.return_value = {"age_minutes": 10}
        self.db_mock.load_button_state.return_value = None
        
        self.handler = GoalMineHandler(self.wa_mock, self.db_mock)

    @patch("agents.gatekeeper.gatekeeper.Gatekeeper.classify_intent")
    @patch("core.initializer.llm.query_llm")
    async def test_rejects_text(self, mock_query, mock_classify):
        """Ensure random text triggers the rejection message and main menu."""
        mock_classify.return_value = ("CONV", {})
        mock_query.return_value = "Hello! Use buttons please."
        
        await self.handler.handle_incoming_message("12345", "Hello GoalMine")

        # 1. Should send rejection message (either via _handle_general_conversation or fallback)
        self.wa_mock.send_message.assert_called()
        
        # 2. Should send main menu interactive message
        self.wa_mock.send_interactive_message.assert_called()
        args = self.wa_mock.send_interactive_message.call_args[0]
        self.assertEqual(args[0], "12345")
        self.assertEqual(args[1]["type"], "button")

    @patch("services.orchestrator.get_active_schedule")
    async def test_show_schedule(self, mock_get_active_schedule):
        """Ensure specific payload triggers schedule browser."""
        await self.handler.handle_incoming_message("12345", "Show_Schedule")

        self.wa_mock.send_interactive_message.assert_called_once()
        args = self.wa_mock.send_interactive_message.call_args[0]
        self.assertEqual(args[1]["type"], "list")

    @patch("services.orchestrator.find_match_by_home_team")
    @patch("services.orchestrator.generate_betting_briefing")
    @patch("services.orchestrator.format_the_closer_report")
    async def test_analyze_flow(self, mock_report, mock_briefing, mock_find):
        """Ensure analysis payload triggers the swarm."""
        mock_find.return_value = {
            "team_home": "USA",
            "team_away": "Mexico",
            "venue": "SoFi Stadium, Los Angeles",
        }
        mock_briefing.return_value = {}
        mock_report.return_value = "Analysis Report # BET 1"

        # Mock context manager for venue reading
        with patch(
            "builtins.open",
            unittest.mock.mock_open(
                read_data='{"SoFi Stadium, Los Angeles": {"lat": 34, "lon": -118, "tz_offset": -7}}'
            ),
        ):
            await self.handler.handle_incoming_message("12345", "Analyze USA")

        # 1. Typing indicators
        self.assertTrue(self.wa_mock.send_typing_indicator.called)

        # 2. Text report
        self.wa_mock.send_message.assert_any_call("12345", "Analysis Report")

        # 3. Location Pin
        self.wa_mock.send_location_message.assert_called_with(
            "12345",
            34,
            -118,
            name="SoFi Stadium, Los Angeles",
            address="Official World Cup 2026 Venue • -7 UTC",
        )

        # 4. Main Menu Resent
        # We need to check if send_interactive_message was called at the end
        self.assertTrue(self.wa_mock.send_interactive_message.called)


if __name__ == "__main__":
    unittest.main()
