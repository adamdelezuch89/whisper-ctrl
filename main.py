#!/usr/bin/env python3
"""
Whisper-Ctrl - Cross-platform voice dictation with local or cloud transcription.

This application listens for a global hotkey (double-press Ctrl by default),
records audio, transcribes it using either local GPU (faster-whisper) or
cloud API (OpenAI), and pastes the result at the cursor position.

Features:
- Multi-backend: Local GPU or OpenAI API
- Cross-platform: Linux (X11/Wayland) and Windows
- Configurable: JSON config + Settings GUI
- Visual feedback: Animated cursor indicator
"""

import sys
import signal
import threading
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer
from pynput import keyboard

# Import our modular components
from core.config import ConfigManager
from core.state import State
from core.audio_recorder import AudioRecorder
from core.hotkey_listener import HotkeyListener
from core.text_injector import create_text_injector
from transcribers.base import Transcriber, TranscriptionError
from transcribers.local_whisper import LocalWhisperTranscriber
from transcribers.openai_api import OpenAITranscriber
from ui.feedback_widget import FeedbackWidget
from ui.settings_window import SettingsWindow
from ui.tray_icon import TrayIcon


class WhisperCtrl(QObject):
    """
    Main application controller.

    Orchestrates all components: audio recording, transcription, text injection,
    hotkey handling, and UI updates.
    """

    # Signal emitted when application state changes
    state_changed = Signal(State)

    def __init__(self, config: ConfigManager):
        """
        Initialize Whisper-Ctrl.

        Args:
            config: Configuration manager instance
        """
        super().__init__()
        self.config = config
        self.state = State.IDLE

        # Initialize components
        self._init_transcriber()
        self.audio_recorder = AudioRecorder(
            sample_rate=self.config.get("audio.sample_rate", 16000)
        )
        self.text_injector = create_text_injector()
        self.hotkey_listener = self._create_hotkey_listener()

        # UI components (initialized by run())
        self.settings_window: Optional[SettingsWindow] = None
        self.tray_icon: Optional[TrayIcon] = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        print(f"✅ Whisper-Ctrl initialized with {self.transcriber.get_name()}")

    def _init_transcriber(self):
        """Initialize transcriber based on config."""
        backend = self.config.get("backend", "local")

        try:
            if backend == "local":
                local_cfg = self.config.get("local", {})
                vad_params = self.config.get("audio.vad_parameters", {})

                self.transcriber = LocalWhisperTranscriber(
                    model_size=local_cfg.get("model_size", "large-v3"),
                    device=local_cfg.get("device", "cuda"),
                    compute_type=local_cfg.get("compute_type", "float16"),
                    vad_enabled=self.config.get("audio.vad_enabled", True),
                    vad_parameters=vad_params
                )

            elif backend == "openai":
                api_key = self.config.get("openai.api_key", "")
                if not api_key:
                    raise ValueError("OpenAI API key not configured")

                self.transcriber = OpenAITranscriber(
                    api_key=api_key,
                    model=self.config.get("openai.model", "whisper-1")
                )

            else:
                raise ValueError(f"Unknown backend: {backend}")

        except Exception as e:
            print(f"❌ Failed to initialize transcriber: {e}")
            print("   Check your configuration and try again.")
            sys.exit(1)

    def _create_hotkey_listener(self) -> HotkeyListener:
        """Create hotkey listener from config."""
        keys = self.config.get("hotkey.keys", ["ctrl_l", "ctrl_r"])
        threshold = self.config.get("hotkey.threshold", 0.4)

        # Convert string keys to pynput Key objects
        key_objects = []
        for key_name in keys:
            if hasattr(keyboard.Key, key_name):
                key_objects.append(getattr(keyboard.Key, key_name))

        return HotkeyListener(
            keys=key_objects,
            threshold=threshold,
            on_double_press=self._handle_double_press,
            on_escape=self._handle_escape
        )

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals (Ctrl+C, SIGTERM)."""
        print("\n🛑 Shutting down Whisper-Ctrl...")
        if self.audio_recorder.is_recording():
            self.audio_recorder.cancel_recording()
        self.hotkey_listener.stop()
        QApplication.quit()

    def _handle_double_press(self):
        """Handle double-press of hotkey."""
        if self.state == State.PROCESSING:
            print("⏳ Please wait, processing in progress...")
            return

        if self.state == State.IDLE:
            # Start recording
            self.state = State.RECORDING
            self.state_changed.emit(self.state)
            self.audio_recorder.start_recording(
                on_error=lambda e: self._on_recording_error(e)
            )

        elif self.state == State.RECORDING:
            # Stop recording and start processing
            self.state = State.PROCESSING
            self.state_changed.emit(self.state)

            audio_data = self.audio_recorder.stop_recording()
            print("🧠 Processing audio...")

            # Process in background thread
            threading.Thread(
                target=self._process_audio,
                args=(audio_data,),
                daemon=True
            ).start()

    def _handle_escape(self):
        """Handle Escape key press (cancel operation)."""
        if self.state == State.RECORDING:
            print("❌ Recording cancelled")
            self.audio_recorder.cancel_recording()
            self.state = State.IDLE
            self.state_changed.emit(self.state)

        elif self.state == State.PROCESSING:
            print("❌ Processing cancelled")
            # Note: Can't stop transcription in progress, but we won't paste the result
            self.state = State.IDLE
            self.state_changed.emit(self.state)

    def _on_recording_error(self, error: Exception):
        """Handle recording errors."""
        print(f"❌ Recording error: {error}")
        self.state = State.IDLE
        self.state_changed.emit(self.state)

    def _process_audio(self, audio_data):
        """
        Process audio in background thread.

        Args:
            audio_data: numpy array with audio samples
        """
        try:
            if audio_data is None or len(audio_data) == 0:
                print("❌ No audio data to process")
                return

            # Check if cancelled
            if self.state != State.PROCESSING:
                print("❌ Processing cancelled, skipping transcription")
                return

            # Get language from config
            language = self.config.get("audio.language", "pl")
            if language == "auto":
                language = None

            # Transcribe
            result = self.transcriber.transcribe(audio_data, language=language)

            # Check if cancelled during transcription
            if self.state != State.PROCESSING:
                print("❌ Processing cancelled, skipping paste")
                return

            # Inject text
            if result.text:
                print(f"✅ Transcription: '{result.text}'")
                success = self.text_injector.inject(result.text)

                if not success:
                    print("⚠️ Text injection may have failed")
            else:
                print("📝 Empty transcription, skipping paste")

        except TranscriptionError as e:
            print(f"❌ Transcription error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            # Always return to IDLE state
            self.state = State.IDLE
            self.state_changed.emit(self.state)

    def open_settings(self):
        """Open the settings window."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.settings_changed.connect(self._on_settings_changed)

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_settings_changed(self):
        """Handle settings changes - reinitialize transcriber."""
        print("⚙️ Settings changed, reinitializing...")

        # Reinitialize transcriber
        old_name = self.transcriber.get_name()
        self._init_transcriber()
        new_name = self.transcriber.get_name()

        if old_name != new_name:
            print(f"✅ Switched from {old_name} to {new_name}")

        # Update tray tooltip
        if self.tray_icon:
            self.tray_icon.set_tooltip(f"Whisper-Ctrl ({new_name})")

        # Recreate hotkey listener if keys changed
        self.hotkey_listener.stop()
        self.hotkey_listener = self._create_hotkey_listener()
        self.hotkey_listener.start()

    def run(self, app: QApplication):
        """
        Run the application.

        Args:
            app: QApplication instance
        """
        # Create UI components
        self.tray_icon = TrayIcon(app)
        self.tray_icon.settings_requested.connect(self.open_settings)
        self.tray_icon.quit_requested.connect(app.quit)
        self.tray_icon.set_tooltip(f"Whisper-Ctrl ({self.transcriber.get_name()})")

        # Start hotkey listener
        self.hotkey_listener.start()

        # Show first-run setup if needed
        if self.config.is_first_run():
            print("👋 First run detected - opening settings...")
            self.config.mark_first_run_complete()
            QTimer.singleShot(500, self.open_settings)

        # Print startup info
        backend = self.config.get("backend", "local")
        print("🚀 Whisper-Ctrl is running")
        print(f"   Backend: {backend}")
        print(f"   Transcriber: {self.transcriber.get_name()}")
        print(f"   Hotkey: Double-press {self.config.get('hotkey.keys')}")
        print("   Press Escape to cancel recording/processing")
        print("   Right-click tray icon for settings")


def main():
    """Main entry point."""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when windows close

    # Load configuration
    config = ConfigManager()

    # Create main controller
    whisper_ctrl = WhisperCtrl(config)

    # Create feedback widget
    feedback_widget = FeedbackWidget(
        offset_x=config.get("ui.feedback_widget_offset_x", 2),
        offset_y=config.get("ui.feedback_widget_offset_y", 2)
    )

    # Connect state changes to feedback widget
    def on_state_changed(state: State):
        if state == State.RECORDING:
            feedback_widget.show_recording()
        elif state == State.PROCESSING:
            feedback_widget.show_processing()
        else:  # IDLE
            feedback_widget.hide_feedback()

    whisper_ctrl.state_changed.connect(on_state_changed)

    # Timer to make feedback widget follow cursor
    cursor_follower = QTimer()
    cursor_follower.setInterval(16)  # ~60 FPS
    cursor_follower.timeout.connect(feedback_widget.follow_cursor)
    cursor_follower.start()

    # Run application
    whisper_ctrl.run(app)

    # Start Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
