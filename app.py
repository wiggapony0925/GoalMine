import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verify Token should be kept in your .env file
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.route("/")
def home():
    return "GoalMine WhatsApp Bot is Running!"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Webhook for WhatsApp API.
    GET: Verifies the webhook subscription.
    POST: Receives messages from WhatsApp.
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
        # Handle incoming messages
        body = request.json
        logger.info(f"Received webhook: {body}")
        
        # Check if it's a message from WhatsApp Cloud API
        if body.get("object"):
            if (
                body.get("entry")
                and body["entry"][0].get("changes")
                and body["entry"][0]["changes"][0].get("value")
                and body["entry"][0]["changes"][0]["value"].get("messages")
            ):
                phone_number_id = body["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
                from_number = body["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
                msg_body = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] 
                
                logger.info(f"Message from {from_number}: {msg_body}")
                
                # TODO: Process the message and send a response
                
            return "EVENT_RECEIVED", 200
        else:
            return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
