# Whisper-Ctrl (Local GPU)

Whisper-Ctrl is a lightweight voice dictation application for Linux that leverages the power of your **local GPU** for lightning-fast speech-to-text transcription. By using the `faster-whisper` library, the application operates entirely offline, with no reliance on external APIs.

The application is activated by a global hotkey (a quick double-press of the `Ctrl` key), and the entire process provides clear, on-screen visual feedback via an indicator that follows your cursor.

## Features

- **Local GPU Transcription**: All processing happens on your local machine, ensuring both privacy and speed.
- **On-Demand Activation**: Recording starts and stops with a quick, double-press of the `Ctrl` key.
- **Contextual Pasting**: The transcribed text is automatically pasted at your current cursor position.
- **High Performance**: Powered by `faster-whisper` for up to 4x faster transcription than the original model, with lower VRAM consumption.

## System Requirements

- **Linux Operating System (Debian, Ubuntu, or compatible)** with an X11 session.
- **NVIDIA graphics card with CUDA 11 or 12 support**
- **Installed NVIDIA drivers** and **CUDA Toolkit**
- **Git** and the required build tools (`python3-pip`, `fakeroot`)
- A working microphone

## Installation

This application **must be built from source**. The process is automated by a build script that creates a standard Debian (`.deb`) package, which you can then install on your system.

#### Step 1: Clone the Repository
First, open a terminal and clone this repository to your local machine:
```bash
git clone https://github.com/username/whisper-ctrl.git
cd whisper-ctrl
```
*(Replace `username/whisper-ctrl` with the actual repository URL)*

#### Step 2: Install Build Dependencies
Ensure you have the necessary tools to build the package. On Debian, Ubuntu, or Zorin OS, run:
```bash
sudo apt update
sudo apt install git python3-pip fakeroot
```

#### Step 3: Build the `.deb` Package
The repository includes an automated build script. Make it executable and run it. This step does **not** require `sudo`.

```bash
# Make the script executable
chmod +x build.sh

# Run the build script
./build.sh
```
The script will create a self-contained build environment, install all Python dependencies (like PyQt6, PyTorch, and faster-whisper), and package everything into a `.deb` file in the project's root directory. All temporary build files will be cleaned up automatically.

#### Step 4: Install the Generated Package
After the script finishes, you will find a new `whisper-ctrl_*.deb` file. Install it using `apt`, which will also handle any remaining runtime dependencies.
```bash
sudo apt install ./whisper-ctrl_*.deb
```

## Usage

1.  Anywhere in your system where you can input text, **quickly double-press a Ctrl key**.
2.  A **red, pulsing circle** will appear next to your cursor. Start speaking.
3.  When you're finished, **quickly double-press a Ctrl key again**.
4.  The circle will change to a **blue, spinning indicator** while your speech is processed. The transcribed text will be pasted at your cursor's position after a few seconds.
5.  To cancel recording or processing at any time, simply press the **`Esc` key**.

## Permissions
For the global hotkeys to work, your user account must have permission to read input devices. This is a one-time setup step.
```bash
sudo usermod -a -G input $USER
```
**You will need to log out and back in for this change to take effect.**

## License

[MIT](LICENSE)