# ruff: noqa: E402
"""
GoalMine Comprehensive Integration Test Suite
Tests full conversation flows, agent orchestration, and strategic logic.
"""

import asyncio
import sys
import os
import logging

from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging to console for visibility during test
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from services import GoalMineHandler
from core.initializer.whatsapp import WhatsAppClient
# from prompts.system_prompts import * # Directory was deleted by user


# Mock WhatsApp to capture messages instead of sending them
class MockWhatsApp(WhatsAppClient):
    def __init__(self):
        self.token = "mock_token"
        self.phone_number_id = "mock_id"
        self.sent_messages = []

    def send_message(self, to, body):
        self.sent_messages.append({"to": to, "body": body})
        print(f"\n[TO: {to}] 📱 WHATSAPP OUTGOING:\n{body}\n{'-' * 40}")
        return {"status": "sent"}


# Mock DB to use in-memory context for tests
class MockDB:
    def __init__(self):
        self.memory = {}

    def save_memory(self, phone, data):
        self.memory[phone] = data

    def load_memory(self, phone):
        return self.memory.get(phone)

    def save_chat_context(self, phone, context):
        pass

    def load_chat_context(self, phone):
        return []


async def run_scenario(handler, phone, message, description):
    print(f"\n🚀 SCENARIO: {description}")
    print(f"User > {message}")
    await handler.handle_incoming_message(phone, message)


async def test_full_suite():
    print("\n" + "🏆" * 25)
    print("   GOALMINE INTEGRATION TEST SUITE")
    print("🏆" * 25)

    from unittest.mock import patch

    with patch("services.conversation.Database", return_value=MockDB()):
        wa = MockWhatsApp()
        handler = GoalMineHandler(wa_client=wa)
        db = handler.db

        test_phone = "123456789"

    # --- SCENARIO 1: GREETING ---
    await run_scenario(handler, test_phone, "Hello!", "Initial Greeting")

    # --- SCENARIO 2: ANALYZE COMMAND (Natural Language) ---
    await run_scenario(
        handler,
        test_phone,
        "Analyze Mexico vs South Africa",
        "Natural Analysis Request",
    )

    # --- SCENARIO 3: CONFIRMATION FLOW (If triggered) ---
    # In case the bot asks "Did you mean Mexico vs South Africa?", we simulate "Yes"
    if wa.sent_messages and "confirm" in wa.sent_messages[-1]["body"].lower():
        await run_scenario(handler, test_phone, "Yes do it", "Confirmation of Match")

    # --- SCENARIO 4: BUDGET FOLLOW-UP ---
    # Now that analysis exists, ask about a specific budget
    await run_scenario(
        handler,
        test_phone,
        "I have 50 dollars what should I get on",
        "Budget Follow-up (Should use Strategic Advisor)",
    )

    # --- SCENARIO 5: PARLAY STRATEGY ---
    await run_scenario(
        handler,
        test_phone,
        "Should I parlay the draw with Mexico win?",
        "Strategy Query (Parlay)",
    )

    # --- SCENARIO 6: NEW MATCH (Reset Context) ---
    await run_scenario(
        handler,
        test_phone,
        "What about England vs Germany?",
        "New Match Request (Should detect new teams)",
    )

    # --- SCENARIO 7: SCHEDULE QUERY ---
    await run_scenario(handler, test_phone, "When is the next game?", "Schedule Query")

    # --- SCENARIO 8: OOS / OFF-TOPIC ---
    await run_scenario(
        handler,
        test_phone,
        "How do I make sushi?",
        "Off-topic Query (Gatekeeper Check)",
    )

    # --- SCENARIO 9: HIGH BUDGET ANALYSIS ---
    await run_scenario(
        handler,
        test_phone,
        "Analyze Mexico vs South Africa with $1000 budget and 5 bets",
        "High-Budget Specific Command",
    )

    # --- SCENARIO 10: PARTIAL NAMES ---
    await run_scenario(handler, test_phone, "Mex vs S. Afr", "Partial Team Names")

    # --- SCENARIO 11: EXTREME BUDGET ---
    await run_scenario(
        handler, test_phone, "Analyze with $0 budget", "Zero Budget Check"
    )

    # --- SCENARIO 12: BUDGET ONLY FOLLOW-UP ---
    await run_scenario(
        handler, test_phone, "$250 please", "Budget-only message after match analysis"
    )

    # --- SCENARIO 13: INVALID TEAM ---
    await run_scenario(
        handler, test_phone, "Analyze Mars vs Jupiter", "Invalid Team Scenario"
    )

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print("Total Scenarios Run: 9")
    print(f"Messages Sent: {len(wa.sent_messages)}")

    # Verify memory persistence
    mem = db.load_memory(test_phone)
    if mem:
        print("\n✅ Final State Check:")
        print(f"Last Match in Memory: {mem.get('match')}")
        print(f"Analysis Present: {'Yes' if 'god_view' in mem else 'No'}")
    else:
        print("\n❌ Memory was not persisted.")

    print("\n" + "=" * 60)
    print("✅ COMPREHENSIVE TEST COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_full_suite())
