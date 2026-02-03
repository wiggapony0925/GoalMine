import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from dotenv import load_dotenv
load_dotenv()
from services.buttonConversationalFlow.button_conversation import ButtonConversationHandler
from prompts.messages_prompts import ButtonResponses

class TestButtonConversationFlow(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.wa_mock = MagicMock()
        self.db_mock = MagicMock()
        self.handler = ButtonConversationHandler(self.wa_mock, self.db_mock)
        
    async def test_rejects_text(self):
        """Ensure random text triggers the main menu."""
        await self.handler.handle_incoming_message("12345", "Hello GoalMine")
        
        # Should send main menu interactive message
        self.wa_mock.send_interactive_message.assert_called_once()
        args = self.wa_mock.send_interactive_message.call_args[0]
        self.assertEqual(args[0], "12345")
        self.assertEqual(args[1]['type'], 'button')
        self.assertEqual(args[1]['header']['text'], ButtonResponses.MAIN_MENU['header'])

    @patch('services.orchestrator.get_future_matches')
    async def test_show_schedule(self, mock_get_matches):
        """Ensure specific payload triggers schedule list."""
        mock_get_matches.return_value = [
            {'team_home': 'USA', 'team_away': 'Mexico', 'date_iso': '2026-06-11T09:00:00', 'venue': 'SoFi'}
        ]
        
        await self.handler.handle_incoming_message("12345", "Show_Schedule")
        
        self.wa_mock.send_interactive_message.assert_called_once()
        args = self.wa_mock.send_interactive_message.call_args[0]
        # Should be a list type
        self.assertEqual(args[1]['type'], 'list')
        self.assertIn("USA", args[1]['action']['sections'][0]['rows'][0]['title'])

    @patch('services.orchestrator.find_match_by_home_team')
    @patch('services.orchestrator.generate_betting_briefing')
    @patch('services.orchestrator.format_the_closer_report')
    async def test_analyze_flow(self, mock_report, mock_briefing, mock_find):
        """Ensure analysis payload triggers the swarm."""
        mock_find.return_value = {
            'team_home': 'USA', 'team_away': 'Mexico', 'venue': 'SoFi Stadium, Los Angeles'
        }
        mock_briefing.return_value = {}
        mock_report.return_value = "Analysis Report # BET 1"
        
        # Mock context manager for venue reading
        with patch("builtins.open", unittest.mock.mock_open(read_data='{"SoFi Stadium, Los Angeles": {"lat": 34, "lon": -118, "tz_offset": -7}}')):
            await self.handler.handle_incoming_message("12345", "Analyze USA")
            
        # 1. Typing indicators
        self.assertTrue(self.wa_mock.send_typing_indicator.called)
        
        # 2. Text report
        self.wa_mock.send_message.assert_any_call("12345", "Analysis Report")
        
        # 3. Location Pin
        self.wa_mock.send_location_message.assert_called_with(
            "12345", 34, -118, name='SoFi Stadium, Los Angeles', address="Official World Cup 2026 Venue • -7 UTC"
        )
        
        # 4. Main Menu Resent
        # We need to check if send_interactive_message was called at the end
        self.assertTrue(self.wa_mock.send_interactive_message.called)

if __name__ == '__main__':
    unittest.main()
