import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

import logs
from core.whatsapp import WhatsAppClient
from services.conversation import ConversationHandler
from services import orchestrator

# --- SETUP ---
logger = logs.setup_logging()

app = Flask(__name__)
logs.register_request_logger(app, logger)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
logs.print_start_banner()

# --- SERVICES ---
wa_client = WhatsAppClient()
CONVERSATION_MEMORY = {}
conv_handler = ConversationHandler(wa_client, CONVERSATION_MEMORY)

# --- SCHEDULER ---
def push_morning_brief():
    """ 8am Daily Brief """
    logger.info("Pushing Morning Brief...")
    msg = orchestrator.get_morning_brief_content()

    if msg:
        test_user = "15550000000"
        wa_client.send_message(test_user, msg)
    else:
        logger.info("No matches today. Skipping brief.")


def check_upcoming_matches_alert():
    """ Runs every 15 mins for Kick-off Alerts """
    upcoming = orchestrator.get_upcoming_matches()

    for m in upcoming:
        test_user = "15550000000"
        msg = f"🚨 KICK-OFF ALERT: {m['team_home']} vs {m['team_away']} starts in 1 hour!\nReply 'Analyze {m['team_home']}' for a last-minute edge."
        wa_client.send_message(test_user, msg)


scheduler = BackgroundScheduler()
scheduler.add_job(push_morning_brief, 'cron', hour=8, minute=0)
scheduler.add_job(check_upcoming_matches_alert, 'interval', minutes=15)
scheduler.start()

# --- ROUTES ---
@app.route("/")
def home():
    return "GoalMine WhatsApp Bot is Running!"


@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
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
