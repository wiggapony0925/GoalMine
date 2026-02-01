import os
import logging
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import pyfiglet
from colorama import init, Fore, Style

from core.whatsapp import WhatsAppClient
from services import orchestrator
from agents.gatekeeper.gatekeeper import Gatekeeper
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init(autoreset=True)
app = Flask(__name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

ascii_banner = pyfiglet.figlet_format("GoalMine AI")
print(Fore.CYAN + ascii_banner)
print(Fore.GREEN + "✅ System Initialized: World Cup 2026 Betting Engine Online")
print(Fore.YELLOW + "📊 Agents: [Logistics, Tactics, Market, Narrative] -> READY")
print(Fore.MAGENTA + f"📡 Webhook Active: /webhook")
print(Style.RESET_ALL)

wa_client = WhatsAppClient()

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
                
                intent, extracted_text = Gatekeeper.classify_intent(msg_body)
                
                if intent == "CHIT_CHAT" or intent == "OFF_TOPIC":
                    resp = Gatekeeper.get_response(intent)
                    wa_client.send_message(from_number, resp)
                    
                elif intent == "BETTING":
                    todays_games = orchestrator.get_todays_matches()
                    
                    match_info = None
                    if msg_body.strip() in ["1", "2"] and todays_games:
                        idx = int(msg_body.strip()) - 1
                        match_info = orchestrator.get_match_info_from_selection(idx)
                        if match_info:
                             wa_client.send_message(from_number, f"Targeting {match_info['home_team']} vs {match_info['away_team']}...")
                    
                    else:
                        wa_client.send_message(from_number, "🤖 Reading match details...")
                        match_info = await orchestrator.extract_match_details_from_text(msg_body)
                        
                        if not match_info:
                            if not todays_games:
                                wa_client.send_message(from_number, "No World Cup matches scheduled today.\nTry 'Analyze France vs Brazil'.")
                                return "EVENT_RECEIVED", 200
                            else:
                                wa_client.send_message(from_number, "I couldn't identify the teams. Please specify them clearly.")
                                return "EVENT_RECEIVED", 200
                        else:
                             wa_client.send_message(from_number, f"Identified: {match_info['home_team']} vs {match_info['away_team']}. Launching Swarm... 🕵️")

                    if match_info:
                        briefing = await orchestrator.generate_betting_briefing(match_info)
                        final_report = await orchestrator.format_the_closer_report(briefing)
                        wa_client.send_message(from_number, final_report)

            return "EVENT_RECEIVED", 200
        else:
            return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
