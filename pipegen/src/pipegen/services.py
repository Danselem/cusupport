"""Service factory for creating Pipecat services."""

import os

from pipecat.services.google.gemini_live.llm import (
    GeminiLiveLLMService,
    GeminiVADParams,
)

from pipegen.prompts import CUSTOMER_SERVICE_PROMPT


def create_llm_service() -> GeminiLiveLLMService:
    """Create and return a Gemini Live LLM service."""
    return GeminiLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY", ""),
        settings=GeminiLiveLLMService.Settings(
            model="models/gemini-2.5-flash-native-audio-preview-12-2025",
            voice="Charon",
            system_instruction=CUSTOMER_SERVICE_PROMPT,
            temperature=0.7,
            max_tokens=2048,
            language="en-US",
            vad=GeminiVADParams(
                silence_duration_ms=500,
            ),
        ),
    )
