import os
import requests
import logging

logger = logging.getLogger(__name__)

class WhatsAppClient:
    """
    Handles all interactions with the WhatsApp Cloud API.
    """
    def __init__(self):
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")
        self.api_version = "v17.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def send_message(self, to_number, message_text):
        """
        Sends a standard text message.
        """
        if not self.token or not self.phone_number_id:
            logger.warning("WhatsApp Credentials missing. Message not sent.")
            return None

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message_text},
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"Message sent to {to_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            return None

    def send_template_message(self, to_number, template_name, language_code="en_US"):
        """
        Sends a pre-approved template message (required for business initiated conversations).
        """
        # Implementation for template sending
        pass
        
    def mark_as_read(self, message_id):
        """
        Marks a received message as read.
        """
        if not self.token or not self.phone_number_id:
            return

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        try:
            requests.post(url, headers=headers, json=data)
        except Exception as e:
            logger.warning(f"Failed to mark message as read: {e}")
