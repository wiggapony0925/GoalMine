import random

class Responses:
    """
    Central repository for premium, randomized bot strings.
    """
    
    SYSTEM_GREETINGS = [
        "🤖 GoalMine AI Online. Targeting alpha in World Cup 2026.",
        "📊 System Ready. Swarm intel activated for match analysis.",
        "🕵️ GoalMine Analyst 01 reporting. Feed me a match, I'll find the edge."
    ]

    MATCH_READING = [
        "🤖 Reading match details...",
        "🔍 Parsing fixture data...",
        "⚖️ Extracting match context..."
    ]

    LAUNCHING_SWARM = [
        "🕵️ Identified: {match}. Launching Swarm...",
        "🚀 Fixture Confirmed: {match}. Deploying agents...",
        "📡 Syncing: {match}. Synchronizing Logistics, Tactics, Market, and Narrative..."
    ]

    @staticmethod
    def get_greeting():
        return random.choice(Responses.SYSTEM_GREETINGS)

    @staticmethod
    def get_reading():
        return random.choice(Responses.MATCH_READING)

    @staticmethod
    def get_launch(match):
        return random.choice(Responses.LAUNCHING_SWARM).format(match=match)

    NO_MATCHES_TODAY = "⛔ No World Cup matches today.\n\nTry 'Analyze France vs Brazil' or ask about an upcoming clash."
    UNKNOWN_TEAMS = "❓ I couldn't identify the teams. Please specify them clearly (e.g., 'Analyze USA vs Mexico')."
    INVALID_SCHEDULE = "⚠️ Match not found in World Cup 2026 Schedule.\nI only track official tournament fixtures."
