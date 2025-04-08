from os import environ
import logging

LOGGER = logging.getLogger(__name__)

LANGGRAPH_URL = environ.get("LANGGRAPH_URL")
ASSISTANT_ID = environ.get("LANGGRAPH_ASSISTANT_ID", "agent")
CONFIG = environ.get("CONFIG") or "{}"
TWILIO_AUTH_TOKEN = environ.get("TWILIO_AUTH_TOKEN")