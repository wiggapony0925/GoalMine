import logging
import os
import pyfiglet
from colorama import init, Fore, Style
from flask import request

# Initialize colorama for terminal colors
init(autoreset=True)

def get_logger(name="GoalMine"):
    """
    Helper to get a sub-logger that inherits from the main GoalMine configuration.
    """
    if not name.startswith("GoalMine"):
        full_name = f"GoalMine.{name}"
    else:
        full_name = name
    logger = logging.getLogger(full_name)
    logger.propagate = True 
    return logger

def clear_log():
    """
    Truncates the app.log file to give a fresh start.
    """
    from datetime import datetime
    try:
        with open('app.log', 'w') as f:
            f.write(f"--- 🧼 LOG WIPED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Session Refresh) ---\n")
    except Exception as e:
        print(f"Failed to clear log: {e}")

class GoalMineFormatter(logging.Formatter):
    """
    Premium Formatter for Terminal Output with icons and vibrant colors.
    """
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
    }

    ICONS = {
        'GoalMine': '🏰',
        'Database': '📡',
        'LLM': '🧠',
        'WhatsApp': '💬',
        'Network': '🌐',
        'Orchestrator': '🎯',
        'Tactics': '⚔️',
        'Logistics': '🚛',
        'Market': '💰',
        'Narrative': '📰',
        'Quant': '🎲',
        'Conversation': '🗣️',
        'Gatekeeper': '🚪',
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        
        # Extract base component name (e.g., GoalMine.Database -> Database)
        comp_parts = record.name.split('.')
        base_comp = comp_parts[-1] if comp_parts else "System"
        icon = self.ICONS.get(base_comp, '⚙️')
        
        # Handle special formatting for LLM or Agent results
        message = record.getMessage()
        
        # 🟢 Special Formatting for "INTERNAL RESULTS" (JSON or long text)
        if base_comp == "LLM" and ("Response" in message or "Request" in message):
             icon = "🪄" 
             comp_color = Fore.MAGENTA
        elif base_comp in ["Tactics", "Logistics", "Market", "Narrative", "Quant"]:
             comp_color = Fore.CYAN
        else:
             comp_color = log_color

        comp_label = f"{icon} {base_comp}"
        
        # High-End Formatting
        if record.levelname == 'INFO':
            # Add a vertical bar for cleaner separation
            timestamp = self.formatTime(record, "%H:%M:%S")
            return f"{Fore.WHITE}{timestamp} | {comp_color}{comp_label.ljust(15)}{Style.RESET_ALL} | {message}"
        elif record.levelname == 'DEBUG':
             return f"{Fore.WHITE}{Style.DIM}[DEBUG] {comp_label.ljust(15)} | {message}"
        else:
            return f"{log_color}{record.levelname.ljust(8)} | {comp_label.ljust(15)} | {message}"

def setup_logging():
    """
    Centralized logging configuration for GoalMine.
    Initializes both file and console handlers.
    """
    # 1. Reset Root Logger handlers to avoid duplicates
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 2. Base Configuration for Root (Catch-all)
    logging.basicConfig(level=logging.WARNING)

    # 3. GoalMine Master Logger
    try:
        from core.config import settings
        log_level_str = settings.get('GLOBAL_APP_CONFIG.app.log_level', 'INFO').upper()
    except:
        log_level_str = 'INFO'
    
    log_level = getattr(logging, log_level_str, logging.INFO)

    # 4. Handlers
    # File Handler: Detailed for debugging, persistent in app.log
    file_handler = logging.FileHandler('app.log', mode='a') # Append for history
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # Console Handler: Optimized for clean terminal viewing
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(GoalMineFormatter())

    # Setup core loggers
    for logger_name in ["GoalMine", "WhatsApp", "Database", "Orchestrator", "Agent", "LLM", "Conversation", "KickoffAlerts", "MarketMonitor", "MorningBrief"]:
        l = logging.getLogger(logger_name)
        l.setLevel(log_level)
        l.propagate = False # Ensure these specific loggers don't propagate to root
        l.addHandler(file_handler)
        l.addHandler(console_handler)

    main_logger = logging.getLogger("GoalMine") # Get the configured GoalMine logger
    main_logger.info(f"✅ Logging System Initialized (Level: {log_level_str})")

    # Suppress external noise for a cleaner terminal
    # Library noise is suppressed at WARNING unless the app is in DEBUG mode
    ext_level = logging.WARNING if log_level != logging.DEBUG else logging.INFO
    
    for noisy_lib in ["werkzeug", "openai", "httpx", "httpcore", "apscheduler", "supabase", "postgrest"]:
        logging.getLogger(noisy_lib).setLevel(ext_level)
    
    # Extra quiet for werkzeug (Flask logs) unless in debug
    if log_level != logging.DEBUG:
        logging.getLogger("werkzeug").setLevel(logging.ERROR)

    return main_logger

def register_request_logger(app):
    """
    Cleaner Flask request logging.
    """
    logger = get_logger("Network")
    
    @app.after_request
    def log_response(response):
        from core.config import settings
        # We only care about matching/webhook logs to keep terminal noise down
        if "webhook" in request.path or settings.get('GLOBAL_APP_CONFIG.app.detailed_request_logging'):
            status = response.status_code
            symbol = "🟢" if status < 400 else "🔴"
            logger.info(f"{symbol} Net {request.method} {request.path} -> {status}")
        return response

def print_start_banner():
    """
    Prints a premium startup banner.
    """
    # Only print inside the Reloader process (when live) to avoid double print on startup
    # or if strictly not in debug mode (production).
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        ascii_banner = pyfiglet.figlet_format("GoalMine AI")
        print(Fore.CYAN + ascii_banner)
        print(Fore.GREEN + "🚀 GoalMine AI Prediction Engine — v2.0 'Ghost Logic' Active")
        print(Fore.WHITE + "------------------------------------------------------------")
        
        # Check Database
        # Metadata
        from data.scripts.data import SCHEDULE
        num_matches = len(SCHEDULE)
        
        # Security Check for Banner
        secret_status = "🛡️ SECURE (HMAC)" if os.getenv("WHATSAPP_APP_SECRET") else "🔓 STANDARD"

        print(Fore.WHITE + f"💾 Cloud Sync: ONLINE")
        print(Fore.WHITE + f"📅 Schedule: {num_matches} Matches Loaded")
        print(Fore.WHITE + f"🔐 Security: {secret_status}")
        print(Fore.WHITE + f"🤖 Agents: [Tactics, Logistics, Market, Narrative] -> WAITING")
        print(Fore.WHITE + "------------------------------------------------------------")
        print(Style.RESET_ALL)
