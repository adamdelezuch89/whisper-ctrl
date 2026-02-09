# Quick Start Guide - Refactored Whisper-Ctrl

## What's New? 🎉

Your Whisper-Ctrl has been refactored with a modular architecture that supports:

✅ **Hybrid Backend**: Switch between Local GPU and OpenAI Cloud
✅ **Cross-Platform**: Works on Linux (X11/Wayland) and Windows
✅ **Settings GUI**: Configure everything through a user-friendly interface
✅ **System Tray**: Quick access from tray icon
✅ **Maintainable**: Clean separation of concerns

## New Project Structure

```
whisper-ctrl/
├── core/
│   ├── config.py           # ⚙️ Configuration management
│   └── text_injector.py    # 📋 Cross-platform text paste
├── transcribers/
│   ├── base.py             # 🎯 Transcriber interface
│   ├── local_whisper.py    # 🖥️ Local GPU implementation
│   └── openai_api.py       # ☁️ OpenAI Cloud implementation
├── ui/
│   ├── settings_window.py  # 🎨 Settings GUI
│   └── tray_icon.py        # 🔔 System tray icon
├── main.py                 # 📜 Your original code
├── example_integration.py  # 🚀 Reference implementation
├── test_components.py      # 🧪 Component tests
└── MIGRATION_GUIDE.md      # 📖 Detailed migration guide
```

## Step-by-Step: Get Started in 5 Minutes

### Step 1: Install New Dependencies

```bash
# Core dependencies (already installed)
pip install sounddevice numpy pynput faster-whisper torch PySide6

# NEW: Cloud and Windows support
pip install openai pyclip keyboard

# Or just update from requirements.txt
pip install -r requirements.txt
```

### Step 2: Test Individual Components

```bash
# Run comprehensive tests
python test_components.py
```

This will test:
- ✅ ConfigManager (settings management)
- ✅ TextInjector (cross-platform paste)
- ✅ Transcriber classes (Local/OpenAI)
- ✅ UI components (Settings, Tray)

**Note**: The text injection test will actually paste text, so have a text editor ready!

### Step 3: Run the Application

```bash
# Run the refactored application
python main.py
```

This will:
1. Load configuration from `~/.config/whisper-ctrl/config.json`
2. Create a system tray icon
3. Initialize the transcriber (Local GPU by default)
4. Show settings window on first run
5. Start listening for double-Ctrl hotkey

**Try this**:
- Double-press Ctrl to start recording
- Speak something
- Double-press Ctrl again to transcribe
- Text will be pasted at cursor position
- Right-click tray icon → Settings to configure
- Press Escape to cancel recording/processing

### Step 4: Understanding the Architecture

#### ConfigManager - Your New Best Friend

**Before** (hardcoded):
```python
WHISPER_MODEL_SIZE = "large-v3"
LANGUAGE = "pl"
```

**After** (configurable):
```python
from core.config import ConfigManager

config = ConfigManager()
model_size = config.get("local.model_size")  # "large-v3"
language = config.get("audio.language")       # "pl"

# Change settings
config.set("backend", "openai")
config.set("audio.language", "en")
```

Config is stored in JSON at `~/.config/whisper-ctrl/config.json` - **users can edit it directly!**

#### TextInjector - Platform Magic

**Before** (manual platform detection):
```python
session_type = os.getenv('XDG_SESSION_TYPE', '').lower()
if session_type == 'wayland':
    subprocess.run(['wl-copy', text], ...)
else:
    subprocess.run(['xclip', '-selection', 'clipboard'], ...)
```

**After** (automatic):
```python
from core.text_injector import create_text_injector

injector = create_text_injector()  # Magic! Detects Linux/Windows/X11/Wayland
injector.inject("Hello World")
```

Works on:
- ✅ Linux X11 (xclip + xdotool)
- ✅ Linux Wayland (wl-copy + wtype)
- ✅ Windows (pyperclip + keyboard)

#### Transcriber - Strategy Pattern

**Before** (single backend):
```python
self.model = WhisperModel(model_size, device="cuda", ...)
segments, _ = self.model.transcribe(audio_float32, ...)
```

**After** (multiple backends, same interface):
```python
from transcribers.local_whisper import LocalWhisperTranscriber
from transcribers.openai_api import OpenAITranscriber

# Choose backend
if backend == "local":
    transcriber = LocalWhisperTranscriber(model_size="large-v3")
else:
    transcriber = OpenAITranscriber(api_key="sk-...")

# Same interface for both!
result = transcriber.transcribe(audio_data, language="pl")
print(result.text)  # Your transcription
```

**Want to add Google Cloud Speech?** Just create `transcribers/google_cloud.py` and implement the `Transcriber` interface!

### Step 5: Settings GUI

The new Settings window lets users configure everything without touching code:

```python
from ui.settings_window import SettingsWindow
from core.config import ConfigManager

config = ConfigManager()
settings = SettingsWindow(config)
settings.show()
```

**Features**:
- 🎨 **Backend Tab**: Switch Local ↔ OpenAI, model size, API key
- 🎤 **Audio Tab**: Language, VAD settings
- ⌨️ **Hotkey Tab**: Activation hotkey (future enhancement)
- 🔧 **Advanced Tab**: Notifications, widget position

**Signal**: `settings_changed` is emitted when user clicks "Save & Apply"

### Step 6: System Tray Integration

```python
from ui.tray_icon import TrayIcon

tray_icon = TrayIcon(app)
tray_icon.settings_requested.connect(open_settings)
tray_icon.quit_requested.connect(app.quit)
```

**User Experience**:
- App minimizes to tray
- Right-click for menu (Settings, About, Quit)
- Shows status in tooltip

## Integration with Your main.py

You have **two options**:

### Option A: Complete Rewrite (Recommended)

Use `example_integration.py` as a starting point:

1. Copy your `FeedbackWidget` class
2. Copy your keyboard listener logic
3. Replace hardcoded configs with `ConfigManager`
4. Replace `inject_text()` with `TextInjector`
5. Use `Transcriber` classes instead of direct `WhisperModel`
6. Add `SettingsWindow` and `TrayIcon`

**Benefits**: Clean, maintainable, all new features

### Option B: Gradual Migration

Keep `main.py` working, migrate piece by piece:

1. **Week 1**: Add `ConfigManager`
   ```python
   from core.config import ConfigManager
   config = ConfigManager()
   WHISPER_MODEL_SIZE = config.get("local.model_size")
   LANGUAGE = config.get("audio.language")
   ```

2. **Week 2**: Replace `inject_text()` with `TextInjector`
   ```python
   from core.text_injector import create_text_injector
   self.text_injector = create_text_injector()
   # In inject_text():
   self.text_injector.inject(text)
   ```

3. **Week 3**: Add Settings GUI
   ```python
   from ui.settings_window import SettingsWindow
   # Add menu or hotkey to open settings
   ```

4. **Week 4**: Refactor transcription to use Strategy pattern

**Benefits**: Less risk, incremental progress

## Testing on Different Platforms

### Linux (X11) - Your Current Setup
```bash
# Should work out of the box
python example_integration.py
```

Dependencies: `xclip`, `xdotool` (already have these)

### Linux (Wayland)
```bash
# Requires different tools
sudo apt install wl-clipboard wtype
python example_integration.py
```

The code auto-detects Wayland and uses the right tools!

### Windows (Future)
```bash
# Install Windows-specific packages
pip install pyperclip keyboard

# Run
python example_integration.py
```

Uses `pyperclip` for clipboard, `keyboard` for Ctrl+V simulation.

## Configuration File Reference

After first run, you'll find:

**~/.config/whisper-ctrl/config.json**:
```json
{
  "backend": "local",
  "local": {
    "model_size": "large-v3",
    "compute_type": "float16",
    "device": "cuda"
  },
  "openai": {
    "api_key": "",
    "model": "whisper-1"
  },
  "audio": {
    "language": "pl",
    "vad_enabled": true,
    "vad_parameters": {
      "threshold": 0.5,
      "min_speech_duration_ms": 250,
      "min_silence_duration_ms": 700
    }
  }
}
```

**Users can edit this file directly!** Changes take effect on next restart (or when settings are reloaded).

## What's Next?

1. **Run Tests**: `python test_components.py` - verify all components work
2. **Run Application**: `python main.py` - start using it!
3. **Configure**: Right-click tray icon → Settings
4. **Read Architecture**: `ARCHITECTURE.md` for deep dive into design
5. **Customize**: Edit `~/.config/whisper-ctrl/config.json` or use Settings GUI

## Common Issues

### "Missing tools" on Linux
```bash
# X11
sudo apt install xclip xdotool

# Wayland
sudo apt install wl-clipboard wtype
```

### "Module not found: openai"
```bash
pip install openai
```

### "Invalid API key" when using OpenAI
- Get key from: https://platform.openai.com/api-keys
- Must start with `sk-`
- Enter in Settings → Backend → OpenAI API Configuration

### Windows: "Access denied" for keyboard library
- May need to run as administrator for global hotkeys
- Or use `pynput` instead (cross-platform alternative)

## Need Help?

1. Check `MIGRATION_GUIDE.md` for detailed examples
2. Check `ARCHITECTURE.md` for understanding the design
3. Run `python test_components.py` to diagnose issues
4. Look at `example_integration.py` for reference implementation

## Summary: Key Improvements

| Feature | Before | After |
|---------|--------|-------|
| **Configuration** | Hardcoded constants | JSON file + GUI |
| **Backends** | Local only | Local + OpenAI (extensible) |
| **Platforms** | Linux X11 only | Linux (X11/Wayland) + Windows |
| **Settings** | Edit code | Settings GUI |
| **UI** | Minimal | Tray icon + Settings window |
| **Architecture** | Monolithic | Modular (Strategy pattern) |
| **Extensibility** | Hard to add features | Easy plugin-style backends |

**Ready to start?** Run `python test_components.py` now! 🚀
