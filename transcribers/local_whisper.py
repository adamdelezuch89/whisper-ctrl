"""
Local Whisper Transcriber.

Uses faster-whisper library for local GPU-accelerated transcription.
"""

import time
from typing import Optional
import numpy as np

from faster_whisper import WhisperModel

from .base import Transcriber, TranscriptionResult, TranscriptionError


class LocalWhisperTranscriber(Transcriber):
    """Transcriber using local Whisper model via faster-whisper."""

    def __init__(self, model_size: str = "large-v3",
                 device: str = "cuda",
                 compute_type: str = "float16",
                 vad_enabled: bool = True,
                 vad_parameters: Optional[dict] = None):
        """
        Initialize local Whisper transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v3)
            device: Device to use ("cuda" or "cpu")
            compute_type: Computation precision ("float16", "int8", "float32")
            vad_enabled: Enable Voice Activity Detection filter
            vad_parameters: VAD parameters dict
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.vad_enabled = vad_enabled
        self.vad_parameters = vad_parameters or {
            "threshold": 0.5,
            "min_speech_duration_ms": 250,
            "min_silence_duration_ms": 700,
        }

        self.model: Optional[WhisperModel] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the Whisper model."""
        try:
            print(f"🚀 Loading Whisper model '{self.model_size}' on {self.device}...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            print(f"✅ Whisper model loaded successfully")
        except Exception as e:
            error_msg = f"Failed to load Whisper model: {e}"
            print(f"❌ {error_msg}")
            raise TranscriptionError(error_msg) from e

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio using local Whisper model.

        Args:
            audio_data: Audio samples as numpy array (float32, 16kHz)
            language: Language code (e.g., "en", "pl") or None for auto-detect

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self.is_available():
            raise TranscriptionError("Local Whisper model is not available")

        if audio_data is None or len(audio_data) == 0:
            raise TranscriptionError("No audio data provided")

        try:
            # Ensure audio is float32 and flattened
            audio_float32 = audio_data.astype(np.float32).flatten()

            print(f"🤖 Transcribing with local Whisper (language: {language or 'auto'})...")
            start_time = time.time()

            # Transcribe
            segments, info = self.model.transcribe(
                audio_float32,
                language=language,
                beam_size=5,
                vad_filter=self.vad_enabled,
                vad_parameters=self.vad_parameters if self.vad_enabled else None
            )

            # Collect text from segments
            transcribed_text = "".join(segment.text for segment in segments).strip()
            duration = time.time() - start_time

            detected_language = info.language if hasattr(info, 'language') else language

            print(f"✅ Transcription complete in {duration:.2f}s: '{transcribed_text[:100]}'")

            return TranscriptionResult(
                text=transcribed_text,
                language=detected_language,
                duration=duration
            )

        except Exception as e:
            error_msg = f"Transcription failed: {e}"
            print(f"❌ {error_msg}")
            raise TranscriptionError(error_msg) from e

    def is_available(self) -> bool:
        """Check if the local model is loaded and ready."""
        return self.model is not None

    def get_name(self) -> str:
        """Get the name of this transcriber."""
        return f"Local Whisper ({self.model_size})"
