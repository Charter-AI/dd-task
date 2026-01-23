"""Structured outputs helpers for LLM calls.

This module provides utilities for calling the LLM with structured outputs
using JSON Schema, ensuring the response matches the expected format.
"""

import json
import time
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from ascentra_agent.config import settings
from ascentra_agent.llm.azure_client import get_client

T = TypeVar("T", bound=BaseModel)


def chat_structured(
    messages: list[dict[str, str]],
    schema_name: str,
    schema: dict[str, Any],
    model_deployment: Optional[str] = None,
    temperature: Optional[float] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Call the LLM with a JSON schema for structured output.

    Uses Azure OpenAI's structured outputs feature with response_format
    set to json_schema with strict: true.

    Args:
        messages: List of chat messages
        schema_name: Name for the schema
        schema: JSON Schema dict
        model_deployment: Azure deployment name (defaults to settings)
        temperature: Temperature for generation (defaults to settings)

    Returns:
        Tuple of (parsed JSON response, trace info)
    """
    client = get_client()
    deployment = model_deployment or settings.AZURE_OPENAI_DEPLOYMENT
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

    start_time = time.time()

    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=temp,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": False,  # Disabled due to Azure OpenAI limitations with discriminated unions
                "schema": schema,
            },
        },
    )

    elapsed = time.time() - start_time

    # Parse the response
    content = response.choices[0].message.content
    parsed = json.loads(content)

    # Build trace info
    trace = {
        "model": deployment,
        "temperature": temp,
        "latency_s": round(elapsed, 3),
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        },
        "finish_reason": response.choices[0].finish_reason,
    }

    return parsed, trace


def chat_structured_pydantic(
    messages: list[dict[str, str]],
    model: Type[T],
    model_deployment: Optional[str] = None,
    temperature: Optional[float] = None,
) -> tuple[T, dict[str, Any]]:
    """Call the LLM with a Pydantic model schema for structured output.

    This is a convenience wrapper that:
    1. Extracts the JSON schema from the Pydantic model
    2. Calls the LLM with structured output
    3. Validates and returns the parsed model instance

    Args:
        messages: List of chat messages
        model: Pydantic model class to use for the schema
        model_deployment: Azure deployment name (defaults to settings)
        temperature: Temperature for generation (defaults to settings)

    Returns:
        Tuple of (validated model instance, trace info)
    """
    schema = model.model_json_schema()
    parsed, trace = chat_structured(
        messages=messages,
        schema_name=model.__name__,
        schema=schema,
        model_deployment=model_deployment,
        temperature=temperature,
    )

    # Validate and create model instance
    instance = model.model_validate(parsed)

    return instance, trace


def build_messages(
    system_prompt: str,
    user_content: str,
    examples: Optional[list[tuple[str, str]]] = None,
) -> list[dict[str, str]]:
    """Build a message list for chat completion.

    Args:
        system_prompt: The system prompt
        user_content: The user message content
        examples: Optional list of (user, assistant) example pairs

    Returns:
        List of message dicts for the API
    """
    messages = [{"role": "system", "content": system_prompt}]

    if examples:
        for user_example, assistant_example in examples:
            messages.append({"role": "user", "content": user_example})
            messages.append({"role": "assistant", "content": assistant_example})

    messages.append({"role": "user", "content": user_content})

    return messages
