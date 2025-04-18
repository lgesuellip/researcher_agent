from fastapi import FastAPI, Request, Response, HTTPException
from langgraph_whatsapp.channel import WhatsAppAgentTwilio
import logging

APP = FastAPI()
WSP_AGENT = WhatsAppAgentTwilio()


# twilio_middleware.pyxs
from starlette.middleware.base import BaseHTTPMiddleware
from twilio.request_validator import RequestValidator
from src.langgraph_whatsapp.config import TWILIO_AUTH_TOKEN

from urllib.parse import parse_qs

class TwilioSignatureMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, path: str = "/whatsapp"):
        super().__init__(app)
        self.path = path
        self.validator = RequestValidator(TWILIO_AUTH_TOKEN)

    async def dispatch(self, request, call_next):
        if request.url.path == self.path and request.method.upper() == "POST":
            # ❶ Read the raw body ONCE
            raw = await request.body()

            # ❷ Validate the signature
            form_dict = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
            forwarded_proto = request.headers.get("x-forwarded-proto", "http")
            forwarded_host  = request.headers.get("x-forwarded-host",
                                                  request.headers.get("host"))
            url = f"{forwarded_proto}://{forwarded_host}{request.url.path}"
            sig = request.headers.get("X-Twilio-Signature", "")

            if not self.validator.validate(url, form_dict, sig):
                return Response(status_code=401, content="Invalid signature")

            # ❸ Put the body back so downstream can read it again
            request._body = raw        # ✨ Starlette’s accepted rewind trick
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