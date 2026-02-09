"""
Application State for Whisper-Ctrl.

Defines the possible states of the application.
"""

import enum


class State(enum.Enum):
    """Possible application states."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
