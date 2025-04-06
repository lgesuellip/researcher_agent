from fastapi import FastAPI, Request
from twilio.twiml.messaging_response import MessagingResponse
from langgraph_whatsapp.agent import Agent
import logging

APP = FastAPI()
WSP_AGENT = Agent()
LOGGER = logging.getLogger(__name__)

@APP.post("/whatsapp")
async def whatsapp_reply_twilio(request: Request):
    # Get the raw form data
    form_data = await request.form()
    
    # Log all incoming data
    print("Incoming WhatsApp request data:")
    for key, value in form_data.items():
        print(f"{key}: {value}")
    
    # Process the message and generate a response
    incoming_msg = form_data.get("Body", "").strip()  # Received message
    sender = form_data.get("From", "").strip()  # Sender's number
    
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        # Process the message through the agent
        try:
            # Extract numeric sender ID from the phone number
            sender_id = int(''.join(filter(str.isdigit, sender)))
            response_text = await WSP_AGENT.invoke(sender_id, incoming_msg)
            msg.body(response_text)
        except Exception as e:
            LOGGER.error(f"Error processing message: {e}")
            msg.body("Sorry, I encountered an error processing your message.")
    else:
        msg.body("No message received")

    return str(resp)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        APP,
        host="0.0.0.0",
        port=8081,
        log_level="info"
    ) 