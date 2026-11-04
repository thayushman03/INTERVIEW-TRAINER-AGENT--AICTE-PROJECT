"""
granite_llm.py
--------------
IBM Granite LLM wrapper using ibm-watsonx-ai SDK.
Provides a unified interface for text generation with IBM Granite models.
"""

import logging
from typing import Optional
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from src.config import (
    IBM_CLOUD_API_KEY,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
    GRANITE_MODEL_ID,
    GRANITE_INSTRUCT_MODEL_ID,
    LLM_MAX_NEW_TOKENS,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_TOP_K,
    LLM_REPETITION_PENALTY,
)

logger = logging.getLogger(__name__)


class GraniteLLM:
    """
    Wrapper around IBM Granite models via WatsonX.ai.

    Usage
    -----
    llm = GraniteLLM()
    response = llm.generate("What is a good answer to 'Tell me about yourself'?")
    """

    def __init__(self, model_id: Optional[str] = None, instruct: bool = False):
        self.model_id = model_id or (
            GRANITE_INSTRUCT_MODEL_ID if instruct else GRANITE_MODEL_ID
        )
        self._client: Optional[APIClient] = None
        self._model: Optional[ModelInference] = None
        self._connect()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        """Initialise the WatsonX API client and model inference object."""
        try:
            credentials = Credentials(
                url=WATSONX_URL,
                api_key=IBM_CLOUD_API_KEY,
            )
            self._client = APIClient(credentials=credentials)
            self._model = ModelInference(
                model_id=self.model_id,
                credentials=credentials,
                project_id=WATSONX_PROJECT_ID,
                params={
                    GenParams.MAX_NEW_TOKENS: LLM_MAX_NEW_TOKENS,
                    GenParams.TEMPERATURE: LLM_TEMPERATURE,
                    GenParams.TOP_P: LLM_TOP_P,
                    GenParams.TOP_K: LLM_TOP_K,
                    GenParams.REPETITION_PENALTY: LLM_REPETITION_PENALTY,
                    GenParams.STOP_SEQUENCES: ["<|endoftext|>", "###"],
                },
            )
            logger.info("Connected to IBM WatsonX with model: %s", self.model_id)
        except Exception as exc:
            logger.error("Failed to connect to WatsonX: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Generate text from a prompt.

        Parameters
        ----------
        prompt      : The input prompt string.
        max_tokens  : Override default max_new_tokens for this call.

        Returns
        -------
        Generated text as a string.
        """
        if self._model is None:
            raise RuntimeError("LLM model not initialised. Call _connect() first.")

        params = {}
        if max_tokens:
            params[GenParams.MAX_NEW_TOKENS] = max_tokens

        try:
            response = self._model.generate_text(
                prompt=prompt,
                params=params if params else None,
            )
            return response.strip() if isinstance(response, str) else str(response)
        except Exception as exc:
            logger.error("Generation error: %s", exc)
            raise

    def chat(self, messages: list[dict]) -> str:
        """
        Chat completion using Granite chat models.

        Parameters
        ----------
        messages : List of {"role": "user"|"assistant"|"system", "content": str}

        Returns
        -------
        Assistant reply as string.
        """
        if self._model is None:
            raise RuntimeError("LLM model not initialised.")

        try:
            response = self._model.chat(messages=messages)
            # Extract the content from the response structure
            if hasattr(response, "choices") and response.choices:
                return response.choices[0].message.content.strip()
            return str(response).strip()
        except Exception as exc:
            # Fall back to generate() if chat() is not supported for this model
            logger.warning("chat() not supported, falling back to generate(): %s", exc)
            prompt = self._messages_to_prompt(messages)
            return self.generate(prompt)

    @staticmethod
    def _messages_to_prompt(messages: list[dict]) -> str:
        """Convert a chat messages list into a flat prompt string."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        parts.append("Assistant:")
        return "\n".join(parts)


# Module-level singleton
_llm_instance: Optional[GraniteLLM] = None


def get_llm(instruct: bool = False) -> GraniteLLM:
    """Return (or create) the module-level GraniteLLM singleton."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = GraniteLLM(instruct=instruct)
    return _llm_instance
