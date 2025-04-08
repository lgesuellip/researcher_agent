from langgraph_sdk import Auth
from twilio.request_validator import RequestValidator
from langgraph_whatsapp import config

auth = Auth()

@auth.authenticate
async def authenticate(request, path, headers, method):

    print(request)
    print(path)
    print(headers)
    print(method)

    validator = RequestValidator(config.TWILIO_AUTH_TOKEN)

    request_valid = validator.validate(
        request.url,
        request.form,
        request.headers.get('X-TWILIO-SIGNATURE', ''))
    print(request_valid)

    return None
