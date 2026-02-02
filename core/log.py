import logging
import os
import pyfiglet
from colorama import init, Fore, Style
from flask import request

# Initialize colorama for terminal colors
init(autoreset=True)

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
        
        comp_label = f"{icon} {base_comp}"
        
        # High-End Formatting
        if record.levelname == 'INFO':
            return f"{log_color}{comp_label.ljust(15)} | {record.getMessage()}"
        elif record.levelname == 'DEBUG':
             return f"{Fore.WHITE}{Style.DIM}[DEBUG] {comp_label.ljust(15)} | {record.getMessage()}"
        else:
            return f"{log_color}{record.levelname.ljust(8)} | {comp_label.ljust(15)} | {record.getMessage()}"

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
    from core.config import settings
    log_level_str = settings.get('app.log_level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    main_logger = logging.getLogger("GoalMine")
    main_logger.setLevel(log_level)
    main_logger.propagate = False

    # 4. Handlers
    # File Handler: Detailed for debugging, persistent in app.log
    file_handler = logging.FileHandler('app.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s | %(levelname)-8s | [%(name)s] | %(message)s')
    file_handler.setFormatter(file_format)

    # Console Handler: Optimized for clean terminal viewing
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(GoalMineFormatter())

    main_logger.addHandler(file_handler)
    main_logger.addHandler(console_handler)

    # Suppress external noise
    # Suppress external noise UNLESS detailed logging is on
    from core.config import settings
    if not settings.get('app.detailed_request_logging'):
        for noisy_lib in ["werkzeug", "openai", "httpx", "httpcore", "apscheduler", "supabase", "postgrest"]:
            logging.getLogger(noisy_lib).setLevel(logging.WARNING)
        
        # Extra quiet for werkzeug (Flask logs)
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
    else:
        # If detailed logging is on, set them to INFO so we see API calls
        for noisy_lib in ["openai", "httpx", "httpcore", "apscheduler", "supabase", "postgrest"]:
            logging.getLogger(noisy_lib).setLevel(logging.INFO)
            # Ensure they propagate to our handlers
            logging.getLogger(noisy_lib).addHandler(file_handler)
            if log_level == logging.DEBUG:
                 logging.getLogger(noisy_lib).addHandler(console_handler)

    return main_logger

def get_logger(name="GoalMine"):
    """
    Helper to get a sub-logger that inherits from the main GoalMine configuration.
    Example usage: logger = get_logger("Tactics")
    """
    # If the name doesn't start with GoalMine, we prefix it to ensure it inherits settings/handlers
    # if we were using propagate=True. But since we have custom handlers on "GoalMine",
    # we'll just attach them if it's a new top-level request.
    
    # For now, let's keep all app logic under the "GoalMine" hierarchy or just return a child.
    if not name.startswith("GoalMine"):
        full_name = f"GoalMine.{name}"
    else:
        full_name = name
        
    logger = logging.getLogger(full_name)
    
    # If this logger has no handlers and isn't the root, it might not log anything 
    # if we don't enable propagation or add handlers. 
    # We want child loggers to propagate up to "GoalMine".
    logger.propagate = True 
    
    return logger

def register_request_logger(app):
    """
    Cleaner Flask request logging.
    """
    logger = get_logger("Network")
    
    @app.after_request
    def log_response(response):
        from core.config import settings
        # We only care about matching/webhook logs to keep terminal noise down
        if "webhook" in request.path or settings.get('app.detailed_request_logging'):
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
        db_valid = os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")
        db_msg = Fore.GREEN + "Cloud Sync: ONLINE" if db_valid else Fore.RED + "Cloud Sync: OFFLINE (Check Keys)"
        print(f"💾 {db_msg}")
        
        # Check Data
        try:
            from data.scripts.data import SCHEDULE
            print(Fore.GREEN + f"📅 Schedule: {len(SCHEDULE)} Matches Loaded")
        except:
            print(Fore.RED + "📅 Schedule: FAILED TO LOAD")

        print(Fore.YELLOW + "🤖 Agents: [Tactics, Logistics, Market, Narrative] -> WAITING")
        print(Fore.WHITE + "------------------------------------------------------------\n")
