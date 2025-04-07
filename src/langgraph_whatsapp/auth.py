import logging
from langgraph_sdk import Auth

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

auth = Auth()


@auth.authenticate
async def authenticate(request, path, headers, method):
    # Log the incoming request details
    logger.info(f"Authentication attempt - Path: {path}, Method: {method}")
    logger.info(f"Headers received: {headers}")
    
    user_agent = headers.get(b"user-agent")
    logger.info(f"User-Agent: {user_agent}")
    
    if user_agent and user_agent.startswith(b"Slackbot"):
        logger.info("Authentication successful - Slackbot request authenticated")
        return {"identity": "default-user", "permissions": ["read", "write"]}
    
    logger.warning("Authentication failed - Not a Slackbot request")
    return None
