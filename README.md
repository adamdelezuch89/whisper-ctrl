# Whisper-Ctrl

**Cross-platform voice dictation with local GPU or cloud transcription.**

Whisper-Ctrl is a powerful voice dictation application that works on **Linux** (X11/Wayland) and **Windows**. Activate it with a quick double-press of the Ctrl key, speak, and have your words automatically transcribed and pasted at your cursor position.

## ✨ Features

- **🎯 Multi-Backend Support**
  - Local GPU transcription (faster-whisper) - Private & Free
  - OpenAI API transcription - High accuracy, cloud-based

- **🖥️ Cross-Platform**
  - Linux with X11 or Wayland
  - Windows (7/10/11)

- **⚙️ User-Friendly Configuration**
  - Settings GUI for easy configuration
  - JSON config file for advanced users
  - System tray integration

- **🚀 High Performance**
  - GPU-accelerated local transcription (4x faster than original Whisper)
  - Voice Activity Detection (VAD) for better accuracy
  - Real-time visual feedback with cursor-following indicator

- **🔒 Privacy-Focused**
  - Local mode processes everything on your machine
  - No data leaves your computer (when using local backend)

## 📋 Requirements

### For Local GPU Backend (Recommended)
- **NVIDIA GPU** with CUDA 11 or 12 support
- **NVIDIA Drivers** and **CUDA Toolkit** installed
- **4-6 GB VRAM** (depending on model size)

### For OpenAI API Backend
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Internet connection**
- No GPU required

### System Requirements
- **Linux**: Debian/Ubuntu or compatible with X11 or Wayland
- **Windows**: 7/10/11 with Python 3.10+
- **Python**: 3.10 or higher
- **Microphone**: Any working microphone

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/whisper-ctrl.git
cd whisper-ctrl

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Platform-Specific Tools

**Linux (X11)**:
```bash
sudo apt install xclip xdotool
```

**Linux (Wayland)**:
```bash
sudo apt install wl-clipboard wtype
```

**Windows**: No additional tools needed (uses pyperclip + keyboard)

### 3. Run the Application

```bash
python main.py
```

On first run, a settings window will appear to configure your preferences.

### 4. Basic Usage

1. **Activate**: Double-press the **Ctrl** key quickly
2. **Record**: A red pulsing circle appears - start speaking
3. **Stop**: Double-press **Ctrl** again
4. **Wait**: Blue spinning indicator shows processing
5. **Done**: Text is pasted at your cursor position

**Cancel anytime**: Press **Escape** to cancel recording or processing

## ⚙️ Configuration

### Using the Settings GUI

Right-click the system tray icon and select "Settings" to access:

- **Backend Tab**: Switch between Local GPU and OpenAI API
- **Audio Tab**: Configure language, VAD settings
- **Hotkey Tab**: Customize activation hotkey (future)
- **Advanced Tab**: Notification settings, widget position

### Manual Configuration

Configuration is stored at `~/.config/whisper-ctrl/config.json`:

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
    "vad_enabled": true
  }
}
```

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - 5-minute guide to get started
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into the design
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Upgrading from older versions

## 🏗️ Architecture

Whisper-Ctrl uses a modular architecture with clean separation of concerns:

```
whisper-ctrl/
├── core/
│   ├── config.py          # Configuration management
│   ├── audio_recorder.py  # Audio recording
│   ├── hotkey_listener.py # Keyboard shortcuts
│   └── text_injector.py   # Cross-platform text paste
├── transcribers/
│   ├── local_whisper.py   # Local GPU backend
│   └── openai_api.py      # OpenAI API backend
└── ui/
    ├── feedback_widget.py # Cursor indicator
    ├── settings_window.py # Settings GUI
    └── tray_icon.py       # System tray integration
```

## 🔧 Advanced Features

### Switching Backends

```python
# Via Settings GUI: Backend tab → Select "OpenAI API" → Enter API key

# Via config file:
{
  "backend": "openai",
  "openai": {
    "api_key": "sk-your-api-key-here"
  }
}
```

### Custom Model Sizes (Local)

Choose based on your needs:
- `tiny` - Fastest, ~1GB VRAM
- `base` - Fast, good accuracy, ~1GB VRAM
- `small` - Balanced, ~2GB VRAM
- `medium` - Better accuracy, ~5GB VRAM
- `large-v3` - Best accuracy, ~10GB VRAM (default)

### Multiple Languages

Supports 90+ languages. Configure in Settings → Audio → Language:
- `auto` - Auto-detect language
- `en` - English
- `pl` - Polish
- `de` - German
- `fr` - French
- ... and more

## 🐛 Troubleshooting

### "Missing tools" error (Linux)
```bash
# For X11
sudo apt install xclip xdotool

# For Wayland
sudo apt install wl-clipboard wtype
```

### "Failed to load model" (Local GPU)
- Verify CUDA is installed: `nvidia-smi`
- Check PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
- Try CPU mode: Change `"device": "cuda"` to `"device": "cpu"` in config

### "Invalid API key" (OpenAI)
- Get key from: https://platform.openai.com/api-keys
- Must start with `sk-`
- Add billing information to OpenAI account

### Hotkeys not working
```bash
# Add user to input group (Linux)
sudo usermod -a -G input $USER
# Log out and back in
```

## 🔨 Building from Source

### Building .deb Package (Linux/Debian/Ubuntu)

The application includes an automated build script that creates a `.deb` package:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/whisper-ctrl.git
cd whisper-ctrl

# 2. Install build dependencies
sudo apt install git python3-pip fakeroot

# 3. Make build script executable
chmod +x build.sh

# 4. Build the package (no sudo needed)
./build.sh

# 5. Install the generated package
sudo apt install ./whisper-ctrl_2.0-1_amd64.deb
```

The build script will:
- Create a self-contained package with all Python dependencies
- Include the modular structure (core/, transcribers/, ui/)
- Bundle PyTorch, faster-whisper, PySide6, and other dependencies
- Create a launcher script and .desktop entry

**Package size**: ~2-3GB (includes all dependencies)

### Building Portable .exe (Windows)

For Windows, use PyInstaller to create a portable executable:

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build single-file executable
pyinstaller main.py --name "Whisper-Ctrl" --onefile --windowed ^
    --icon=icon.ico ^
    --add-data "core;core" ^
    --add-data "transcribers;transcribers" ^
    --add-data "ui;ui" ^
    --hidden-import=PySide6 ^
    --hidden-import=faster_whisper ^
    --hidden-import=pyclip

# Result: dist/Whisper-Ctrl.exe (~800MB-2GB)
```

**Alternative** - Use `--onedir` instead of `--onefile` for faster startup:
```bash
pyinstaller main.py --name "Whisper-Ctrl" --onedir --windowed ...
# Result: dist/Whisper-Ctrl/ folder (~2GB)
```

## 📊 Performance

| Backend | Startup Time | Transcription Speed | Cost | Privacy |
|---------|-------------|-------------------|------|---------|
| **Local GPU** | ~5-10s (first run) | 0.5-2s per audio | Free | ✅ 100% Private |
| **OpenAI API** | Instant | 1-3s per audio | ~$0.006/min | ⚠️ Cloud-based |

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional transcription backends (Google, Azure)
- First-run wizard UI
- Custom hotkey configuration UI
- Audio feedback (sound effects)
- Transcription history log

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Fast Whisper implementation
- [OpenAI Whisper](https://github.com/openai/whisper) - Original Whisper model
- [PySide6](https://doc.qt.io/qtforpython-6/) - Modern Qt GUI framework (LGPL)
- [pynput](https://github.com/moses-palmer/pynput) - Keyboard/mouse control
- [pyclip](https://github.com/spyoungtech/pyclip) - Cross-platform clipboard

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/whisper-ctrl/issues)
- **Documentation**: Check the docs/ folder
- **Testing**: Run `python test_components.py` to diagnose problems

---

**Made with ❤️ for productivity enthusiasts**
