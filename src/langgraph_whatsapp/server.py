from fastapi import FastAPI, Request, Response, HTTPException
from langgraph_whatsapp.channel import WhatsAppAgentTwilio
import logging

APP = FastAPI()
WSP_AGENT = WhatsAppAgentTwilio()

@APP.post("/whatsapp")
async def whatsapp_reply_twilio(request: Request):
    try:
        response = await WSP_AGENT.handle_message(request)
        return Response(content=response, media_type="application/xml")
    except HTTPException as e:
        logging.error(f"Error handling WhatsApp request: {e.detail}")
        raise e
    except Exception as e:
        logging.exception("Unhandled exception processing WhatsApp request")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        APP,
        host="0.0.0.0",
        port=8081,
        log_level="info"
    )