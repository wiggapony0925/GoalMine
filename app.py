import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

from core.log import setup_logging, register_request_logger, print_start_banner
from core.whatsapp import WhatsAppClient
from services.conversation import ConversationHandler
from services import orchestrator
from core.config import settings

# --- SETUP ---
logger = setup_logging()

app = Flask(__name__)
register_request_logger(app)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
print_start_banner()

# --- SERVICES ---
wa_client = WhatsAppClient()
conv_handler = ConversationHandler(wa_client)

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
                from_number = changes["messages"][0]["from"]
                msg_body = changes["messages"][0]["text"]["body"]

                # Delegate to Conversation Handler
                await conv_handler.handle_incoming_message(from_number, msg_body)

            return "EVENT_RECEIVED", 200
        else:
            return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
