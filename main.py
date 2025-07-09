#!/usr/bin/env python3
"""
Whisper-Ctrl - A voice dictation tool for Linux with a local Whisper model.

This script implements an application that listens for global keyboard shortcuts,
records audio from the microphone, transcribes it using a local, GPU-accelerated
Whisper model (via faster-whisper), and pastes the result at the cursor's location.

Visual feedback is provided via a PyQt6 overlay widget that follows the cursor,
displaying the application's status (recording, processing, idle).
"""

import os
import sys
import time
import enum
import math
import signal
import threading
import subprocess
from typing import Optional

import numpy as np
import sounddevice as sd
from pynput import keyboard
from faster_whisper import WhisperModel

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QPointF

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


class FeedbackWidget(QWidget):
    """A frameless, transparent widget that displays feedback next to the cursor."""

    class Mode(enum.Enum):
        HIDDEN = "hidden"
        RECORDING = "recording"
        PROCESSING = "processing"

    def __init__(self):
        super().__init__()
        self.mode = self.Mode.HIDDEN
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Prevents showing up in the taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.setFixedSize(40, 40)

        # --- POPRAWKA ---
        # Zmniejszenie offsetu, aby wskaźnik był bliżej kursora.
        self.cursor_offset_x = 2
        self.cursor_offset_y = 2

        # For recording animation (pulsing)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update)
        self.pulse_radius = 5
        self.pulse_direction = 1

        # For processing animation (spinning)
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self.update)
        self.spinner_angle = 0

    def show_recording(self):
        self.spinner_timer.stop()
        self.mode = self.Mode.RECORDING
        if not self.pulse_timer.isActive():
            self.pulse_timer.start(50) # Pulse speed
        self.show()

    def show_processing(self):
        self.pulse_timer.stop()
        self.mode = self.Mode.PROCESSING
        if not self.spinner_timer.isActive():
            self.spinner_timer.start(15) # Spinner speed
        self.show()

    def hide_feedback(self):
        self.mode = self.Mode.HIDDEN
        self.pulse_timer.stop()
        self.spinner_timer.stop()
        self.hide()

    def follow_cursor(self):
        if self.isVisible():
            pos = QCursor.pos()
            # Przesuwamy widżet o zdefiniowany offset względem kursora.
            self.move(pos.x() + self.cursor_offset_x, pos.y() + self.cursor_offset_y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.mode == self.Mode.RECORDING:
            # Pulsing red circle
            self.pulse_radius += 0.2 * self.pulse_direction
            if not 5 <= self.pulse_radius <= 8:
                self.pulse_direction *= -1
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 0, 0, 200)) # Red, semi-transparent
            center = QPointF(self.width() / 2, self.height() / 2)
            painter.drawEllipse(center, self.pulse_radius, self.pulse_radius)

        elif self.mode == self.Mode.PROCESSING:
            # Spinning arc
            self.spinner_angle = (self.spinner_angle + 6) % 360
            pen = QPen(QColor(0, 120, 255, 220))
            pen.setWidth(4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            rect = self.rect().adjusted(10, 10, -10, -10)
            painter.drawArc(rect, self.spinner_angle * 16, 90 * 16)

class WhisperCtrl(QObject):
    """The main class for the Whisper-Ctrl application. Now a QObject."""
    state_changed = pyqtSignal(State)

    def __init__(self, model_size: str, compute_type: str):
        super().__init__()
        self.state = State.IDLE
        self.last_ctrl_press_time = 0
        self.recording_thread: Optional[threading.Thread] = None
        self.recording_event = threading.Event()
        self.stop_event = threading.Event()
        self.audio_data: Optional[np.ndarray] = None
        self.cancelled = False  # Flag to track if current operation was cancelled
        self.listener: Optional[keyboard.Listener] = None

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
        QApplication.quit()

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
            self.state_changed.emit(self.state)
        elif self.state == State.PROCESSING:
            print("❌ Processing cancelled by user (Escape pressed)")
            self.cancelled = True
            self.state = State.IDLE  # Reset state immediately to allow new operations
            self.state_changed.emit(self.state)

    def setup_keyboard_listener(self):
        def on_press(key):
            if key in {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
                self.on_ctrl_press()
            elif key == keyboard.Key.esc:
                self.handle_escape()
        self.listener = keyboard.Listener(on_press=on_press)
        return self.listener

    def handle_double_tap(self):
        if self.state == State.PROCESSING:
            print("⏳ Please wait, the previous recording is still being processed.")
            return

        if self.state == State.IDLE:
            self.state = State.RECORDING
            self.state_changed.emit(self.state)
            self.start_recording()
        elif self.state == State.RECORDING:
            self.state = State.PROCESSING
            self.state_changed.emit(self.state)
            self.stop_recording()
            print("🧠 Processing...")
            threading.Thread(target=self.process_audio, daemon=True).start()

    def start_recording(self):
        print("🎙️ Starting recording...")
        self.cancelled = False
        self.recording_event.clear()
        self.audio_data = None
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()

    def record_audio(self):
        try:
            frames = []
            print(f"🎤 Attempting to record directly at {WHISPER_SAMPLE_RATE} Hz...")
            with sd.InputStream(samplerate=WHISPER_SAMPLE_RATE, channels=1, dtype='float32') as stream:
                print("🔊 Microphone active. Speak now...")
                while not self.recording_event.is_set():
                    data, _ = stream.read(1024)
                    frames.append(data.copy())
            if self.cancelled:
                self.audio_data = None
                return
            if frames:
                self.audio_data = np.concatenate(frames, axis=0)
        except Exception as e:
            print(f"❌ Error during recording: {e}")
            self.state = State.IDLE
            self.state_changed.emit(self.state)

    def stop_recording(self):
        if self.recording_thread and self.recording_thread.is_alive():
            print("🛑 Stopping recording...")
            self.recording_event.set()
            self.recording_thread.join()
            self.recording_thread = None

    def process_audio(self):
        if self.audio_data is None or len(self.audio_data) == 0:
            print("❌ No audio data to process.")
        else:
            try:
                if self.cancelled:
                    print("❌ Processing cancelled, skipping transcription.")
                else:
                    audio_float32 = self.audio_data.flatten()
                    print("🤖 Starting local transcription...")
                    segments, _ = self.model.transcribe(audio_float32, language=LANGUAGE, beam_size=5, vad_filter=ENABLE_VAD_FILTER, vad_parameters=VAD_PARAMETERS)
                    transcribed_text = "".join(s.text for s in segments).strip()
                    print(f"✅ Received transcription: '{transcribed_text}'")
                    if transcribed_text and not self.cancelled:
                        self.inject_text(transcribed_text)
                    else:
                        print("📝 Received an empty transcription, skipping paste.")
            except Exception as e:
                print(f"❌ Error during audio processing: {e}")
        
        # Finally block equivalent
        self.state = State.IDLE
        self.state_changed.emit(self.state)
        self.audio_data = None
        self.cancelled = False

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    whisper_ctrl = WhisperCtrl(model_size=WHISPER_MODEL_SIZE, compute_type=WHISPER_COMPUTE_TYPE)
    feedback_widget = FeedbackWidget()

    # --- Controller Logic ---
    def on_state_changed(state: State):
        if state == State.RECORDING:
            feedback_widget.show_recording()
        elif state == State.PROCESSING:
            feedback_widget.show_processing()
        else: # IDLE
            feedback_widget.hide_feedback()

    whisper_ctrl.state_changed.connect(on_state_changed)

    # Timer to move the widget with the cursor
    mouse_follower_timer = QTimer()
    mouse_follower_timer.setInterval(16)  # ~60 FPS
    mouse_follower_timer.timeout.connect(feedback_widget.follow_cursor)
    mouse_follower_timer.start()
    
    # Start the non-blocking parts of the application
    whisper_ctrl.run()
    
    # Start the main Qt event loop
    # sys.exit() is important for proper cleanup
    sys.exit(app.exec())