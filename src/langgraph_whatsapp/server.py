from fastapi import FastAPI, Request
from twilio.twiml.messaging_response import MessagingResponse
from langgraph_whatsapp.agent import Agent
import logging

APP = FastAPI()
WSP_AGENT = Agent()
LOGGER = logging.getLogger(__name__)

@APP.post("/whatsapp")
async def whatsapp_reply_twilio(request: Request):

    form_data = await request.form()

    incoming_msg = form_data.get("Body", "").strip()
    sender = form_data.get("From").strip()
    
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        try:
            response_text = await WSP_AGENT.invoke(sender, incoming_msg)
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