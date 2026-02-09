"""
OpenAI API Transcriber.

Uses OpenAI's Whisper API for cloud-based transcription.
"""

import time
import tempfile
from typing import Optional
import numpy as np
import soundfile as sf

from .base import Transcriber, TranscriptionResult, TranscriptionError


class OpenAITranscriber(Transcriber):
    """Transcriber using OpenAI Whisper API."""

    def __init__(self, api_key: str, model: str = "whisper-1"):
        """
        Initialize OpenAI API transcriber.

        Args:
            api_key: OpenAI API key
            model: Model name (default: "whisper-1")
        """
        self.api_key = api_key
        self.model = model
        self._client = None

        if not api_key or not api_key.startswith("sk-"):
            raise TranscriptionError("Invalid OpenAI API key")

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
            print("✅ OpenAI client initialized")
        except ImportError:
            raise TranscriptionError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        except Exception as e:
            raise TranscriptionError(f"Failed to initialize OpenAI client: {e}")

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio using OpenAI API.

        Args:
            audio_data: Audio samples as numpy array (float32, 16kHz)
            language: Language code (ISO-639-1, e.g., "en", "pl")

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self.is_available():
            raise TranscriptionError("OpenAI API is not available")

        if audio_data is None or len(audio_data) == 0:
            raise TranscriptionError("No audio data provided")

        try:
            # Convert numpy array to WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_path = temp_audio.name

            # Write audio data to WAV file (soundfile handles float32 natively)
            sf.write(temp_path, audio_data.flatten(), 16000, subtype='PCM_16')

            print(f"🌐 Sending audio to OpenAI API (language: {language or 'auto'})...")
            start_time = time.time()

            # Prepare API request parameters
            with open(temp_path, "rb") as audio_file:
                kwargs = {
                    "model": self.model,
                    "file": audio_file,
                }

                # Add language parameter if specified
                if language and language != "auto":
                    kwargs["language"] = language

                # Call OpenAI API
                response = self._client.audio.transcriptions.create(**kwargs)

            # Clean up temp file
            import os
            try:
                os.unlink(temp_path)
            except:
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
            error_msg = f"OpenAI API transcription failed: {e}"
            print(f"❌ {error_msg}")
            raise TranscriptionError(error_msg) from e

    def is_available(self) -> bool:
        """Check if OpenAI client is initialized."""
        return self._client is not None

    def get_name(self) -> str:
        """Get the name of this transcriber."""
        return f"OpenAI API ({self.model})"
