# Whisper-Ctrl (Local GPU)

Whisper-Ctrl is a lightweight voice dictation application for Linux that leverages the power of your **local GPU** for lightning-fast speech-to-text transcription. By using the `faster-whisper` library, the application operates entirely offline, with no reliance on external APIs.

The application is activated by a global hotkey (a quick double-press of the `Ctrl` key), and the entire process provides feedback via system notifications (if installed).

## Features

- **Local GPU Transcription**: All processing happens on your local machine, ensuring both privacy and speed.
- **On-Demand Activation**: Recording starts and stops with a quick, double-press of the left `Ctrl` key.
- **Contextual Pasting**: The transcribed text is automatically pasted at your current cursor position.
- **System Feedback**: Stay informed of the current status (recording, processing) through system notifications.
- **High Performance**: Powered by `faster-whisper` for up to 4x faster transcription than the original model, with lower VRAM consumption.

## System Requirements

- **Linux Operating System**
- **NVIDIA graphics card with CUDA 11 or 12 support**
- **Installed NVIDIA drivers** and **CUDA Toolkit**
- Python 3.8+ and `python3-venv` (or the equivalent for your distribution)
- A working microphone
- External tools (required for running, not for building):
  - **X11**: `xclip` and `xdotool`
  - **Wayland**: `wl-clipboard` and `wtype`
  - **Notifications**: `libnotify` (package `libnotify-bin` or `notify-send`)

## Installation (for Users)

Download the latest `.AppImage` file from the [Releases](https://github.com/username/whisper-ctrl/releases) section. Then:
1. Make the file executable: `chmod +x Whisper-Ctrl-*.AppImage`.
2. Run the application by double-clicking it.
3. To have the application start automatically, add it to your desktop environment's startup applications.

## Building the AppImage (for Developers)

The included `build.sh` script automates the entire process, from creating the environment to building the final file.

### Prerequisites
1.  **Clone the repository** and navigate into its directory.
2.  **Ensure you have Python 3 and the `venv` package installed** on your system (e.g., `sudo apt install python3-venv` on Debian/Ubuntu).

### Build Process
The process is fully automated. Just run the following commands:

```bash
# First, make the script executable
chmod +x build.sh

# Then, run it
./build.sh
```

The script will automatically:
- Create a `venv` virtual environment.
- Install dependencies from `requirements.txt`.
- Download the `linuxdeploy` and `appimagetool` utilities.
- Build the AppImage file.
- **Clean up after itself by removing all temporary files.**

## Usage

1.  Anywhere in your system where you can input text, **quickly double-press the left Ctrl key**.
2.  A "🎙️ Recording..." notification will appear. Start speaking.
3.  When you're finished, **quickly double-press the left Ctrl key again**.
4.  Wait for the "🧠 Processing..." notification. The transcription will be pasted at your cursor's position after a few seconds.

## Permissions
For the global hotkeys to work, your user account must have permission to read input devices. This can be achieved by adding your user to the `input` group:
```bash
sudo usermod -a -G input $USER
```
**You will need to log out and back in for this change to take effect.**

## License

[MIT](LICENSE)