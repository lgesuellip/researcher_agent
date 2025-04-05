import logging
from langgraph_sdk import get_client
from langgraph_slack import config
import json

LOGGER = logging.getLogger(__name__)


class Agent:
    def __init__(self):
        self.client = get_client(url=config.LANGGRAPH_URL)
        self.graph_config = (
            json.loads(config.CONFIG) if isinstance(config.CONFIG, str) else config.CONFIG
        )

    async def invoke(self, id: int, user_message: str) -> dict:
        """
        Process a user message through the LangGraph client.
        
        Args:
            user_message: The message content from the user
            
        Returns:
            dict: The result from the LangGraph run
        """
        response = await self.client.runs.create(
            thread_id=str(id),
            assistant_id=config.ASSISTANT_ID,
            input={
                "messages": [
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ]
            },
            config=self.graph_config,
            metadata={
                "event": "api_call",
                "user_message": user_message,
            },
            multitask_strategy="interrupt",
            if_not_exists="create",
        )
        return response["messages"][-1].content