"""
Base Transcriber Interface.

Defines the abstract interface that all transcription backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class TranscriptionResult:
    """Container for transcription results with metadata."""

    def __init__(self, text: str, language: Optional[str] = None,
                 confidence: Optional[float] = None, duration: Optional[float] = None):
        """
        Initialize transcription result.

        Args:
            text: Transcribed text
            language: Detected/used language code
            confidence: Average confidence score (0-1)
            duration: Processing duration in seconds
        """
        self.text = text
        self.language = language
        self.confidence = confidence
        self.duration = duration

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"TranscriptionResult(text='{self.text[:50]}...', language={self.language})"


class Transcriber(ABC):
    """Abstract base class for all transcription backends."""

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Audio samples as numpy array (float32, 16kHz)
            language: Optional language code (e.g., "en", "pl", "auto")

        Returns:
            TranscriptionResult containing the transcribed text and metadata

        Raises:
            TranscriptionError: If transcription fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the transcriber is properly configured and available.

        Returns:
            True if the transcriber can be used, False otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the human-readable name of this transcriber.

        Returns:
            Name of the transcriber backend
        """
        pass


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""
    pass
