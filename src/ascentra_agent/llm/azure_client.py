"""AzureOpenAI client wrapper.

This module provides a wrapper around the OpenAI Python SDK's Azure client,
following the patterns from the OpenAI cookbook for Azure integration.
"""

from typing import Optional

from openai import AzureOpenAI

from ascentra_agent.config import settings

# Global client instance (lazy initialization)
_client: Optional[AzureOpenAI] = None


def build_client() -> AzureOpenAI:
    """Build a new AzureOpenAI client instance.

    This follows the OpenAI cookbook pattern for Azure client construction:
    - azure_endpoint: The Azure OpenAI resource endpoint
    - api_key: The API key for authentication
    - api_version: The API version to use

    Returns:
        Configured AzureOpenAI client instance
    """
    return AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        timeout=settings.LLM_TIMEOUT_S,
    )


def get_client() -> AzureOpenAI:
    """Get the shared AzureOpenAI client instance.

    Uses lazy initialization to create the client on first use.

    Returns:
        Shared AzureOpenAI client instance
    """
    global _client
    if _client is None:
        _client = build_client()
    return _client


def reset_client() -> None:
    """Reset the shared client instance.

    Useful for testing or when configuration changes.
    """
    global _client
    _client = None
