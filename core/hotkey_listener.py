"""
Hotkey Listener for Whisper-Ctrl.

Handles global keyboard shortcuts with double-press detection.
"""

import time
from typing import Callable, Optional
from pynput import keyboard


class HotkeyListener:
    """
    Global hotkey listener with double-press detection.

    Listens for double-press of specified keys (e.g., Ctrl, Alt)
    and triggers callbacks.
    """

    def __init__(
        self,
        keys: list[keyboard.Key],
        threshold: float = 0.4,
        on_double_press: Optional[Callable[[], None]] = None,
        on_escape: Optional[Callable[[], None]] = None
    ):
        """
        Initialize hotkey listener.

        Args:
            keys: List of keys to listen for (e.g., [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
            threshold: Time window for double-press detection in seconds
            on_double_press: Callback triggered on double-press
            on_escape: Callback triggered on Escape key press
        """
        self.keys = set(keys)
        self.threshold = threshold
        self.on_double_press = on_double_press
        self.on_escape = on_escape

        self.last_press_time = 0.0
        self.listener: Optional[keyboard.Listener] = None

    def _on_press(self, key):
        """Internal key press handler."""
        # Check for double-press of configured keys
        if key in self.keys:
            current_time = time.monotonic()
            time_diff = current_time - self.last_press_time
            self.last_press_time = current_time

            if time_diff < self.threshold:
                if self.on_double_press:
                    self.on_double_press()

        # Check for Escape key
        elif key == keyboard.Key.esc:
            if self.on_escape:
                self.on_escape()

    def start(self):
        """Start listening for hotkeys."""
        if self.listener is None:
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.start()
            print(f"👂 Listening for double-press of {self.keys}")

    def stop(self):
        """Stop listening for hotkeys."""
        if self.listener:
            self.listener.stop()
            self.listener = None
            print("🛑 Hotkey listener stopped")

    def is_active(self) -> bool:
        """Check if listener is active."""
        return self.listener is not None and self.listener.is_alive()
