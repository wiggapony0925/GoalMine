# ruff: noqa: E402
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Only show errors from agents
logger = logging.getLogger("UserJourneyTest")

from services import GoalMineHandler


class MockWhatsAppClient:
    def __init__(self):
        self.sent_messages = []

    def send_message(self, to, message):
        self.sent_messages.append(message)
        print(f"\n[GOALMINE AI 🤖]:\n{message}\n{'-' * 40}")


async def simulate_conversation(phone_number, scripts):
    """
    Simulates a sequence of user messages and prints the interaction.
    """
    mock_wa = MockWhatsAppClient()
    handler = GoalMineHandler(mock_wa)

    # Clear memory for fresh start
    handler.db.clear_memory(phone_number)

    print(f"\n{'=' * 20} STARTING CONVERSATION {phone_number} {'=' * 20}")

    for user_msg in scripts:
        print(f"\n[USER 👤]: {user_msg}")
        await handler.handle_incoming_message(phone_number, user_msg)
        # Small delay to mimic realism
        await asyncio.sleep(0.3)

    print(f"\n{'=' * 20} END OF CONVERSATION {'=' * 20}")


async def main():
    """Run all scenarios."""
    print("Running Scenario 1...")
    await run_journey_1()

    print("\nRunning Scenario 2...")
    await run_journey_2()

    print("\nRunning Scenario 3...")
    await run_journey_3()


async def run_journey_1():
    """Scenario 1: Greeting -> Match Analysis -> Follow-up tactical question."""
    script = [
        "Hey, who are you?",
        "Cool. When does Mexico play?",
        "Can you analyze the Mexico vs South Africa game for me?",
        "What's their fatigue risk exactly?",
        "Should I parlay a Mexico win with the draw?",
    ]
    await simulate_conversation("+1234567890", script)


async def run_journey_2():
    """Scenario 2: Direct analysis request with budget -> Confirmation -> Strategy."""
    script = [
        "Analyze Brazil vs Morocco with a $250 budget",
        "Yes, do it",
        "How should I split my money on this?",
    ]
    await simulate_conversation("+0987654321", script)


async def run_journey_3():
    """Scenario 3: Vague request -> Confirmation -> Pivot question."""
    script = [
        "Analyze",
        "Sure, go ahead",
        "Wait, what happened to the Brazil game?",
        "Okay, tell me about the xG for this Mexico match instead",
    ]
    await simulate_conversation("+1122334455", script)


if __name__ == "__main__":
    import sys

    # Set PYTHONPATH
    sys.path.append(os.getcwd())

    asyncio.run(main())
