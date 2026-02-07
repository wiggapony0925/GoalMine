import random

class Responses:
    """
    Central repository for premium, conversational bot strings.
    Clean, punchy messages designed for WhatsApp button conversation flow.
    """
    
    GREETING = (
        "⚽ *GoalMine AI* — World Cup 2026\n\n"
        "Sharp odds. Real edges. Zero fluff.\n\n"
        "Here's what I do:\n"
        "• 📊 *Analyze* any match — say _\"Analyze USA vs Mexico\"_\n"
        "• 🎯 *Parlays* — say _\"Parlay this with Brazil\"_\n"
        "• 💵 *Budget plans* — say _\"How should I spend $200?\"_\n\n"
        "I drop a *Sharp Briefing* every morning at *5 AM*.\n\n"
        "What match are we looking at?"
    )

    MATCH_READING = [
        "🔍 Pulling live data…",
        "⚙️ Reading odds & match context…",
        "📡 Syncing market data…"
    ]

    LAUNCHING_SWARM = [
        "🚀 *{match}* — Running full analysis…",
        "📡 *{match}* — Crunching xG & market edge…",
        "🔬 *{match}* — Deep scan in progress…"
    ]
    
    CONFIRMATION_PROMPTS = [
        "👉 *{match}* — want me to run it?",
        "📌 *{match}* — shall I break it down?",
        "🎯 *{match}* — ready to analyze?"
    ]
    
    ANALYSIS_ERROR = "⚠️ Hit a snag pulling that analysis. Give me one more shot — try again."
    
    CONTEXT_ERROR = "Hmm, couldn't pull that up. Try rephrasing your question."
    
    GENERAL_HELP = (
        "⚽ I'm *GoalMine* — your World Cup edge-finder.\n"
        "Ask me to analyze a match, check the schedule, or find value bets."
    )

    BET_OPTIONS_FOOTER = (
        "🎲 *Bet Options*\n"
        "Want more plays? Say _\"more bets\"_ or _\"parlay this\"_."
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

    NO_MATCHES_TODAY = (
        "📅 No World Cup matches today.\n\n"
        "Say _\"full schedule\"_ or try _\"Analyze USA vs Mexico\"_."
    )
    UNKNOWN_TEAMS = (
        "❓ Couldn't catch those teams.\n"
        "Try something like _\"Analyze England vs Germany\"_."
    )
    INVALID_SCHEDULE = (
        "⚠️ Match not found in the World Cup 2026 schedule.\n"
        "I only cover official tournament fixtures."
    )
