from langgraph_sdk import Auth
from twilio.request_validator import RequestValidator
from langgraph_whatsapp import config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

auth = Auth()

@auth.authenticate
async def authenticate(request, path, headers, method):
    logger.info(f"Authentication request received - Path: {path}, Method: {method}")
    logger.debug(f"Request: {request}")
    logger.debug(f"Headers: {headers}")

    validator = RequestValidator(config.TWILIO_AUTH_TOKEN)

    request_valid = validator.validate(
        request.url,
        request.form,
        request.headers.get('X-TWILIO-SIGNATURE', ''))
    logger.info(f"Request validation result: {request_valid}")

    return None
