import os
import logging
import asyncio
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from services import orchestrator
from agents.gatekeeper.gatekeeper import Gatekeeper
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import pyfiglet
from colorama import init, Fore, Style

# Load environment variables
load_dotenv()
init(autoreset=True)

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fancy Startup
ascii_banner = pyfiglet.figlet_format("GoalMine AI")
print(Fore.CYAN + ascii_banner)
print(Fore.GREEN + "✅ System Initialized: World Cup 2026 Betting Engine Online")
print(Fore.YELLOW + "🧠 Agents Loaded: Logistics, Tactics, Market, Narrative, Quant")
print(Fore.MAGENTA + "📡 Webhook Active: Listening for WhatsApp Signals...")
print(Style.RESET_ALL)

# Verify Token should be kept in your .env file
from core.whatsapp import WhatsAppClient

# ... (Logging setup remains) ...

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# Initialize WhatsApp Client
wa_client = WhatsAppClient()

# --- SCHEDULER (Scenario A: Morning Brief) ---
def push_morning_brief():
    logger.info("Pushing Morning Brief...")
    msg = orchestrator.get_morning_brief_content()
    if msg:
        # In production, iterate over subscribed users
        test_user = "15550000000" # Replace with real number
        wa_client.send_message(test_user, msg)

scheduler = BackgroundScheduler()
scheduler.add_job(push_morning_brief, 'cron', hour=8, minute=0)
scheduler.start()

# --- WEBHOOK ROUTES ---
@app.route("/")
def home():
    return "GoalMine WhatsApp Bot is Running!"

@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
    """
    Webhook for WhatsApp API (Async).
    """
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                logger.info("Webhook Verified!")
                return challenge, 200
            else:
                return "Forbidden", 403
        return "Bad Request", 400

    if request.method == "POST":
        body = request.json
        logger.info(f"Received webhook: {body}")
        
        if body.get("object"):
            if (
                body.get("entry")
                and body["entry"][0].get("changes")
                and body["entry"][0]["changes"][0].get("value")
                and body["entry"][0]["changes"][0]["value"].get("messages")
            ):
                changes = body["entry"][0]["changes"][0]["value"]
                phone_number_id = changes["metadata"]["phone_number_id"]
                from_number = changes["messages"][0]["from"]
                msg_body = changes["messages"][0]["text"]["body"]
                
                logger.info(f"Message from {from_number}: {msg_body}")
                
                # --- GATEKEEPER LOGIC ---
                intent, extracted_text = Gatekeeper.classify_intent(msg_body)
                
                if intent == "CHIT_CHAT" or intent == "OFF_TOPIC":
                    resp = Gatekeeper.get_response(intent)
                    wa_client.send_message(from_number, resp)
                    
                elif intent == "BETTING":
                    # Check for "1", "2" prompt response from Scenario A
                    match_idx = -1
                    if msg_body.strip() == "1": match_idx = 0
                    if msg_body.strip() == "2": match_idx = 1
                    
                    match_info = None
                    if match_idx >= 0:
                        # Scenario A Follow-up
                        match_info = orchestrator.get_match_info_from_selection(match_idx)
                        if match_info:
                            wa_client.send_message(from_number, f"Targeting {match_info['home_team']} vs {match_info['away_team']}. Checking Logistics & Odds... 🕵️")
                    else:
                        # Scenario B: Ad-Hoc
                        # Simplified extraction (mocking entity found)
                        match_info = {
                             'home_team': 'Mexico', 
                             'away_team': 'South Africa',
                             'venue_from': 'MetLife_NY', 
                             'venue_to': 'Azteca_Mexico'
                        }
                        wa_client.send_message(from_number, f"Analyzing {match_info['home_team']} vs {match_info['away_team']}. Running the Swarm... 🕵️")
                    
                    # RUN SWARM (Async)
                    if match_info:
                        briefing = await orchestrator.generate_betting_briefing(match_info)
                        final_report = await orchestrator.format_the_closer_report(briefing)
                        wa_client.send_message(from_number, final_report)
                    else:
                        wa_client.send_message(from_number, "Could not identify the match. Please check the schedule.")

            return "EVENT_RECEIVED", 200
        else:
            return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
