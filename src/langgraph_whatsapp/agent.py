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
        except json.JSONDecodeError as e:
            LOGGER.error(f"Failed to parse CONFIG as JSON: {e}")
            raise

    async def invoke(self, id: str, user_message: str, media: dict = None) -> dict:
        """
        Process a user message through the LangGraph client.
        
        Args:
            id: The unique identifier for the conversation
            user_message: The message content from the user
            media: Dictionary with image media data (url and content_type)
            
        Returns:
            dict: The result from the LangGraph run
        """
        print(f"Invoking agent with thread_id: {id}, message: {user_message}")

        try:
            message_content = []

            if user_message:
                message_content.append({
                    "type": "text",
                    "text": user_message
                })

            if media and isinstance(media, dict) and 'url' in media and 'content_type' in media:
                if media['content_type'].startswith('image/'):
                    # Process only images
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": media['url'],
                            "detail": "high"
                        }
                    })
                    print(f"Added image: {media['url']}")
                else:
                    print(f"Ignoring non-image media type: {media['content_type']}")
            
            request_payload = {
                "thread_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, id)),
                "assistant_id": config.ASSISTANT_ID,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": message_content if message_content else user_message
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
            
            print(f"Request payload: {json.dumps(request_payload, indent=2)}")
            
            async for chunk in self.client.runs.stream(
                **request_payload
            ):
                final_response = chunk
            return final_response.data["messages"][-1]["content"]
        except Exception as e:
            print(f"Error during invoke: {str(e)}", exc_info=True)
            raise