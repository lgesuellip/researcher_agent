from typing import Dict, Any
from .agent import Agent

class WhatsAppAgent:
    def __init__(self):
        self.agent = Agent()

    def handle_message(self, message: Dict[str, Any]) -> str:
        """
        Entrypoint for handling incoming WhatsApp messages.
        
        :param message: A dictionary containing message details
        :return: Response to be sent back to the user
        """

        sender = message.get('from')
        content = message.get('text')

        response = self._process_message(sender, content)

        return response

    def _process_message(self, sender: str, content: str) -> str:
        """
        Process the incoming message and generate a response.
        
        :param sender: The sender's identifier
        :param content: The content of the message
        :return: Response to be sent back to the user
        """
        return self.agent.invoke(id=sender, message=content)