import random

class Responses:
    """
    Central repository for premium, conversational bot strings.
    """
    
    GREETING = (
        "🤖 *Welcome to GoalMine AI* — Your elite World Cup 2026 **Money-Making Machine**.\n\n"
        "I am a multi-agent swarm engineered for one purpose: **Alpha**. I bypass public narratives to find mathematical edges in the market.\n\n"
        "📍 *Operational Capabilities:*\n"
        "• *Deep-Swarm Analysis:* Say 'Analyze [Teams]' for a full tactical & market breakdown.\n"
        "• *Strategic Parlays:* Ask 'Parlay this with [Team]' to find compounded value.\n"
        "• *Budget Allocation:* Ask 'How should I spend $200 today?' for a Kelly-based plan.\n\n"
        "📜 *The Rules:*\n"
        "1. I only track official World Cup 2026 fixtures.\n"
        "2. I strictly discuss Football and Betting ROI.\n"
        "3. Every morning at *5:00 AM*, I drop a 'Sharp' briefing into your inbox.\n\n"
        "How can I help you extract value from the pitch today?"
    )

    MATCH_READING = [
        "🔍 One moment, I'm pulling the latest data for this fixture...",
        "⚖️ Accessing the vault. Reading match context and market odds...",
        "🤖 Just a second, GoalMine Analyst 01 is parsing the details..."
    ]

    LAUNCHING_SWARM = [
        "🚀 Action confirmed: *{match}*. Deploying the Swarm [Logistics, Tactics, Market, Narrative]...",
        "📡 Syncing all agents for *{match}*. Calculating adjusted xG and market edge...",
        "🕵️ Identified: *{match}*. Launching deep-swarm analysis now..."
    ]
    
    CONFIRMATION_PROMPTS = [
        "I assume you mean *{match}*?\nShall I run the numbers?",
        "Found it: *{match}*.\nWant me to deploy the swarm?",
        "Next up: *{match}*.\nReady to analyze?"
    ]
    
    ANALYSIS_ERROR = "⚠️ Something went wrong with the analysis. Let me try again..."
    
    CONTEXT_ERROR = "I'm having trouble accessing that information right now. Could you rephrase your question?"
    
    GENERAL_HELP = (
        "Hey! I'm GoalMine, your World Cup betting assistant. "
        "I can analyze matches, check schedules, and identify value bets. "
        "What would you like to know?"
    )

    @staticmethod
    def get_greeting():
        return Responses.GREETING

    @staticmethod
    def get_reading():
        return random.choice(Responses.MATCH_READING)

    @staticmethod
    def get_launch(match):
        return random.choice(Responses.LAUNCHING_SWARM).format(match=match)
    
    @staticmethod
    def get_confirmation(match):
        """Returns a natural confirmation prompt for a match."""
        return random.choice(Responses.CONFIRMATION_PROMPTS).format(match=match)

    NO_MATCHES_TODAY = "📅 *Calendar Check:* No official World Cup matches scheduled for today.\n\nTry asking for the 'Full Schedule' or analyze an upcoming clash like 'Analyze USA vs Mexico'."
    UNKNOWN_TEAMS = "❓ *Identify Failed:* I couldn't quite catch those teams. Could you specify them clearly? (e.g., 'Analyze England vs Germany')"
    INVALID_SCHEDULE = "⚠️ *Fixture Error:* Match not found in the official World Cup 2026 Schedule.\nI only track sanctioned tournament games."
