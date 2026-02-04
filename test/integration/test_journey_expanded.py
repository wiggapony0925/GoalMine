# ruff: noqa: E402
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Ensure root path is in sys.path before local imports
sys.path.append(os.getcwd())

# Load env variables
load_dotenv()

from core.log import setup_logging
from services import GoalMineHandler  # noqa: E402

# Initialize centralized logging
setup_logging()
logger = logging.getLogger("UserJourneyTest")


class MockWhatsAppClient:
    def __init__(self):
        self.sent_messages = []

    def send_message(self, to, message):
        self.sent_messages.append(message)
        # We wrap in a nice frame to see the "WhatsApp" feel
        print(f"\n[GOALMINE AI 🤖]:\n{message}")
        print("-" * 50)


async def simulate_conversation(phone_number, scripts, delay=0.5):
    """
    Simulates a sequence of user messages and prints the interaction.
    """
    mock_wa = MockWhatsAppClient()
    handler = GoalMineHandler(mock_wa)

    # Clear memory for fresh start
    try:
        handler.db.clear_memory(phone_number)
    except Exception:
        pass  # Handle if local db etc.

    print(f"\n{'#' * 30} STARTING JOURNEY: {phone_number} {'#' * 30}")

    for user_msg in scripts:
        print(f"\n[USER 👤]: {user_msg}")
        await handler.handle_incoming_message(phone_number, user_msg)
        # Small delay to mimic realism and let API calls finish
        await asyncio.sleep(delay)

    print(f"\n{'#' * 30} END OF JOURNEY {'#' * 30}")


async def run_journey_1():
    """Scenario 1: High-IQ Betting Strategy (The Sharp)."""
    script = [
        "Yo, who am I talking to?",
        "I'm looking at the Mexico vs South Africa game. Give me the tactical breakdown.",
        "You say the xG is close, but what about the altitude variable?",
        "If I have $1,000, how much should I put on the Draw if I want to play it safe?",
        "Actually, what if I parlay that with a Morocco win against Brazil?",
        "Wait, why is that mutually exclusive? Oh wait, I see. You're right. Just the Draw then.",
    ]
    await simulate_conversation("+SHARP_USER_01", script)


async def run_journey_2():
    """Scenario 2: Off-Topic Redirection (The McDonald's Test)."""
    script = [
        "Hey! Do you know where the nearest McDonald's is in Mexico City?",
        "I'm hungry man, just tell me. Can I buy a Big Mac with my winnings?",
        "Fine, fine. Since I'm in Mexico City anyway for the opener, who's playing?",
        "Is there any travel fatigue for the away team there?",
        "Okay, analyze that game for me. Maximize my value.",
    ]
    await simulate_conversation("+HUNGRY_USER_02", script)


async def run_journey_3():
    """Scenario 3: The Newbie / Tournament Structure."""
    script = [
        "Hello! I'm new to this. What is GoalMine?",
        "Wow, 2026? How many teams are in the World Cup this time?",
        "That's a lot of games. When's the first one?",
        "I want to bet $10 on my favorite team even if they lose. Is that a bad idea?",
        "Tell me about the mood in the Mexico camp right now. Any drama?",
    ]
    await simulate_conversation("+NEWBIE_USER_03", script)


async def run_journey_4():
    """Scenario 4: The Skeptic / Model Logic Deep Dive."""
    script = [
        "Your model says the Draw is a value lock. Why?",
        "But the market has it at 4.2. Doesn't that mean something is wrong with your xG calculation?",
        "Explain the Dixon-Coles adjustment to me like I'm five.",
        "Is the Narrative agent actually seeing the Reddit rumors about the manager?",
        "Okay, I'll trust the math. Run the analysis for me with a $500 budget.",
    ]
    await simulate_conversation("+SKEPTIC_USER_04", script)


async def run_journey_5():
    """Scenario 5: Multi-Match Pivot (The Heavy Overlord)."""
    script = [
        "Analyze!",  # Vague start
        "Sure, go ahead with the Mexico game.",
        "Actually, stop. Tell me about Brazil vs Morocco instead.",
        "Wait, what happened to my Mexico analysis? Can I see both?",
        "If I parlay both favorites, what's my edge?",
        "How do I split $2,000 across these two games for maximum survival?",
    ]
    await simulate_conversation("+OVERLORD_USER_05", script)


async def run_journey_6():
    """Scenario 6: Support & Capabilities."""
    script = [
        "What's your model's historical ROI?",
        "Can you help me with a parlay across 5 games?",
        "What if I lose all my money?",
        "Alright, you're cool. What's the best bet right now for the next 4 hours?",
        "Thanks GoalMine. You're the best.",
    ]
    await simulate_conversation("+SUPPORT_USER_06", script)


async def main():
    """Run the hundred-line conversation endurance test."""
    print("\n🚀 STARTING THE GOALMINE CONVERSATION ENDURANCE TEST 🚀")
    print("Testing for Persona, Redirection, Arithmetic, and Context Memory.\n")

    tasks = [
        run_journey_1(),
        run_journey_2(),
        run_journey_3(),
        run_journey_4(),
        run_journey_5(),
        run_journey_6(),
    ]

    # We run them sequentially to make the console output readable for the user
    for task in tasks:
        await task

    print("\n✅ ENDURANCE TEST COMPLETE ✅")


if __name__ == "__main__":
    asyncio.run(main())
