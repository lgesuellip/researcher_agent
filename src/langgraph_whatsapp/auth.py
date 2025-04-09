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
    
    # Reconstruct the full URL (assuming HTTPS and presence of 'host' header)
    scheme = headers.get("x-forwarded-proto", "https")
    host = headers.get("host")
    if not host:
        raise auth.exceptions.HTTPException(status_code=400, detail="Missing Host header")
    url = f"{scheme}://{host}{path}"
    
    # Await and extract form data (application/x-www-form-urlencoded)
    form_data = await request.form()
    
    # Get the Twilio signature from headers (case-insensitive)
    signature = headers.get("x-twilio-signature")
    if not signature:
        raise auth.exceptions.HTTPException(status_code=401, detail="Missing Twilio signature")
    
    # Validate the request using Twilio's RequestValidator
    validator = RequestValidator(config.TWILIO_AUTH_TOKEN)
    if not validator.validate(url, form_data, signature):
        raise auth.exceptions.HTTPException(status_code=401, detail="Invalid Twilio signature")
    
    # If valid, extract user info from form data (e.g., sender phone number)
    user_identity = form_data.get("From")
    if not user_identity:
        raise auth.exceptions.HTTPException(status_code=401, detail="Missing sender information")
    
    return None
