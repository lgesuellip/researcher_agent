from langgraph_whatsapp.agent import Agent
from twilio.twiml.messaging_response import MessagingResponse
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from src.langgraph_whatsapp.config import TWILIO_AUTH_TOKEN

class WhatsAppAgent:
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
        print(request.__dict__)
        print(request.url)
        form_req = await request.form()
        print(form_req.__dict__)
        print(request.headers.get("x-twilio-signature", ""))
        print(request.headers.get("X-Twilio-Signature", ""))


        form_ = await request.form()
        if not self.validator.validate(
            str(request.url),
            form_,  
            request.headers.get("x-twilio-signature", "")
        ):
            raise HTTPException(status_code=403, detail="Twilio signature validation failed")

        # Extract message details from form data
        sender = form_.get('From', "").strip() # e.g., 'whatsapp:+14155238886'
        content = form_.get('Body', "").strip()

        if not sender or not content:
             raise HTTPException(status_code=400, detail="Missing 'From' or 'Body' in request form")

        agent_response = self._process_message(sender, content)

        twilio_resp = MessagingResponse()
        twilio_resp.message(agent_response)

        return str(twilio_resp)

    def _process_message(self, sender: str, content: str) -> str:
        """
        Process the incoming message and generate a response using the agent.

        :param sender: The sender's identifier (e.g., WhatsApp number)
        :param content: The content of the message
        :return: Response string from the agent
        """
        
        return self.agent.invoke(id=sender, message=content)