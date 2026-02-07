import os
from datetime import datetime
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
    """ Daily Brief — sends today's match lineup with venue context. """
    logger.info("☀️ Pushing Morning Brief...")
    
    try:
        matches = orchestrator.get_todays_matches()
        test_user = os.getenv("ALERT_PHONE_NUMBER", "9294255178")
        
        if not matches:
            logger.info("📅 No matches today — skipping morning brief.")
            return
        
        today_str = datetime.now().strftime("%b %d")
        num_matches = len(matches)
        top_match = f"{matches[0]['team_home']} vs {matches[0]['team_away']}"
        top_venue = matches[0].get('venue', 'TBD')

        # Generate rich fallback text
        fallback = orchestrator.get_schedule_brief(days=1)

        if settings.get('whatsapp.use_templates'):
            template_name = settings.get('whatsapp.templates.briefing', 'goalmine_alpha_briefing')
            wa_client.send_template_message(
                test_user, 
                template_name, 
                [today_str, str(num_matches), top_match],
                fallback_text=fallback
            )
        else:
            if fallback:
                wa_client.send_message(test_user, fallback)
    except Exception as e:
        logger.error(f"❌ Morning brief failed: {e}")

def check_upcoming_matches_alert():
    """ Runs on interval — sends kickoff alerts with venue + stage context. """
    try:
        upcoming = orchestrator.get_upcoming_matches()
        test_user = os.getenv("ALERT_PHONE_NUMBER", "9294255178")

        for m in upcoming:
            home = m['team_home']
            away = m['team_away']
            venue = m.get('venue', 'TBD')
            stage = m.get('stage', 'Group Stage')
            time_str = orchestrator.format_to_12hr(m['date_iso'])
            
            fallback = (
                f"🚨 *KICKOFF ALERT*\n\n"
                f"⚽ *{home} vs {away}*\n"
                f"🕐 {time_str} · {stage}\n"
                f"🏟️ {venue}\n\n"
                f"Say _\"analyze {home} vs {away}\"_ for a last-minute edge."
            )
            
            if settings.get('whatsapp.use_templates'):
                template_name = settings.get('whatsapp.templates.kickoff', 'goalmine_kickoff_alert')
                wa_client.send_template_message(
                    test_user, 
                    template_name, 
                    [home, away],
                    fallback_text=fallback
                )
            else:
                wa_client.send_message(test_user, fallback)
    except Exception as e:
        logger.error(f"❌ Kickoff alert failed: {e}")


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
