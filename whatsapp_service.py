import requests
import logging
from datetime import datetime
from app import app, db
from models import WhatsAppMessage, Client

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_token = app.config.get('WHATSAPP_API_TOKEN')
        self.base_url = "https://graph.facebook.com/v18.0"
        
    def get_business_accounts(self):
        """Get WhatsApp Business accounts"""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/me/businesses",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting business accounts: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting business accounts: {str(e)}")
            return None
    
    def get_phone_number_id(self):
        """Get the phone number ID for sending messages"""
        # This would typically come from your WhatsApp Business setup
        # For now, we'll use a placeholder that should be configured
        return app.config.get('WHATSAPP_PHONE_NUMBER_ID', 'YOUR_PHONE_NUMBER_ID')
    
    def send_message(self, to_phone, message_text):
        """Send a WhatsApp message"""
        phone_number_id = self.get_phone_number_id()
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/{phone_number_id}/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Save message to database
                client = Client.query.filter_by(whatsapp=to_phone).first()
                message = WhatsAppMessage(
                    client_id=client.id if client else None,
                    phone_number=to_phone,
                    message_id=result.get('messages', [{}])[0].get('id'),
                    content=message_text,
                    direction='outgoing',
                    status='sent'
                )
                db.session.add(message)
                db.session.commit()
                
                return result
            else:
                logger.error(f"Error sending message: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception sending message: {str(e)}")
            return None
    
    def get_messages(self, limit=50):
        """Get recent WhatsApp messages"""
        # This is a simplified version. In reality, you'd need to set up webhooks
        # to receive messages in real-time from WhatsApp
        messages = WhatsAppMessage.query.order_by(
            WhatsAppMessage.timestamp.desc()
        ).limit(limit).all()
        
        return messages
    
    def process_incoming_message(self, webhook_data):
        """Process incoming WhatsApp message from webhook"""
        try:
            entry = webhook_data.get('entry', [])
            if not entry:
                return
            
            changes = entry[0].get('changes', [])
            if not changes:
                return
            
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            
            for message_data in messages:
                phone_number = message_data.get('from')
                message_id = message_data.get('id')
                timestamp = message_data.get('timestamp')
                
                # Get message content
                content = ""
                message_type = "text"
                
                if 'text' in message_data:
                    content = message_data['text']['body']
                elif 'image' in message_data:
                    content = message_data['image'].get('caption', 'Imagem recebida')
                    message_type = "image"
                elif 'document' in message_data:
                    content = message_data['document'].get('filename', 'Documento recebido')
                    message_type = "document"
                
                # Find or create client
                client = Client.query.filter_by(whatsapp=phone_number).first()
                if not client:
                    # Create new client from phone number
                    client = Client(
                        name=f"Cliente {phone_number}",
                        whatsapp=phone_number,
                        phone=phone_number,
                        status='prospect'
                    )
                    db.session.add(client)
                    db.session.flush()
                
                # Save message
                message = WhatsAppMessage(
                    client_id=client.id,
                    phone_number=phone_number,
                    message_id=message_id,
                    content=content,
                    message_type=message_type,
                    direction='incoming',
                    timestamp=datetime.fromtimestamp(int(timestamp))
                )
                db.session.add(message)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing incoming message: {str(e)}")
            db.session.rollback()

# Global instance
whatsapp_service = WhatsAppService()
