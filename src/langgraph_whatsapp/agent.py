"""
agent.py – fully patched

▪  Converts **every** Twilio /Media/ URL to an inline data‑URI before it ever
  reaches Gemini, so the model no longer tries to re‑download the file (and
  thus never gets a 401).
▪  Replaces the bad `print(..., exc_info=True)` with proper logging so the
  original stack‑trace is preserved.
"""

import asyncio
import base64
import json
import logging
import mimetypes
import os
import uuid
from typing import Any, Dict, List

import requests
from langgraph_sdk import get_client
from langgraph_whatsapp import config

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)  # or DEBUG


# ──────────────────────────────────────────────────────────────────────────────
# Helper ─ turn a Twilio URL into a data URI (once)
# ──────────────────────────────────────────────────────────────────────────────
def twilio_url_to_data_uri(url: str) -> str:
    """Download the Twilio media and return a base‑64 data URI."""
    sid = config.TWILIO_ACCOUNT_SID
    token = config.TWILIO_AUTH_TOKEN
    if not sid or not token:
        raise RuntimeError("Twilio credentials are not configured")

    res = requests.get(url, auth=(sid, token), timeout=15)
    res.raise_for_status()
    mime = mimetypes.guess_type(url)[0] or "image/jpeg"
    data = base64.b64encode(res.content).decode()
    return f"data:{mime};base64,{data}"


def sanitize_parts(parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Replace any Twilio image_url in a single message with a data URI."""
    new_parts = []
    for part in parts:
        if part.get("type") == "image_url":
            img_url = part["image_url"]["url"]
            if img_url.startswith("https://api.twilio.com"):
                try:
                    part["image_url"]["url"] = twilio_url_to_data_uri(img_url)
                except Exception as err:
                    LOGGER.warning("Could not inline %s – skipping (%s)", img_url, err)
                    continue  # drop the part instead of crashing
        new_parts.append(part)
    return new_parts


# ──────────────────────────────────────────────────────────────────────────────
# WhatsApp Agent
# ──────────────────────────────────────────────────────────────────────────────
class Agent:
    def __init__(self):
        self.client = get_client(url=config.LANGGRAPH_URL)
        try:
            self.graph_config = (
                json.loads(config.CONFIG)
                if isinstance(config.CONFIG, str)
                else config.CONFIG
            )
        except json.JSONDecodeError as e:
            LOGGER.exception("CONFIG is not valid JSON")
            raise

    # ──────────────────────────────────────────────────────────────────────
    async def invoke(
        self, id: str, user_message: str, media: Dict[str, str] | None = None
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp text + optional image through the LangGraph assistant.
        Media is always inlined as a data URI before the call.
        """
        thread_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id))
        LOGGER.info("Invoking agent thread=%s", thread_id)

        try:
            # 1) build parts for *this* user turn
            parts: List[Dict[str, Any]] = []

            # -- optional image
            if media and media.get("url"):
                try:
                    data_uri = twilio_url_to_data_uri(media["url"])
                    parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri, "detail": "high"},
                        }
                    )
                except Exception as img_err:
                    LOGGER.warning("Image skipped: %s", img_err)

            # -- user text
            if user_message:
                parts.append({"type": "text", "text": user_message})

            # 2) final payload
            request_payload = {
                "thread_id": thread_id,
                "assistant_id": config.ASSISTANT_ID,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            # ensure no raw Twilio links leak through
                            "content": sanitize_parts(parts),
                        }
                    ]
                },
                "config": self.graph_config,
                "metadata": {"event": "api_call"},
                "multitask_strategy": "interrupt",
                "if_not_exists": "create",
                "stream_mode": "values",
            }

            LOGGER.debug("Payload =>\n%s", json.dumps(request_payload, indent=2))

            # 3) stream the run and return the assistant’s last message
            final = None
            async for chunk in self.client.runs.stream(**request_payload):
                final = chunk

            if not final or "messages" not in final.data:
                raise RuntimeError("Assistant returned no messages")

            return final.data["messages"][-1]["content"]

        except Exception:
            LOGGER.exception("Error during invoke")
            raise
