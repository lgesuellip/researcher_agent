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
        print(TWILIO_AUTH_TOKEN)
        self.validator = RequestValidator(TWILIO_AUTH_TOKEN)

    async def handle_message(self, request: Request) -> str:
        """
        Entrypoint for handling incoming WhatsApp messages with Twilio validation.

        :param request: The incoming FastAPI request object
        :return: Response containing TwiML XML or error
        """
        form_data = await request.form()
        post_vars = dict(form_data)

        print("--- Twilio Validation ---")
        # Construct the URL using the forwarded headers to match what Twilio expects
        forwarded_proto = request.headers.get("x-forwarded-proto", "http")
        forwarded_host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost"))
        url = f"{forwarded_proto}://{forwarded_host}{request.url.path}"
        print(f"URL used for validation: {url}")
        print(f"POST variables used for validation: {post_vars}")
        signature_header = request.headers.get("X-Twilio-Signature", "")
        print(f"X-Twilio-Signature header: {signature_header}")
        token_str = self.validator.token.decode()
        token_start = token_str[:5]
        token_end = token_str[-5:]
        print(f"Auth Token used: {token_start}...{token_end}")

        validation_result = self.validator.validate(
            url,  # Use the manually constructed URL
            post_vars,
            signature_header
        )
        print(f"Validation result: {validation_result}")
        print("-------------------------")

        if not validation_result:
            raise HTTPException(status_code=403, detail="Twilio signature validation failed")

        sender = form_data.get('From', "").strip() # e.g., 'whatsapp:+14155238886'
        content = form_data.get('Body', "").strip()

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