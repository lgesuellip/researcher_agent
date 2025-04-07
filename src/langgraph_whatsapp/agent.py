import logging
from langgraph_sdk import get_client
from langgraph_whatsapp import config
import json
import uuid

LOGGER = logging.getLogger(__name__)


class Agent:
    def __init__(self):
        LOGGER.info(f"Initializing Agent with LANGGRAPH_URL: {config.LANGGRAPH_URL}")
        LOGGER.info(f"ASSISTANT_ID: {config.ASSISTANT_ID}")
        LOGGER.info(f"Raw CONFIG: {config.CONFIG}")
        
        self.client = get_client(url=config.LANGGRAPH_URL)
        try:
            self.graph_config = (
                json.loads(config.CONFIG) if isinstance(config.CONFIG, str) else config.CONFIG
            )
            LOGGER.info(f"Parsed graph_config: {self.graph_config}")
        except json.JSONDecodeError as e:
            LOGGER.error(f"Failed to parse CONFIG as JSON: {e}")
            raise

    async def invoke(self, id: int, user_message: str) -> dict:
        """
        Process a user message through the LangGraph client.
        
        Args:
            user_message: The message content from the user
            
        Returns:
            dict: The result from the LangGraph run
        """
        LOGGER.info(f"Invoking agent with thread_id: {id}, message: {user_message}")

        try:
            request_payload = {
                "thread_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"PHONE:{id}")),
                "assistant_id": "agent",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": 'hi',
                        }
                    ]
                },
                "config": self.graph_config,
                "metadata": {
                    "event": "api_call",
                    "user_message": 'hi',
                },
                "multitask_strategy": "interrupt",
                "if_not_exists": "create",
            }
            LOGGER.info(f"Request payload: {json.dumps(request_payload, indent=2)}")
            
            response = await self.client.runs.create(**request_payload)
            LOGGER.info(f"Received response: {json.dumps(response, indent=2)}")
            
            return response["messages"][-1].content
        except Exception as e:
            LOGGER.error(f"Error during invoke: {str(e)}", exc_info=True)
            raise