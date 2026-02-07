import os
import requests
import hmac
import hashlib
import json
from core.log import get_logger

logger = get_logger("WhatsApp")


class WhatsAppClient:
    """
    Handles all interactions with the WhatsApp Cloud API.
    """

    def __init__(self):
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")
        self.api_version = "v24.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET")
        self._appsecret_proof = (
            self._generate_appsecret_proof() if self.app_secret and self.token else None
        )

        # LOG SECURITY STATUS
        if self._appsecret_proof:
            logger.info("🛡️ WhatsApp Security: App Secret Proof ACTIVE (Secure Mode)")
        else:
            logger.warning(
                "🔓 WhatsApp Security: App Secret Proof INACTIVE (Standard Mode)"
            )

    def _generate_appsecret_proof(self):
        """Generates the appsecret_proof required for secure API calls."""
        return hmac.new(
            self.app_secret.encode("utf-8"), self.token.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def _get_headers(self):
        """Helper to get standardized headers including security proofs."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        # If user enabled 'Require App Secret' in Portal, we must send this
        if self._appsecret_proof:
            headers["x-app-secret-proof"] = self._appsecret_proof
        return headers

    def send_message(self, to_number, message_text):
        """
        Sends a standard text message.
        """
        if not self.token or not self.phone_number_id:
            logger.warning("WhatsApp Credentials missing. Message not sent.")
            return None

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = self._get_headers()
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message_text},
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            logger.info(f"Message sent to {to_number}")

            # [AUDIT LOG] Log what the bot said (Developer Only)
            logger.debug(
                f"🤖 BOT REPLY: {message_text[:200]}..."
                if len(message_text) > 200
                else f"🤖 BOT REPLY: {message_text}"
            )

            return response.json()
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                status = e.response.status_code
                if status == 401:
                    logger.error("❌ WHATSAPP AUTH ERROR (401 Unauthorized)")
                    logger.error("👉 TROUBLESHOOTING:")
                    logger.error(
                        "   1. Your WHATSAPP_TOKEN has likely expired. Temporary tokens only last 24 hours."
                    )
                    logger.error(
                        "   2. Go to Meta Developer Portal -> WhatsApp -> API Setup to generate a new token."
                    )
                    logger.error(
                        "   3. Check if your PHONE_NUMBER_ID in .env matches the portal."
                    )
                elif status == 400:
                    logger.error(f"❌ WHATSAPP BAD REQUEST (400): {e.response.text}")
                    logger.error("👉 TROUBLESHOOTING:")
                    logger.error(
                        "   1. Check if the recipient number is a 'Test Number' in your Meta Portal."
                    )
                    logger.error(
                        "   2. Ensure the phone number format is correct (no + or leading zeros)."
                    )
                    logger.error("   3. Check if THE PHONE_NUMBER_ID is correct.")
                else:
                    logger.error(f"WhatsApp API Error ({status}): {e.response.text}")
            else:
                logger.error(f"Network Error sending WhatsApp message: {e}")
            return None

    def send_template_message(
        self,
        to_number,
        template_name,
        components,
        fallback_text=None,
        language_code="en_US",
    ):
        """
        Sends a pre-approved template message.
        'components' should be a list of strings for variables {{1}}, {{2}}, etc.
        If it fails, it will attempt to send 'fallback_text' if provided.
        """
        if not self.token or not self.phone_number_id:
            logger.warning("WhatsApp Credentials missing. Template not sent.")
            return None

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = self._get_headers()

        parameters = [{"type": "text", "text": str(val)} for val in components]

        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": [],
            },
        }

        # 1. HANDLE BODY COMPONENTS
        # Determine if we are using positional list or named dict
        if isinstance(components, list):
            # Standard Positional Format
            parameters = [{"type": "text", "text": str(val)} for val in components]
        else:
            # Named Parameters Format
            parameters = [
                {"type": "text", "parameter_name": key, "text": str(val)}
                for key, val in components.items()
            ]

        data["template"]["components"].append(
            {"type": "body", "parameters": parameters}
        )

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Template '{template_name}' sent to {to_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            error_data = e.response.text if e.response else str(e)
            logger.warning(f"⚠️ Template '{template_name}' failed: {error_data}")

            if fallback_text:
                logger.info(
                    f"🔄 Attempting fallback to standard message for {to_number}"
                )
                return self.send_message(to_number, fallback_text)
            return None

    def mark_as_read(self, message_id):
        """
        Marks a received message as read.
        """
        if not self.token or not self.phone_number_id:
            return

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = self._get_headers()
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        try:
            requests.post(url, headers=headers, json=data, timeout=5)
        except Exception as e:
            logger.warning(f"Failed to mark message as read: {e}")

    def send_interactive_message(self, to_number, interactive_object):
        """
        Sends a List or Button message (no template approval needed).
        Args:
            to_number (str): Recipient phone number.
            interactive_object (dict): The inner 'interactive' JSON object properly formatted.
        """
        if not self.token or not self.phone_number_id:
            logger.warning(
                "WhatsApp Credentials missing. Interactive message not sent."
            )
            return None

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = self._get_headers()

        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": interactive_object,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            # If 400, log the payload for debugging
            if response.status_code == 400:
                logger.error(f"❌ WhatsApp 400 Payload: {json.dumps(data, indent=2)}")

            response.raise_for_status()
            logger.info(f"🔘 Interactive Message sent to {to_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            # EXTRACT FULL JSON ERROR BODY FOR 400s
            error_body = "No Response Body"
            if e.response is not None:
                try:
                    error_body = json.dumps(e.response.json(), indent=2)
                except Exception:
                    error_body = e.response.text

            logger.error(f"❌ WhatsApp API Failed: {e}")
            logger.error(f"📝 Error Details: {error_body}")
            return None

    def send_location_message(
        self, to_number, latitude, longitude, name=None, address=None
    ):
        """
        Sends a Location message.
        """
        if not self.token or not self.phone_number_id:
            logger.warning("WhatsApp Credentials missing. Location message not sent.")
            return None

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = self._get_headers()

        location_data = {"latitude": latitude, "longitude": longitude}
        if name:
            location_data["name"] = name
        if address:
            location_data["address"] = address

        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "location",
            "location": location_data,
        }

        try:
            requests.post(url, headers=headers, json=data, timeout=10)
            logger.info(f"📍 Location sent to {to_number}")
        except Exception as e:
            logger.error(f"Failed to send location: {e}")

    def send_typing_indicator(self, to_number):
        """
        Sends a 'typing...' status to the user using the standard sender action.
        """
        if not self.token or not self.phone_number_id:
            return

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = self._get_headers()

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "sender_action",
            "sender_action": "typing_on",
        }

        try:
            requests.post(url, headers=headers, json=data, timeout=5)
        except Exception:
            pass
