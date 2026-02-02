import logging
import os
import pyfiglet
from colorama import init, Fore, Style
from flask import request

def setup_logging():
    """
    Configures the application logger (GoalMine) and suppresses external noise.
    Returns: logger instance
    """
    # 1. Reset Root Logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(level=logging.WARNING) # Suppress external libs

    # 2. Configure GoalMine Logger
    logger = logging.getLogger("GoalMine")
    logger.setLevel(logging.INFO)
    logger.propagate = False # Prevent double logging if root captures it

    # File Handler (Full Detail, Overwrite on Restart)
    file_handler = logging.FileHandler('app.log', mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Console Handler (Clean, just the message)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Suppress noisy libraries explicitly
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logger

def register_request_logger(app, logger):
    """
    Attaches a hook to Flask to log incoming HTTP requests cleanly.
    """
    @app.after_request
    def log_response(response):
        status_code = response.status_code
        if status_code == 200:
            symbol = "🟢"
        elif status_code >= 400:
            symbol = "🔴"
        else:
            symbol = "🔵"
            
        # Only log webhook traffic to keep it clean
        if "webhook" in request.path:
            logger.info(f"📡 Incoming {request.method} {request.path} -> {symbol} {response.status}")
        
        return response

def print_start_banner():
    """
    Prints the startup ASCII banner with system status.
    """
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        init(autoreset=True)
        
        # Database Status Check
        db_status = Fore.RED + "OFFLINE"
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
            db_status = Fore.GREEN + "ONLINE (Supabase Cloud)"
        
        # Data Files Status Check
        from data.scripts.data import VENUES_DB, SCHEDULE, BET_TYPES
        data_status = Fore.GREEN + f"✅ {len(VENUES_DB)} venues, {len(SCHEDULE)} matches, {len(BET_TYPES)} bet types"
        if not VENUES_DB or not SCHEDULE:
            data_status = Fore.RED + "⚠️ Missing data files"
        
        ascii_banner = pyfiglet.figlet_format("GoalMine AI")
        print(Fore.CYAN + ascii_banner)
        print(Fore.GREEN + "✅ System Initialized: World Cup 2026 Betting Engine Online")
        print(Fore.YELLOW + f"💾 Persistence: {db_status}")
        print(Fore.YELLOW + f"📊 Data: {data_status}")
        print(Fore.YELLOW + "🤖 Agents: [Logistics, Tactics, Market, Narrative] -> READY")
        print(Fore.MAGENTA + f"📡 Webhook Active: /webhook")
        print(Style.RESET_ALL)
