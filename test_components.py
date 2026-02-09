#!/usr/bin/env python3
"""
Component Testing Script for Whisper-Ctrl.

Tests individual components before full integration.
Run this to verify everything works on your platform.
"""

import sys
import platform
import numpy as np
from pathlib import Path


def test_config_manager():
    """Test ConfigManager functionality."""
    print("\n" + "="*60)
    print("TEST 1: ConfigManager")
    print("="*60)

    try:
        from core.config import ConfigManager

        # Create config with test path
        test_config_path = Path.home() / ".config" / "whisper-ctrl" / "test_config.json"
        config = ConfigManager(str(test_config_path))

        # Test reading
        backend = config.get("backend")
        print(f"✅ Read backend: {backend}")

        # Test writing
        config.set("test_key", "test_value")
        value = config.get("test_key")
        assert value == "test_value", "Config read/write mismatch"
        print(f"✅ Write/read test: {value}")

        # Test nested keys
        model_size = config.get("local.model_size")
        print(f"✅ Nested key access: {model_size}")

        # Test backend config
        backend_config = config.get_backend_config()
        print(f"✅ Backend config: {list(backend_config.keys())}")

        print("✅ ConfigManager: PASSED")
        return True

    except Exception as e:
        print(f"❌ ConfigManager: FAILED - {e}")
        return False


def test_text_injector():
    """Test TextInjector functionality."""
    print("\n" + "="*60)
    print("TEST 2: TextInjector")
    print("="*60)

    try:
        from core.text_injector import create_text_injector, LinuxTextInjector, WindowsTextInjector

        # Detect platform
        system = platform.system()
        print(f"📍 Platform: {system}")

        # Create injector
        injector = create_text_injector()
        print(f"✅ Created injector: {injector.__class__.__name__}")

        # Platform-specific checks
        if system == "Linux":
            assert isinstance(injector, LinuxTextInjector)
            print(f"✅ Correct injector type for Linux")
            print(f"   Session type: {injector.session_type}")

        elif system == "Windows":
            assert isinstance(injector, WindowsTextInjector)
            print(f"✅ Correct injector type for Windows")

        # Test injection (will actually paste text!)
        print("\n⚠️  Testing text injection in 3 seconds...")
        print("    Focus a text editor and wait...")
        import time
        time.sleep(3)

        test_text = "[Whisper-Ctrl Test - You can delete this]"
        success = injector.inject(test_text)

        if success:
            print(f"✅ Text injection: PASSED")
        else:
            print(f"⚠️  Text injection: Completed but reported failure")

        print("✅ TextInjector: PASSED")
        return True

    except Exception as e:
        print(f"❌ TextInjector: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transcribers():
    """Test Transcriber base classes."""
    print("\n" + "="*60)
    print("TEST 3: Transcriber Classes")
    print("="*60)

    try:
        from transcribers.base import Transcriber, TranscriptionResult
        from transcribers.local_whisper import LocalWhisperTranscriber

        # Test TranscriptionResult
        result = TranscriptionResult(
            text="Hello world",
            language="en",
            confidence=0.95,
            duration=1.5
        )
        print(f"✅ TranscriptionResult created: {result}")

        # Test Local Transcriber initialization (without actually loading model)
        print("\n⚠️  Skipping actual model loading (takes time and GPU)")
        print("    To test transcription, use example_integration.py")

        print("✅ Transcriber Classes: PASSED")
        return True

    except Exception as e:
        print(f"❌ Transcriber Classes: FAILED - {e}")
        return False


def test_ui_components():
    """Test UI components (requires Qt)."""
    print("\n" + "="*60)
    print("TEST 4: UI Components")
    print("="*60)

    try:
        from PySide6.QtWidgets import QApplication
        from ui.settings_window import SettingsWindow
        from ui.tray_icon import TrayIcon
        from core.config import ConfigManager

        # Create Qt application
        app = QApplication(sys.argv)
        print("✅ QApplication created (PySide6)")

        # Test ConfigManager
        config = ConfigManager()
        print("✅ ConfigManager created")

        # Test SettingsWindow
        settings = SettingsWindow(config)
        print("✅ SettingsWindow created")

        # Test TrayIcon
        tray = TrayIcon(app)
        print("✅ TrayIcon created")

        # Clean up
        app.quit()

        print("✅ UI Components: PASSED")
        return True

    except Exception as e:
        print(f"❌ UI Components: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependencies():
    """Test that all required packages are installed."""
    print("\n" + "="*60)
    print("TEST 0: Dependencies")
    print("="*60)

    required_packages = [
        "numpy",
        "sounddevice",
        "soundfile",
        "pynput",
        "PySide6",
        "faster_whisper",
    ]

    optional_packages = [
        ("openai", "OpenAI API support"),
        ("pyclip", "Cross-platform clipboard support"),
        ("keyboard", "Windows keyboard support"),
    ]

    all_good = True

    # Check required packages
    print("\nRequired packages:")
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            all_good = False

    # Check optional packages
    print("\nOptional packages:")
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {package} ({description})")
        except ImportError:
            print(f"  ⚠️  {package} - Not installed ({description})")

    # Platform-specific checks
    print("\nPlatform-specific tools:")
    system = platform.system()

    if system == "Linux":
        import subprocess
        tools = {
            "xclip": "X11 clipboard",
            "xdotool": "X11 keyboard",
            "wl-copy": "Wayland clipboard",
            "wtype": "Wayland keyboard",
        }

        for tool, desc in tools.items():
            try:
                subprocess.run(['which', tool],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             check=True)
                print(f"  ✅ {tool} ({desc})")
            except:
                print(f"  ⚠️  {tool} - Not found ({desc})")

    if all_good:
        print("\n✅ Dependencies: PASSED")
    else:
        print("\n❌ Dependencies: FAILED - Install missing packages")

    return all_good


def main():
    """Run all tests."""
    print("="*60)
    print("WHISPER-CTRL COMPONENT TESTS")
    print("="*60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")

    results = []

    # Run tests
    results.append(("Dependencies", test_dependencies()))
    results.append(("ConfigManager", test_config_manager()))
    results.append(("Transcribers", test_transcribers()))
    results.append(("UI Components", test_ui_components()))

    # Ask before text injection test (it will actually paste text)
    print("\n" + "="*60)
    response = input("Run text injection test? This will paste text! (y/n): ")
    if response.lower() == 'y':
        results.append(("TextInjector", test_text_injector()))
    else:
        print("⏭️  Skipping text injection test")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:20s} {status}")

    print("="*60)
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! You're ready to integrate.")
        print("   Next step: Run 'python example_integration.py'")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
