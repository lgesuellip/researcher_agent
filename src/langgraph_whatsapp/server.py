from fastapi import FastAPI, Request, Response, HTTPException
from langgraph_whatsapp.channel import WhatsAppAgentTwilio
import logging

APP = FastAPI()
WSP_AGENT = WhatsAppAgentTwilio()


# twilio_middleware.pyxs
from starlette.middleware.base import BaseHTTPMiddleware


class TwilioSignatureMiddleware(BaseHTTPMiddleware):
    """
    Reject any request to /whatsapp (or /twilio/webhook) that doesn't carry a
    valid X‑Twilio‑Signature header.
    """

    def __init__(self, app, path: str = "/whatsapp"):
        super().__init__(app)
        self.path = path

    async def dispatch(self, request, call_next):
        # Only run for the specific path (and POST).  Skip everything else.

        # Everything good → continue
        return await call_next(request)


APP.add_middleware(TwilioSignatureMiddleware, path="/whatsapp")

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