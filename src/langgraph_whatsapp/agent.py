import logging
from langgraph_sdk import get_client
from langgraph_whatsapp import config
import json
import uuid
import requests
import base64
import mimetypes
from urllib.parse import urlparse, parse_qs

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

            # Check if media is provided and process it
            if media and media.get("url"):
                media_url = media["url"]
                print(f"Processing media URL: {media_url}")

                # Get auth credentials
                auth_token = config.TWILIO_AUTH_TOKEN
                account_sid = config.TWILIO_ACCOUNT_SID
                                
                if not auth_token or not account_sid:
                    print("Warning: TWILIO_AUTH_TOKEN or TWILIO_ACCOUNT_SID not configured, skipping media processing.")
                    # Optionally raise an error or just skip adding the image
                    # raise ValueError("Missing Twilio credentials")
                else:
                    # Download the image directly with auth
                    try:
                        response = requests.get(media_url, auth=(account_sid, auth_token))
                        response.raise_for_status() # Raise an exception for bad status codes
                        img = response.content
                        
                        # Determine the mime type or use image/jpeg as fallback
                        mime = media.get('content_type') or mimetypes.guess_type(media_url)[0] or "image/jpeg"
                        
                        # Convert to data URL
                        data_url = f"data:{mime};base64," + base64.b64encode(img).decode()
                        
                        # Add image as a data URL
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": "high"
                            }
                        })
                    except requests.exceptions.RequestException as req_err:
                        print(f"Failed to download media from {media_url}: {req_err}")
                    except Exception as e:
                        print(f"Error processing media: {e}")

            # Always add the text message content if it exists
            if user_message:
                 message_content.append({
                     "type": "text",
                     "text": user_message
                 })


            request_payload = {
                "thread_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, id)),
                "assistant_id": config.ASSISTANT_ID,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            # Use the constructed message_content (potentially with image and text)
                            "content": message_content 
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