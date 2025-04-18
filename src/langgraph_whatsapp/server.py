from fastapi import FastAPI, Request, Response, HTTPException
from langgraph_whatsapp.channel import WhatsAppAgentTwilio
import logging

APP = FastAPI()
WSP_AGENT = WhatsAppAgentTwilio()


# twilio_middleware.pyxs
from starlette.middleware.base import BaseHTTPMiddleware
from twilio.request_validator import RequestValidator
from src.langgraph_whatsapp.config import TWILIO_AUTH_TOKEN

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
        if request.url.path == self.path and request.method.upper() == "POST":
            form_data = await request.form()
            post_vars = dict(form_data)

            validator = RequestValidator(TWILIO_AUTH_TOKEN)
            # Construct the URL using the forwarded headers to match what Twilio expects
            forwarded_proto = request.headers.get("x-forwarded-proto", "http")
            forwarded_host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost"))
            url = f"{forwarded_proto}://{forwarded_host}{request.url.path}"
            signature_header = request.headers.get("X-Twilio-Signature", "")

            if not validator.validate(
                url,
                post_vars,
                signature_header
            ):
                raise HTTPException(status_code=401, detail="Invalid Twilio signature")

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