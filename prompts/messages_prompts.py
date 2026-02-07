



class ButtonResponses:
    """
    Dedicated copy for the Button-Strict Interaction Mode.
    Managed here to allow easy UI personality shifts.
    """

    MAIN_MENU = {
        "header": "🤖 GoalMine AI Headquarters",
        "body": "Welcome to the Command Center.\nSelect an operation below:",
        "footer": "Strict Mode Active",
        "buttons": [
            {"id": "Show_Schedule", "title": "View Schedule"},
            {"id": "Show_Help", "title": "Help / Rules"},
        ],
    }

    FALLBACK_MAIN_MENU_BODY = "I'm currently in High-Performance Mode. Please use the buttons below to navigate and explore fixtures! 👇\n\n"
    UNCLEAR_INPUT_PREFIX = (
        "⚠️ *Input not recognized.* Please select an option below to continue:\n\n"
    )

    SCHEDULE_BROWSER = {
        "header": "📅 World Cup Schedule",
        "body": "How would you like to browse the 2026 World Cup fixtures?",
        "footer": "GoalMine AI 🏆",
        "button": "Select Stage",
        "rows": [
            {
                "id": "Show_Groups_Menu",
                "title": "🌍 Group Stages",
                "description": "Browse Groups A-L",
            },
            {
                "id": "Show_Knockouts_Menu",
                "title": "🏆 Knockout Rounds",
                "description": "Round of 32 to The Final",
            },
        ],
    }

    GROUP_SELECTOR = {
        "header": "🌍 Group Stage Selector",
        "body": "Select a group to see its matches and analysis options.",
        "button": "Choose Group",
    }

    GROUP_SELECTOR_GL = {
        "header": "🌍 Group Stage Selector (G-L)",
        "body": "Continuing the group stage fixtures...",
        "button": "Choose Group",
    }

    KNOCKOUT_SELECTOR = {
        "header": "🏆 Knockout Stages",
        "body": "The road to the trophy. Select a round to view upcoming knockout matches.",
        "button": "Choose Round",
        "rows": [
            {"id": "Stage_Round_of_32", "title": "Round of 32"},
            {"id": "Stage_Round_of_16", "title": "Round of 16"},
            {"id": "Stage_Quarter-finals", "title": "Quarter-finals"},
            {"id": "Stage_Semi-finals", "title": "Semi-finals"},
            {"id": "Stage_Final", "title": "The Grand Final"},
        ],
    }

    MATCH_LIST_BODY = (
        "Select a fixture from {filter_name} to launch the swarm intelligence analysis."
    )
    MATCH_LIST_FOOTER = "GoalMine Tournament Browser"
    MATCH_LIST_BUTTON = "View Fixtures"

    HELP_MENU = (
        "🤖 *GoalMine AI Help*\n\n"
        "I am an advanced AI prediction engine for the 2026 World Cup.\n"
        "My Swarm of agents analyzes:\n"
        "• Performance Data (xG)\n"
        "• Market Odds\n"
        "• Tactical Matchups\n"
        "• Logistics (Weather/Travel)\n\n"
        "Tap *Analyze Matches* to start.\n\n"
        "📞 *Support Contact:*\n"
        "👤 Jeffrey Fernandez\n"
        "📱 9294255178\n"
        "📧 ninjeff06@gmail.com\n"
        "💼 capital.jfm@gmail.com"
    )

    BET_GENERATION_MENU = {
        "header": "🎲 Tactical Bet Generator",
        "body": "Quant Engine Ready.\nHow many value recommendations would you like?",
        "footer": "Select Quantity",
        "buttons": [
            {"id": "Bets_1", "title": "1 Top Pick"},
            {"id": "Bets_3", "title": "3 Smart Picks"},
            {"id": "Bets_5", "title": "5 Accumulator"},
        ],
    }

    ANALYSIS_FOOTER = {
        "header": "📊 Analysis Complete",
        "body": "What would you like to do next?",
        "buttons": [
            {"id": "Generate_Bets", "title": "🎲 Generate Bets"},
            {"id": "Show_Schedule", "title": "📅 More Matches"},
            {"id": "Show_MainMenu", "title": "🔙 Main Menu"},
        ],
    }

    BET_FOOTER = {
        "header": "🎲 Bet Options",
        "body": "Need more action?",
        "buttons": [
            {"id": "Generate_More", "title": "🔄 Generate More"},
            {"id": "Show_Schedule", "title": "📅 More Matches"},
            {"id": "Show_MainMenu", "title": "🔙 Main Menu"},
        ],
    }

    NO_MATCHES = "⚠️ No matches found for {filter_name}."
    MATCH_NOT_FOUND = "❌ Error: Match data not found."
    ANALYSIS_START = "🚀 Initializing Swarm for {home} vs {away}..."
    ANALYSIS_ERROR = (
        "⚠️ *Service Temporarily Unavailable*\n\n"
        "Our analysis engine encountered an issue. This may be due to a temporary API outage.\n\n"
        "If this persists, please contact the administrator:\n"
        "👤 *Jeffrey Fernandez*\n"
        "📱 9294255178\n"
        "📧 ninjeff06@gmail.com\n"
        "💼 capital.jfm@gmail.com"
    )
    
    # Rejection & Guidelines
    REJECT_TEXT = (
        "🤖 *GoalMine Command Center*\n\n"
        "Please select an option from the menu below to proceed with your analysis. 👇"
    )
    REJECT_PROFANITY = (
        "⛔ *Protocol Warning*\n\n"
        "Profanity is not permitted in this channel. I am programmed to maintain a professional standard.\n"
        "Please stick to the designated buttons for service."
    )
