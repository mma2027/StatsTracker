"""
Anthropic Claude API client for semantic search query translation.
"""

import json
import logging
import os
from typing import Dict, Optional

try:
    from anthropic import Anthropic, APIError, APITimeoutError
except ImportError:
    # Will be caught when trying to use the client
    Anthropic = None
    APIError = Exception
    APITimeoutError = Exception

from .prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, QUERY_SCHEMA

logger = logging.getLogger(__name__)


class AnthropicClient:
    """
    Handles Claude API calls with structured output for semantic search.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        config: Optional[Dict] = None,
    ):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to config.yaml llm.api_key)
            model: Claude model to use (defaults to config.yaml llm.model)
            timeout: Request timeout in seconds (defaults to config.yaml llm.timeout)
            max_tokens: Maximum tokens in response (defaults to config.yaml llm.max_tokens)
            temperature: Sampling temperature (defaults to config.yaml llm.temperature)
            config: Configuration dict from config.yaml (optional)
        """
        if Anthropic is None:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        # Read from config.yaml first, then fall back to defaults
        llm_config = (config or {}).get("llm", {})
        self.api_key = api_key or llm_config.get("api_key")
        if not self.api_key:
            raise ValueError("Anthropic API key not found in config.yaml llm.api_key")

        self.model = model or llm_config.get("model", "claude-3-haiku-20240307")
        timeout_val = timeout if timeout is not None else llm_config.get("timeout", 10)
        self.max_tokens = max_tokens if max_tokens is not None else llm_config.get("max_tokens", 1024)
        self.temperature = temperature if temperature is not None else llm_config.get("temperature", 0.1)

        self.client = Anthropic(api_key=self.api_key, timeout=timeout_val)

        logger.info(f"Initialized Anthropic client with model: {self.model}")

    def query_to_structured_search(self, query: str, retry_count: int = 1) -> Dict:
        """
        Convert natural language query to structured search parameters.

        Args:
            query: Natural language query from user
            retry_count: Number of retries on failure

        Returns:
            Structured query dict with keys:
            - intent: Query type (rank_by_stat, filter_threshold, etc.)
            - sport: Sport filter
            - stat_name: Statistic name
            - filters: Additional filters (season, min/max values, etc.)
            - ordering: DESC or ASC
            - limit: Max results
            - interpretation: Human-readable explanation

        Raises:
            APIError: If API call fails after retries
            ValueError: If response cannot be parsed as valid JSON
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Limit query length to prevent abuse
        query = query.strip()[:200]

        user_prompt = USER_PROMPT_TEMPLATE.format(query=query)

        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Calling Claude API for query: {query[:50]}...")

                # Call Claude with tool/function calling for structured output
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                    tools=[
                        {
                            "name": "structured_search_query",
                            "description": "Convert natural language query to structured search parameters",
                            "input_schema": QUERY_SCHEMA,
                        }
                    ],
                    tool_choice={"type": "tool", "name": "structured_search_query"},
                )

                # Extract tool use result
                for block in response.content:
                    if block.type == "tool_use" and block.name == "structured_search_query":
                        result = block.input
                        logger.info(f"Claude interpretation: {result.get('interpretation', 'N/A')}")
                        logger.debug(f"Full structured output: {json.dumps(result, indent=2)}")

                        # Validate required fields
                        if "intent" not in result or "interpretation" not in result:
                            raise ValueError("Response missing required fields: intent or interpretation")

                        # Set defaults
                        result.setdefault("ordering", "DESC")
                        result.setdefault("limit", 20)
                        result.setdefault("filters", {})

                        # Default season to Career if not specified
                        if "season" not in result.get("filters", {}):
                            result["filters"]["season"] = "Career"

                        return result

                # If no tool use found in response
                raise ValueError("Claude did not return structured output. Response: " + str(response.content))

            except APITimeoutError as e:
                logger.error(f"Claude API timeout (attempt {attempt + 1}/{retry_count + 1}): {e}")
                if attempt >= retry_count:
                    raise
                continue

            except APIError as e:
                logger.error(f"Claude API error (attempt {attempt + 1}/{retry_count + 1}): {e}")
                if attempt >= retry_count:
                    raise
                continue

            except Exception as e:
                logger.error(f"Unexpected error in Claude API call: {e}")
                raise

        # Should not reach here
        raise APIError("Failed to get response from Claude after retries")

    def is_available(self) -> bool:
        """
        Check if the Claude API is available and configured.

        Returns:
            True if API key is set and anthropic package is available
        """
        return Anthropic is not None and self.api_key is not None and len(self.api_key) > 0
