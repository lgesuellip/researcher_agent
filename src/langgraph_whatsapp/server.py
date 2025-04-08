from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from langgraph_whatsapp.agent import Agent
import logging

APP = FastAPI()
WSP_AGENT = Agent()
LOGGER = logging.getLogger(__name__)

@APP.post("/whatsapp")
async def whatsapp_reply_twilio(request: Request):

    form_data = await request.form()
    
    # Log all incoming data for debugging
    LOGGER.info("Incoming WhatsApp request data:")
    for key, value in form_data.items():
        LOGGER.info(f"{key}: {value}")

    incoming_msg = form_data.get("Body", "").strip()
    sender = form_data.get("From", "").strip()
    
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        try:
            LOGGER.info(f"Processing message from {sender}: {incoming_msg}")
            response_text = await WSP_AGENT.invoke(sender, incoming_msg)
            LOGGER.info(f"Response to be sent: {response_text}")
            msg.body(response_text)
        except Exception as e:
            LOGGER.error(f"Error processing message: {e}")
            msg.body("Sorry, I encountered an error processing your message.")
    else:
        msg.body("No message received")
    
    # Log the outgoing response
    response_str = str(resp)
    LOGGER.info(f"Outgoing response XML: {response_str}")

    # Return with proper content type for TwiML
    return Response(content=response_str, media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        APP,
        host="0.0.0.0",
        port=8081,
        log_level="info"
    ) 