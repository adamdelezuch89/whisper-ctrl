"""
External API Transcriber.

Supports OpenAI-compatible APIs (OpenAI, Groq, Together, etc.)
and Azure AI Foundry via the openai SDK.
"""

import os
import time
import tempfile
from typing import Optional
import numpy as np
import soundfile as sf

from .base import Transcriber, TranscriptionResult, TranscriptionError


class ApiTranscriber(Transcriber):
    """Transcriber using external APIs (OpenAI-compatible or Azure)."""

    def __init__(self, api_type: str = "openai", api_key: str = "",
                 api_url: str = "", model: str = "whisper-1",
                 api_version: str = "2024-10-21"):
        """
        Initialize API transcriber.

        Args:
            api_type: Provider type - "openai" or "azure"
            api_key: API key for authentication
            api_url: Custom base URL (empty = provider default)
            model: Model/deployment name
            api_version: API version (azure only)
        """
        self.api_type = api_type
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.api_version = api_version
        self._client = None

        if not api_key:
            raise TranscriptionError("API key not configured")

        if api_type == "azure" and not api_url:
            raise TranscriptionError("Azure endpoint URL is required")

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the appropriate OpenAI SDK client."""
        try:
            import openai

            if self.api_type == "azure":
                self._client = openai.AzureOpenAI(
                    api_key=self.api_key,
                    azure_endpoint=self.api_url,
                    api_version=self.api_version
                )
                print(f"✅ Azure OpenAI client initialized (endpoint: {self.api_url})")
            else:
                kwargs = {"api_key": self.api_key}
                if self.api_url:
                    kwargs["base_url"] = self.api_url
                self._client = openai.OpenAI(**kwargs)
                url_info = f" (base_url: {self.api_url})" if self.api_url else ""
                print(f"✅ OpenAI client initialized{url_info}")

        except ImportError:
            raise TranscriptionError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        except Exception as e:
            raise TranscriptionError(f"Failed to initialize API client: {e}")

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio using the configured API.

        Args:
            audio_data: Audio samples as numpy array (float32, 16kHz)
            language: Language code (ISO-639-1, e.g., "en", "pl")

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self.is_available():
            raise TranscriptionError("API client is not available")

        if audio_data is None or len(audio_data) == 0:
            raise TranscriptionError("No audio data provided")

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_path = temp_audio.name

            sf.write(temp_path, audio_data.flatten(), 16000, subtype='PCM_16')

            print(f"🌐 Sending audio to {self.get_name()} (language: {language or 'auto'})...")
            start_time = time.time()

            with open(temp_path, "rb") as audio_file:
                kwargs = {
                    "model": self.model,
                    "file": audio_file,
                }
                if language and language != "auto":
                    kwargs["language"] = language

                response = self._client.audio.transcriptions.create(**kwargs)

            try:
                os.unlink(temp_path)
            except OSError:
                pass

            duration = time.time() - start_time
            transcribed_text = response.text.strip()

            print(f"✅ Transcription complete in {duration:.2f}s: '{transcribed_text[:100]}'")

            return TranscriptionResult(
                text=transcribed_text,
                language=language,
                duration=duration
            )

        except Exception as e:
            error_msg = f"API transcription failed: {e}"
            print(f"❌ {error_msg}")
            raise TranscriptionError(error_msg) from e

    def is_available(self) -> bool:
        """Check if API client is initialized."""
        return self._client is not None

    def get_name(self) -> str:
        """Get the name of this transcriber."""
        if self.api_type == "azure":
            return f"Azure AI Foundry ({self.model})"
        if self.api_url:
            return f"OpenAI-compatible API ({self.model})"
        return f"OpenAI API ({self.model})"
