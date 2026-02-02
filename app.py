import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import threading
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from collections import deque
from core.log import setup_logging, register_request_logger, print_start_banner
from core.initializer.whatsapp import WhatsAppClient
from services.conversationalFlow.conversation import ConversationHandler
from services.buttonConversationalFlow.button_conversation import ButtonConversationHandler
from services import orchestrator
from core.config import settings

# --- SETUP ---
logger = setup_logging()

app = Flask(__name__)
register_request_logger(app)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# --- BACKGROUND WORKER ---
# Dedicated loop for long-running background tasks (prevents loop destruction on request end)
bg_loop = asyncio.new_event_loop()

def start_bg_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_bg_loop, args=(bg_loop,), daemon=True).start()

def run_bg_task(coro):
    """Schedules a coroutine to run in the background thread's loop."""
    asyncio.run_coroutine_threadsafe(coro, bg_loop)

print_start_banner()

# --- SERVICES ---
wa_client = WhatsAppClient()
# Deduplication Cache (FIFO)
PROCESSED_IDS = set()
ID_QUEUE = deque(maxlen=500)

# Dynamic Handler Selection
if settings.get('app.interaction_mode') == "BUTTON_STRICT":
    from core.initializer.database import Database
    db_client = Database()
    conv_handler = ButtonConversationHandler(wa_client, db_client)
    logger.info("🛡️ STRICT MODE ACTIVATED: Using ButtonConversationHandler")
else:
    conv_handler = ConversationHandler(wa_client)
    logger.info("💬 CONVERSATIONAL MODE: Using standard ConversationHandler")

# --- SCHEDULER ---
def push_morning_brief():
    """ Daily Brief from settings """
    logger.info("Pushing Morning Brief...")
    
    # 1. Get raw data needed for template / text
    matches = orchestrator.get_todays_matches()
    num_edges = len(matches) # Simplified for now
    today_str = datetime.now().strftime("%b %d")
    top_match = f"{matches[0]['team_home']} vs {matches[0]['team_away']}" if matches else "N/A"

    test_user = "9294255178"
    
    # Generate Fallback Text
    fallback = orchestrator.get_schedule_brief(days=1)

    if settings.get('whatsapp.use_templates'):
        template_name = settings.get('whatsapp.templates.briefing', 'goalmine_alpha_briefing')
        wa_client.send_template_message(
            test_user, 
            template_name, 
            [today_str, num_edges, top_match],
            fallback_text=fallback
        )
    else:
        if fallback:
            wa_client.send_message(test_user, fallback)

def check_upcoming_matches_alert():
    """ Runs based on settings interval for Kick-off Alerts """
    upcoming = orchestrator.get_upcoming_matches()
    test_user = "9294255178"

    for m in upcoming:
        # Generate Fallback Text
        fallback = f"🚨 KICK-OFF ALERT: {m['team_home']} vs {m['team_away']} starts in 1 hour!\nReply 'Analyze {m['team_home']}' for a last-minute edge."
        
        if settings.get('whatsapp.use_templates'):
            template_name = settings.get('whatsapp.templates.kickoff', 'goalmine_kickoff_alert')
            wa_client.send_template_message(
                test_user, 
                template_name, 
                [m['team_home'], m['team_away']],
                fallback_text=fallback
            )
        else:
            wa_client.send_message(test_user, fallback)


scheduler = BackgroundScheduler()
scheduler.add_job(
    push_morning_brief, 
    'cron', 
    hour=settings.get('scheduling.morning_brief_hour', 5), 
    minute=settings.get('scheduling.morning_brief_minute', 0)
)
scheduler.add_job(
    check_upcoming_matches_alert, 
    'interval', 
    minutes=settings.get('scheduling.kickoff_alert_interval_mins', 15)
)
scheduler.start()

# --- ROUTES ---
@app.route("/")
def home():
    return "GoalMine WhatsApp Bot is Running!"


@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
    # Maintenance Check
    if settings.get('app.maintenance_mode'):
        logger.warning("🚫 Webhook hit while in Maintenance Mode. Ignoring.")
        return "Service Temporarily Unavailable", 503

    logger.info(f"📩 Webhook Hit: {request.method}")
    # 1. Verification Request
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                return challenge, 200
            else:
                return "Forbidden", 403
        return "Bad Request", 400

    # 2. Event Notification
    if request.method == "POST":
        body = request.json
        if body.get("object"):
            if (
                body.get("entry")
                and body["entry"][0].get("changes")
                and body["entry"][0]["changes"][0].get("value")
                and body["entry"][0]["changes"][0]["value"].get("messages")
            ):
                changes = body["entry"][0]["changes"][0]["value"]
                message_data = changes["messages"][0]
                from_number = message_data["from"]
                msg_type = message_data.get("type")
                
                msg_body = ""
                
                # EXTRACT CONTENT BASED ON TYPE
                if msg_type == "text":
                    msg_body = message_data["text"]["body"]
                
                elif msg_type == "interactive":
                    interactive = message_data["interactive"]
                    int_type = interactive.get("type")
                    
                    if int_type == "button_reply":
                        # User clicked a button
                        msg_body = interactive["button_reply"]["id"]
                        logger.info(f"🖱️ Button Clicked: {interactive['button_reply']['title']} (ID: {msg_body})")
                        
                    elif int_type == "list_reply":
                        # User selected from a list
                        msg_body = interactive["list_reply"]["id"]
                        logger.info(f"📜 List Selection: {interactive['list_reply']['title']} (ID: {msg_body})")
                
                # Mark as Read (Blue Tick)
                msg_id = message_data.get("id")
                
                # DEDUPLICATION CHECK
                if msg_id in PROCESSED_IDS:
                    logger.warning(f"♻️ Duplicate message ID {msg_id} ignored.")
                    return "ALREADY_PROCESSED", 200
                
                if msg_id:
                    PROCESSED_IDS.add(msg_id)
                    ID_QUEUE.append(msg_id)
                    # Sync set with queue maxlen
                    if len(PROCESSED_IDS) > 500:
                        oldest = ID_QUEUE.popleft()
                        PROCESSED_IDS.discard(oldest)
                    
                    wa_client.mark_as_read(msg_id)

                # Delegate to Conversation Handler if we found content
                if msg_body:
                    # BACKGROUND THE PROCESSING via persistent loop
                    run_bg_task(conv_handler.handle_incoming_message(from_number, msg_body))

            return "EVENT_RECEIVED", 200
        else:
            return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
