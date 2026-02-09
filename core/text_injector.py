"""
Text Injection Module for Whisper-Ctrl.

Provides cross-platform text injection capabilities.
Supports Linux (X11/Wayland) and Windows.
"""

import os
import platform
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Optional


class TextInjector(ABC):
    """Abstract base class for text injection."""

    @abstractmethod
    def inject(self, text: str) -> bool:
        """
        Inject text at the current cursor position.

        Args:
            text: Text to inject

        Returns:
            True if successful, False otherwise
        """
        pass


class LinuxTextInjector(TextInjector):
    """Text injector for Linux (supports both X11 and Wayland)."""

    def __init__(self):
        """Initialize Linux text injector and detect display server."""
        self.session_type = self._detect_session_type()
        self._validate_dependencies()

    def _detect_session_type(self) -> str:
        """
        Detect the display server (X11 or Wayland).

        Returns:
            "wayland", "x11", or "unknown"
        """
        session = os.getenv('XDG_SESSION_TYPE', '').lower()
        if session in ('wayland', 'x11'):
            return session

        # Fallback detection
        if os.getenv('WAYLAND_DISPLAY'):
            return "wayland"
        elif os.getenv('DISPLAY'):
            return "x11"

        return "unknown"

    def _validate_dependencies(self) -> None:
        """Check if required tools are installed."""
        required_tools = []

        if self.session_type == "wayland":
            required_tools = ['wl-copy', 'wtype']
        elif self.session_type == "x11":
            required_tools = ['xclip', 'xdotool']

        missing = []
        for tool in required_tools:
            if not self._command_exists(tool):
                missing.append(tool)

        if missing:
            print(f"⚠️ Warning: Missing tools for {self.session_type}: {', '.join(missing)}")
            print(f"   Install with: sudo apt install {' '.join(missing)}")

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(['which', command],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def inject(self, text: str) -> bool:
        """
        Inject text using X11 or Wayland tools.

        Args:
            text: Text to inject

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.session_type == "wayland":
                return self._inject_wayland(text)
            elif self.session_type == "x11":
                return self._inject_x11(text)
            else:
                print(f"❌ Unsupported session type: {self.session_type}")
                return False
        except Exception as e:
            print(f"❌ Error injecting text: {e}")
            return False

    def _inject_wayland(self, text: str) -> bool:
        """Inject text on Wayland using wl-copy + wtype."""
        # Copy to clipboard
        subprocess.run(['wl-copy', text],
                      text=True,
                      check=True,
                      timeout=2)

        # Paste using Shift+Insert
        subprocess.run(['wtype', '-M', 'shift', '-P', 'insert', '-m', 'shift'],
                      check=True,
                      timeout=2)

        print("✅ Text pasted successfully (Wayland)")
        return True

    def _inject_x11(self, text: str) -> bool:
        """Inject text on X11 using xclip + xdotool."""
        # Copy to clipboard
        subprocess.run(['xclip', '-selection', 'clipboard'],
                      input=text,
                      text=True,
                      check=True,
                      timeout=2)

        # Small delay to ensure clipboard is updated
        time.sleep(0.05)

        # Paste using Ctrl+V
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+v'],
                      check=True,
                      timeout=2)

        print("✅ Text pasted successfully (X11)")
        return True


class WindowsTextInjector(TextInjector):
    """Text injector for Windows using pyclip and keyboard."""

    def __init__(self):
        """Initialize Windows text injector."""
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Check if required Python packages are available."""
        try:
            import pyclip
            import keyboard
        except ImportError as e:
            print(f"❌ Missing required package: {e.name}")
            print("   Install with: pip install pyclip keyboard")
            raise

    def inject(self, text: str) -> bool:
        """
        Inject text using clipboard and keyboard simulation.

        Args:
            text: Text to inject

        Returns:
            True if successful, False otherwise
        """
        try:
            import pyclip
            import keyboard

            # pyclip automatically handles clipboard context (saves/restores)
            pyclip.copy(text)

            # Small delay to ensure clipboard is updated
            time.sleep(0.05)

            # Simulate Ctrl+V
            keyboard.send('ctrl+v')

            # Wait for paste to complete
            time.sleep(0.1)

            print("✅ Text pasted successfully (Windows)")
            return True

        except Exception as e:
            print(f"❌ Error injecting text: {e}")
            return False


def create_text_injector() -> TextInjector:
    """
    Factory function to create the appropriate text injector for the current platform.

    Returns:
        TextInjector instance for the current platform

    Raises:
        NotImplementedError: If the platform is not supported
    """
    system = platform.system()

    if system == "Linux":
        return LinuxTextInjector()
    elif system == "Windows":
        return WindowsTextInjector()
    else:
        raise NotImplementedError(f"Platform '{system}' is not supported yet")
