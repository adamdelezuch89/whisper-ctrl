# Changelog

All notable changes to Whisper-Ctrl will be documented in this file.

## [2.0.0] - 2026-02-09

### 🚀 Major Refactoring
Complete architectural overhaul with modular design and cross-platform support.

### ✨ Added
- **Multi-backend support**: Switch between Local GPU (faster-whisper) and OpenAI API
- **Cross-platform**: Full Linux (X11/Wayland) and Windows support
- **Settings GUI**: User-friendly configuration window with tabbed interface
- **System tray integration**: Minimize to tray with quick access menu
- **Configuration management**: JSON-based config with dot notation API
- **Modular architecture**: Clean separation into core/, transcribers/, and ui/ modules
- **Enhanced feedback widget**: Configurable cursor-following indicator
- **Hotkey customization**: Configurable activation keys and thresholds
- **First-run setup**: Automatic settings window on first launch
- **Error handling**: Graceful degradation and user-friendly error messages

### 🔄 Changed
- **PyQt6 → PySide6**: Migrated to PySide6 for better licensing (LGPL vs GPL)
- **pyperclip → pyclip**: Modern clipboard library with better data handling
- **scipy → soundfile**: Replaced scipy.io.wavfile with soundfile for WAV operations
- **Refactored main.py**: From 353 lines monolithic to 282 lines modular
- **Code organization**: Moved logic to dedicated modules (audio_recorder, hotkey_listener, text_injector)

### 🗑️ Removed
- **python-dotenv**: Unused dependency removed
- **scipy**: Replaced with soundfile (smaller, focused library)
- **Legacy code**: All old monolithic code refactored into modules

### 🔧 Technical Improvements
- **Strategy Pattern**: Transcriber interface for easy backend switching
- **Factory Pattern**: Automatic platform detection for text injection
- **Dependency Injection**: ConfigManager passed to all components
- **Signal/Slot Architecture**: Clean event handling with Qt signals
- **Threading**: Proper background processing for audio and transcription
- **Type hints**: Full type annotations for better IDE support
- **Documentation**: Comprehensive guides (README, QUICK_START, ARCHITECTURE)

### 📦 Updated Dependencies
```
PySide6~=6.7.0 (was PyQt6)
openai~=2.19.0 (was 2.17.0)
pyclip~=0.7.0 (was pyperclip)
soundfile~=0.12.1 (new)
```

### 🐛 Bug Fixes
- Fixed clipboard restoration on Windows
- Improved error handling for missing system tools
- Better cancellation support (ESC key)
- Proper cleanup on shutdown (SIGINT/SIGTERM)

### 📚 Documentation
- New comprehensive README.md
- Quick Start Guide (QUICK_START.md)
- Architecture documentation (ARCHITECTURE.md)
- Component testing suite (test_components.py)

---

## [1.0.0] - 2026-01-XX

### Initial Release
- Basic voice dictation with local Whisper model
- Linux X11 support
- Double-Ctrl activation
- Simple cursor feedback widget
- Hardcoded configuration

---

## Legend
- 🚀 Major features
- ✨ New features
- 🔄 Changes
- 🗑️ Removals
- 🔧 Technical improvements
- 🐛 Bug fixes
- 📚 Documentation
