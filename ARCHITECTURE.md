# Whisper-Ctrl Architecture Documentation

## Overview

Whisper-Ctrl has been refactored to support:
- **Multiple backends**: Local GPU (faster-whisper) and Cloud APIs (OpenAI, Azure, Groq, etc.)
- **Cross-platform**: Linux (X11/Wayland) and Windows
- **User-configurable**: JSON config file + Settings GUI
- **Modular design**: Clean separation of concerns

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Tray Icon    │  │ Settings GUI │  │ Feedback     │      │
│  │ (System Tray)│  │ (PySide6)      │  │ Widget       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Core Layer                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ WhisperCtrl (Main Controller)                        │   │
│  │  - State management (IDLE/RECORDING/PROCESSING)      │   │
│  │  - Hotkey handling                                   │   │
│  │  - Audio recording                                   │   │
│  │  - Orchestrates all components                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ ConfigManager   │  │ Transcriber     │  │ TextInjector    │
│                 │  │ (Strategy)      │  │ (Platform)      │
│ - Load/Save     │  │                 │  │                 │
│ - Validate      │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│ - Dot notation  │  │ │ Local GPU   │ │  │ │ Linux       │ │
│ - Defaults      │  │ │ (faster-    │ │  │ │ (X11/       │ │
│ - JSON storage  │  │ │  whisper)   │ │  │ │  Wayland)   │ │
│                 │  │ └─────────────┘ │  │ └─────────────┘ │
│                 │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│                 │  │ │ Cloud API   │ │  │ │ Windows     │ │
│                 │  │ │ (Cloud)     │ │  │ │ (pyperclip) │ │
│                 │  │ └─────────────┘ │  │ └─────────────┘ │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Module Structure

### `core/` - Core Functionality

#### `config.py` - ConfigManager
**Purpose**: Centralized configuration management

**Key Features**:
- JSON-based configuration storage
- Dot notation for nested keys (`config.get("local.model_size")`)
- Automatic merging with defaults (handles new config keys)
- Validation methods (e.g., `validate_api_config()`)
- First-run detection

**Configuration File Location**: `~/.config/whisper-ctrl/config.json`

**Example Usage**:
```python
from core.config import ConfigManager

config = ConfigManager()
backend = config.get("backend")  # "local" or "api"
config.set("audio.language", "en")
```

#### `text_injector.py` - TextInjector
**Purpose**: Cross-platform text injection

**Implementations**:
1. **LinuxTextInjector**
   - Auto-detects X11 vs Wayland
   - X11: Uses `xclip` + `xdotool`
   - Wayland: Uses `wl-copy` + `wtype`

2. **WindowsTextInjector**
   - Uses `pyperclip` for clipboard
   - Uses `keyboard` library for Ctrl+V simulation
   - Restores previous clipboard content

**Example Usage**:
```python
from core.text_injector import create_text_injector

injector = create_text_injector()  # Auto-detects platform
success = injector.inject("Hello World")
```

### `transcribers/` - Transcription Backends

#### `base.py` - Transcriber Interface
**Purpose**: Abstract interface for all transcription backends

**Key Classes**:
- `Transcriber` (ABC): Interface all backends must implement
- `TranscriptionResult`: Container for results with metadata
- `TranscriptionError`: Custom exception type

**Interface Methods**:
```python
class Transcriber(ABC):
    def transcribe(audio_data, language) -> TranscriptionResult
    def is_available() -> bool
    def get_name() -> str
```

#### `local_whisper.py` - LocalWhisperTranscriber
**Purpose**: Local GPU transcription using faster-whisper

**Features**:
- GPU acceleration (CUDA)
- VAD (Voice Activity Detection) filtering
- Multiple model sizes (tiny → large-v3)
- Configurable compute type (float16/int8/float32)

**Configuration**:
```json
{
  "local": {
    "model_size": "large-v3",
    "device": "cuda",
    "compute_type": "float16"
  }
}
```

#### `api_transcriber.py` - ApiTranscriber
**Purpose**: Cloud transcription via OpenAI-compatible APIs and Azure AI Foundry

**Features**:
- Multi-provider support (OpenAI, Azure, Groq, Together, any OpenAI-compatible API)
- Automatic audio format conversion
- Temp file management
- Lazy import of `faster-whisper` (local backend loads cleanly without the package)

**Configuration**:
```json
{
  "api": {
    "type": "openai",
    "api_key": "your-key",
    "api_url": "",
    "model": "whisper-1",
    "api_version": "2024-10-21"
  }
}
```

### `ui/` - User Interface Components

#### `settings_window.py` - SettingsWindow
**Purpose**: GUI for configuration management

**Tabs**:
1. **Backend**: Choose Local GPU or Cloud API (OpenAI / Azure / compatible)
2. **Audio**: Language, VAD settings
3. **Hotkey**: Activation key configuration
4. **Advanced**: Notifications, widget offset

**Signals**:
- `settings_changed`: Emitted when settings are saved

**Example Usage**:
```python
from ui.settings_window import SettingsWindow

settings = SettingsWindow(config)
settings.settings_changed.connect(on_settings_changed)
settings.show()
```

#### `tray_icon.py` - TrayIcon
**Purpose**: System tray integration

**Features**:
- Context menu (Settings, About, Quit)
- Notification support
- Tooltip updates

**Signals**:
- `settings_requested`: User clicked "Settings"
- `quit_requested`: User clicked "Quit"

## Design Patterns Used

### 1. Strategy Pattern (Transcribers)
Different transcription backends (Local/Cloud API) implement the same interface.

**Benefits**:
- Easy to add new backends (e.g., Google Cloud Speech)
- Switch backends at runtime
- No code changes in the controller

### 2. Factory Pattern (TextInjector)
`create_text_injector()` returns the appropriate injector for the platform.

**Benefits**:
- Platform detection is centralized
- Client code doesn't need to know platform details

### 3. Singleton-like Config (ConfigManager)
One central place for all configuration.

**Benefits**:
- No scattered config constants
- Easy persistence and validation
- User-editable without code changes

## Data Flow

### Recording → Transcription → Injection

```
┌────────────┐
│ User Input │
│ (Double    │
│  Ctrl)     │
└─────┬──────┘
      │
      ▼
┌─────────────────────┐
│ WhisperCtrl         │
│ State: IDLE         │
│  → RECORDING        │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Audio Recording     │
│ (sounddevice)       │
│ - 16kHz, mono       │
│ - float32 samples   │
└─────┬───────────────┘
      │
      ▼ (User stops recording)
┌─────────────────────┐
│ WhisperCtrl         │
│ State: PROCESSING   │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Transcriber         │
│ (Local or OpenAI)   │
│ audio → text        │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ TranscriptionResult │
│ {text, language,    │
│  confidence, time}  │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ TextInjector        │
│ (Platform-specific) │
│ → clipboard → paste │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Text appears at     │
│ cursor position     │
└─────────────────────┘
```

## Configuration Schema

### Complete Config Structure

```json
{
  "backend": "local",  // "local" or "api"

  "local": {
    "model_size": "large-v3",
    "compute_type": "float16",
    "device": "cuda"
  },

  "api": {
    "type": "openai",      // "openai" or "azure"
    "api_key": "",
    "api_url": "",          // custom base URL (empty = provider default)
    "model": "whisper-1",   // model name or Azure deployment name
    "api_version": "2024-10-21"  // Azure only
  },

  "hotkey": {
    "type": "double_ctrl",
    "keys": ["ctrl_l", "ctrl_r"],
    "threshold": 0.4
  },

  "audio": {
    "sample_rate": 16000,
    "language": "pl",
    "vad_enabled": true,
    "vad_parameters": {
      "threshold": 0.5,
      "min_speech_duration_ms": 250,
      "min_silence_duration_ms": 700
    }
  },

  "ui": {
    "show_notifications": true,
    "feedback_widget_offset_x": 2,
    "feedback_widget_offset_y": 2
  },

  "first_run": false
}
```

## Extension Points

### Adding a New Transcription Backend

1. Create `transcribers/my_backend.py`
2. Inherit from `Transcriber` base class
3. Implement required methods:
   - `transcribe()`
   - `is_available()`
   - `get_name()`
4. Update config defaults in `config.py`
5. Update UI in `settings_window.py`

Example skeleton:
```python
from .base import Transcriber, TranscriptionResult

class MyBackendTranscriber(Transcriber):
    def transcribe(self, audio_data, language=None):
        # Your implementation
        return TranscriptionResult(text="...")

    def is_available(self):
        return True

    def get_name(self):
        return "My Backend"
```

### Adding a New Platform (e.g., macOS)

1. Add to `text_injector.py`:
```python
class MacOSTextInjector(TextInjector):
    def inject(self, text):
        # Implementation using macOS tools
        pass

def create_text_injector():
    system = platform.system()
    if system == "Darwin":
        return MacOSTextInjector()
    # ...
```

## Testing Strategy

### Unit Tests (test_components.py)
- Test each component independently
- Mock external dependencies
- Verify interfaces

### Integration Tests (example_integration.py)
- Test components working together
- Verify data flow
- Test configuration changes

## Performance Considerations

### Local GPU Backend
- **Model Loading**: 5-10s on first run (cached afterward)
- **Transcription**: ~0.5-2s depending on audio length and model size
- **VRAM Usage**: 1-4GB depending on model size

### Cloud API Backend
- **No Model Loading**: Instant startup
- **Transcription**: 1-3s (depends on internet speed and provider)
- **Cost**: Varies by provider

### Optimization Tips
1. Use smaller models (base/small) for faster response
2. Enable VAD filtering to reduce processing time
3. Use float16 compute type on GPU for speed
4. Consider int8 quantization for lower VRAM

## Security Considerations

1. **API Keys**: Stored in local config file (not encrypted)
   - Future: Add keyring support
2. **Clipboard**: Text briefly stored in clipboard during injection
   - Restored after pasting on Windows
3. **Audio Data**: Never stored permanently, only in memory
4. **Config File**: User-readable JSON in `~/.config`

## Future Enhancements

1. **Wizard UI**: First-run configuration wizard
2. **Custom Hotkeys**: More flexible hotkey configuration
3. **Audio Feedback**: Sound effects for recording start/stop
4. **History**: Recent transcriptions log
5. **Multiple Languages**: Auto-detect or quick-switch
6. **Backup/Sync**: Config sync across devices
7. **Plugins**: Plugin system for custom backends
