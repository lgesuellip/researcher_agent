from typing import List, Dict
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import os
from langsmith.wrappers import wrap_openai
import logging
from langsmith import traceable


logger = logging.getLogger(__name__)


class OpenAIClientSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            cls._instance = wrap_openai(AsyncOpenAI(api_key=api_key))
        return cls._instance

class Inference:
    def __init__(self):
        self.client = OpenAIClientSingleton.get_instance()

    @traceable
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    async def predict_with_parse_async(self, model_args: Dict, response_format, messages: List[Dict]):
        
        response = await self.client.beta.chat.completions.parse(
                        **model_args,
                        messages=messages,
                        response_format=response_format,
                    )

        return response.choices[0].message.parsed
