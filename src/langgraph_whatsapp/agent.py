import logging
from langgraph_sdk import get_client
from langgraph_whatsapp import config
import json
import uuid

LOGGER = logging.getLogger(__name__)


class Agent:
    def __init__(self):
        
        self.client = get_client(url=config.LANGGRAPH_URL)
        try:
            self.graph_config = (
                json.loads(config.CONFIG) if isinstance(config.CONFIG, str) else config.CONFIG
            )
            LOGGER.info(f"Parsed graph_config: {self.graph_config}")
        except json.JSONDecodeError as e:
            LOGGER.error(f"Failed to parse CONFIG as JSON: {e}")
            raise

    async def invoke(self, id: str, user_message: str) -> dict:
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
                "thread_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, id)),
                "assistant_id": config.ASSISTANT_ID,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    ]
                },
                "config": self.graph_config,
                "metadata": {
                    "event": "api_call",
                },
                "multitask_strategy": "interrupt",
                "if_not_exists": "create",
                "stream_mode": "values",
            }
            
            async for chunk in self.client.runs.stream(
                **request_payload
            ):
                LOGGER.info(f"Chunk: {chunk}")
                final_response = chunk
                # Optionally print chunks for debugging
                print(chunk)
            print(final_response)
            return final_response["messages"][-1]["content"]
        except Exception as e:
            LOGGER.error(f"Error during invoke: {str(e)}", exc_info=True)
            raise