from langgraph_whatsapp.agent import Agent
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from src.langgraph_whatsapp.config import TWILIO_AUTH_TOKEN
from abc import ABC, abstractmethod
import logging

LOGGER = logging.getLogger(__name__)

class WhatsAppAgent(ABC):
    """
    Interface for WhatsApp agent implementations.
    All WhatsApp channel implementations should inherit from this class.
    """

    @abstractmethod
    async def handle_message(self, request: Request) -> str:
        """
        Entrypoint for handling incoming WhatsApp messages.
        
        :param request: The incoming request object
        :return: Response to be sent back to WhatsApp
        """
        pass

class WhatsAppAgentTwilio(WhatsAppAgent):
    def __init__(self):
        if not TWILIO_AUTH_TOKEN:
            raise ValueError("TWILIO_AUTH_TOKEN is not configured or empty.")
        self.agent = Agent()
        self.validator = RequestValidator(TWILIO_AUTH_TOKEN)


    async def handle_message(self, request: Request) -> str:
        """
        Entrypoint for handling incoming WhatsApp messages with Twilio validation.

        :param request: The incoming FastAPI request object
        :return: Response containing TwiML XML or error
        """
        # Validate the request
        if not await self.validate_request(request):
            raise HTTPException(status_code=403, detail="Twilio signature validation failed")

        form_data = await request.form()
        sender = form_data.get('From', "").strip() # e.g., 'whatsapp:+14155238886'
        content = form_data.get('Body', "").strip()
        
        # Get media information if available
        num_media = int(form_data.get('NumMedia', "0"))
        
        # Initialize media as None
        media = None
        
        # If there's at least one media item and it's an image, use only the first one
        if num_media > 0:
            media_url = form_data.get('MediaUrl0', "")
            media_content_type = form_data.get('MediaContentType0', "")
            
            if media_url and media_content_type:
                if media_content_type.startswith('image/'):
                    # Only process images
                    media = {
                        "url": media_url,
                        "content_type": media_content_type
                    }
                    print(f"Found image: {media_url}")
                else:
                    print(f"Ignoring non-image media type: {media_content_type}")
                
                # Log if additional media is being ignored
                if num_media > 1:
                    print(f"Ignoring {num_media-1} additional media items")

        if not sender:
             raise HTTPException(status_code=400, detail="Missing 'From' in request form")

        agent_response = await self._process_message(sender, content, media)

        twilio_resp = MessagingResponse()
        twilio_resp.message(agent_response)

        return str(twilio_resp)

    async def _process_message(self, sender: str, content: str, media: dict = None) -> str:
        """
        Process the incoming message and generate a response using the agent.

        :param sender: The sender's identifier (e.g., WhatsApp number)
        :param content: The content of the message
        :param media: Dictionary with image media data (url and content_type)
        :return: Response string from the agent
        """
        input_data = {
            "id": sender,
            "user_message": content,
        }
        
        # Add media information if available
        if media:
            input_data["media"] = media
            
        print(f"Sending to agent: {input_data}")
        # Invoke the agent with the message content and image attachment
        return await self.agent.invoke(**input_data)