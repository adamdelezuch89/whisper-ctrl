"""
Audio Recorder for Whisper-Ctrl.

Handles microphone recording with threading support.
"""

import threading
from typing import Optional, Callable
import numpy as np
import sounddevice as sd


class AudioRecorder:
    """
    Audio recorder with threading support.

    Records audio from the default microphone in a separate thread.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """
        Initialize audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default: 16000 for Whisper)
            channels: Number of audio channels (default: 1 for mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels

        self.recording_thread: Optional[threading.Thread] = None
        self.recording_event = threading.Event()
        self.audio_data: Optional[np.ndarray] = None
        self.cancelled = False

    def start_recording(self, on_error: Optional[Callable[[Exception], None]] = None):
        """
        Start recording in a background thread.

        Args:
            on_error: Optional callback for error handling
        """
        print("🎙️ Starting recording...")
        self.cancelled = False
        self.recording_event.clear()
        self.audio_data = None

        self.recording_thread = threading.Thread(
            target=self._record_audio,
            args=(on_error,),
            daemon=True
        )
        self.recording_thread.start()

    def _record_audio(self, on_error: Optional[Callable[[Exception], None]] = None):
        """
        Internal method to record audio (runs in separate thread).

        Args:
            on_error: Optional callback for error handling
        """
        try:
            frames = []
            print(f"🎤 Recording at {self.sample_rate} Hz...")

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32'
            ) as stream:
                print("🔊 Microphone active. Speak now...")

                while not self.recording_event.is_set():
                    data, _ = stream.read(1024)
                    frames.append(data.copy())

            if self.cancelled:
                self.audio_data = None
                return

            if frames:
                self.audio_data = np.concatenate(frames, axis=0)
                print(f"✅ Recorded {len(self.audio_data)} samples")

        except Exception as e:
            print(f"❌ Error during recording: {e}")
            if on_error:
                on_error(e)

    def stop_recording(self) -> Optional[np.ndarray]:
        """
        Stop recording and return the recorded audio data.

        Returns:
            numpy array with audio data (float32), or None if cancelled/error
        """
        if self.recording_thread and self.recording_thread.is_alive():
            print("🛑 Stopping recording...")
            self.recording_event.set()
            self.recording_thread.join(timeout=2.0)
            self.recording_thread = None

        return self.audio_data

    def cancel_recording(self):
        """Cancel the current recording."""
        print("❌ Recording cancelled")
        self.cancelled = True
        self.recording_event.set()

    def is_recording(self) -> bool:
        """Check if recording is in progress."""
        return (
            self.recording_thread is not None
            and self.recording_thread.is_alive()
        )
