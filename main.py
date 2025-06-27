#!/usr/bin/env python3
"""
Whisper-Ctrl - A voice dictation tool for Linux with a local Whisper model.

This script implements an application that listens for global keyboard shortcuts,
records audio from the microphone, transcribes it using a local, GPU-accelerated
Whisper model (via faster-whisper), and pastes the result at the cursor's location.

Feedback is displayed in the terminal where the script was launched. Startup
status is also shown via desktop notifications.
"""

import os
import time
import enum
import signal
import threading
import subprocess
from typing import Optional

import numpy as np
import sounddevice as sd
from pynput import keyboard
from faster_whisper import WhisperModel

# --- Local Whisper Model Configuration ---
WHISPER_MODEL_SIZE = "large-v3"
WHISPER_COMPUTE_TYPE = "float16"
LANGUAGE = "pl" # Language for transcription, e.g., "en", "pl", "de"

# --- Voice Activity Detection (VAD) Filter Configuration ---
ENABLE_VAD_FILTER = True
VAD_PARAMETERS = {
    "threshold": 0.5,
    "min_speech_duration_ms": 250,
    "min_silence_duration_ms": 700,
}

# --- Application Configuration ---
WHISPER_SAMPLE_RATE = 16000 # Target sample rate for the Whisper model
DOUBLE_TAP_THRESHOLD_S = 0.4


class State(enum.Enum):
    """Possible application states."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


class WhisperCtrl:
    """The main class for the Whisper-Ctrl application."""

    def __init__(self, model_size: str, compute_type: str):
        self.state = State.IDLE
        self.last_ctrl_press_time = 0
        self.recording_thread: Optional[threading.Thread] = None
        self.recording_event = threading.Event()
        self.stop_event = threading.Event()
        self.audio_data: Optional[np.ndarray] = None
        self.cancelled = False  # Flag to track if current operation was cancelled

        print("🚀 Initializing Whisper model... (this may take a moment on the first run)")
        self.send_notification("Whisper-Ctrl", "Starting Whisper model... (this may take a moment on the first run)")
        try:
            self.model = WhisperModel(model_size, device="cuda", compute_type=compute_type)
            print(f"✅ Model '{model_size}' loaded successfully onto the GPU.")
            self.send_notification("Whisper-Ctrl Ready", f"Model '{model_size}' has been loaded.")
        except Exception as e:
            error_msg = f"CRITICAL ERROR: Failed to load the model on the GPU. {e}"
            print(f"❌ {error_msg}")
            print("   Make sure you have PyTorch with CUDA support and the appropriate NVIDIA drivers installed.")
            self.send_notification("Whisper-Ctrl Error", "Failed to load the model on the GPU.")
            exit(1)

        signal.signal(signal.SIGINT, self.handle_sigint)
        signal.signal(signal.SIGTERM, self.handle_sigint)

    def send_notification(self, title: str, message: str):
        """Sends a desktop notification. Requires 'notify-send' to be installed."""
        try:
            subprocess.run(['notify-send', '-a', 'Whisper-Ctrl', '-i', 'audio-input-microphone', title, message], check=False, timeout=2)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # If notify-send is not installed or times out, do nothing.
            pass

    def handle_sigint(self, signum, frame):
        print("\n🛑 Stopping Whisper-Ctrl application...")
        self.stop_event.set()
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_event.set()
            self.recording_thread.join(timeout=1.0)
        exit(0)

    def on_ctrl_press(self):
        current_time = time.monotonic()
        time_diff = current_time - self.last_ctrl_press_time
        self.last_ctrl_press_time = current_time
        if time_diff < DOUBLE_TAP_THRESHOLD_S:
            self.handle_double_tap()

    def handle_escape(self):
        """Handle Escape key press to cancel current operation."""
        if self.state == State.RECORDING:
            print("❌ Recording cancelled by user (Escape pressed)")
            self.cancelled = True
            self.recording_event.set()  # Stop recording
            self.state = State.IDLE
        elif self.state == State.PROCESSING:
            print("❌ Processing cancelled by user (Escape pressed)")
            self.cancelled = True
            self.state = State.IDLE  # Reset state immediately to allow new operations

    def setup_keyboard_listener(self):
        def on_press(key):
            if key in {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
                self.on_ctrl_press()
            elif key == keyboard.Key.esc:
                self.handle_escape()
        return keyboard.Listener(on_press=on_press)

    def handle_double_tap(self):
        if self.state == State.PROCESSING:
            print("⏳ Please wait, the previous recording is still being processed.")
            return

        if self.state == State.IDLE:
            self.state = State.RECORDING
            self.start_recording()
        elif self.state == State.RECORDING:
            self.state = State.PROCESSING
            self.stop_recording()
            print("🧠 Processing...")
            threading.Thread(target=self.process_audio, daemon=True).start()

    def start_recording(self):
        print("🎙️ Starting recording...")
        self.cancelled = False  # Reset cancelled flag for new operation
        self.recording_event.clear()
        self.audio_data = None
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()

    def record_audio(self):
        try:
            frames = []
            # We force recording at the target frequency of 16000 Hz,
            # which eliminates resampling issues.
            print(f"🎤 Attempting to record directly at {WHISPER_SAMPLE_RATE} Hz...")
            with sd.InputStream(samplerate=WHISPER_SAMPLE_RATE, channels=1, dtype='float32') as stream:
                print("🔊 Microphone active. Speak now...")
                while not self.recording_event.is_set():
                    data, _ = stream.read(1024)
                    frames.append(data.copy())

            # Check if recording was cancelled
            if self.cancelled:
                self.audio_data = None
                return

            if frames:
                self.audio_data = np.concatenate(frames, axis=0)

        except Exception as e:
            print(f"❌ Error during recording: {e}")
            print("   Check if your microphone supports recording at 16000 Hz.")
            self.state = State.IDLE

    def stop_recording(self):
        if self.recording_thread and self.recording_thread.is_alive():
            print("🛑 Stopping recording...")
            self.recording_event.set()
            self.recording_thread.join()
            self.recording_thread = None

    def process_audio(self):
        if self.audio_data is None or len(self.audio_data) == 0:
            print("❌ No audio data to process.")
            self.state = State.IDLE
            return

        try:
            # Check if operation was cancelled before processing
            if self.cancelled:
                print("❌ Processing cancelled, skipping transcription.")
                self.state = State.IDLE
                return

            # Since we are recording at 16kHz, no resampling is needed.
            audio_float32 = self.audio_data.flatten()

            print("🤖 Starting local transcription...")
            segments_generator, _ = self.model.transcribe(
                audio_float32,
                language=LANGUAGE,
                beam_size=5,
                vad_filter=ENABLE_VAD_FILTER,
                vad_parameters=VAD_PARAMETERS
            )

            # Iterate through segments and check for cancellation after each one
            transcribed_segments = []
            for segment in segments_generator:
                # Check if operation was cancelled during transcription
                if self.cancelled:
                    print("❌ Processing was cancelled during transcription.")
                    self.state = State.IDLE
                    return
                transcribed_segments.append(segment)

            transcribed_text = "".join(segment.text for segment in transcribed_segments).strip()

            print(f"✅ Received transcription: '{transcribed_text}'")
            if transcribed_text:
                # Final check for cancellation before pasting
                if self.cancelled:
                    print("❌ Text injection cancelled (operation was cancelled)")
                    return
                self.inject_text(transcribed_text)
            else:
                print("📝 Received an empty transcription, skipping paste.")

        except Exception as e:
            print(f"❌ Error during audio processing: {e}")
        finally:
            self.state = State.IDLE
            self.audio_data = None
            self.cancelled = False  # Reset cancelled flag for clean state

    def inject_text(self, text: str):
        try:
            session_type = os.getenv('XDG_SESSION_TYPE', '').lower()
            if session_type == 'wayland':
                subprocess.run(['wl-copy', text], text=True, check=True)
                subprocess.run(['wtype', '-M', 'shift', '-P', 'insert', '-m', 'shift'], check=True)
            else:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text, text=True, check=True)
                subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+v'], check=True)
            print("✅ Text pasted successfully.")
        except FileNotFoundError as e:
            error_msg = f"Missing tool: {e.filename}. Please check if it's installed."
            print(f"❌ {error_msg}")
        except Exception as e:
            print(f"❌ Error while pasting text: {e}")

    def run(self):
        print("🚀 Starting Whisper-Ctrl in local mode...")
        print("👂 Listening for a double-press of the Ctrl key...")
        print("🚪 Press Escape to cancel recording or processing...")
        print("ℹ️ Press Ctrl+C to exit.")

        listener = self.setup_keyboard_listener()
        listener.start()

        try:
            self.stop_event.wait()
        except KeyboardInterrupt:
            self.handle_sigint(None, None)
        finally:
            listener.stop()

if __name__ == "__main__":
    app = WhisperCtrl(model_size=WHISPER_MODEL_SIZE, compute_type=WHISPER_COMPUTE_TYPE)
    app.run()