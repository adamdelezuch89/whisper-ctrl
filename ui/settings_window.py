"""
Settings Window for Whisper-Ctrl.

Provides a user-friendly GUI for configuring all application settings.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QRadioButton,
    QLineEdit, QLabel, QPushButton, QFormLayout, QGroupBox,
    QComboBox, QCheckBox, QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from core.config import ConfigManager


class SettingsWindow(QWidget):
    """Settings window with tabbed interface for all configuration options."""

    # Signal emitted when settings are saved
    settings_changed = Signal()

    def __init__(self, config: ConfigManager, parent=None):
        """
        Initialize settings window.

        Args:
            config: ConfigManager instance
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Whisper-Ctrl Settings")
        self.resize(500, 400)

        self._init_ui()
        self.load_current_settings()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # Tabbed interface
        self.tabs = QTabWidget()

        # Create tabs
        self.tab_backend = self._create_backend_tab()
        self.tab_audio = self._create_audio_tab()
        self.tab_hotkey = self._create_hotkey_tab()
        self.tab_advanced = self._create_advanced_tab()

        self.tabs.addTab(self.tab_backend, "Backend")
        self.tabs.addTab(self.tab_audio, "Audio")
        self.tabs.addTab(self.tab_hotkey, "Hotkey")
        self.tabs.addTab(self.tab_advanced, "Advanced")

        layout.addWidget(self.tabs)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.btn_reset)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.close)
        button_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save && Apply")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.save_settings)
        button_layout.addWidget(self.btn_save)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_backend_tab(self) -> QWidget:
        """Create the Backend configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Backend selection
        backend_group = QGroupBox("Transcription Backend")
        backend_layout = QVBoxLayout()

        self.radio_local = QRadioButton("Local GPU (faster-whisper)")
        self.radio_local.setToolTip("Use your local GPU for transcription. Free and private.")
        backend_layout.addWidget(self.radio_local)

        self.radio_cloud = QRadioButton("OpenAI API (Cloud)")
        self.radio_cloud.setToolTip("Use OpenAI's API for transcription. Requires API key and internet.")
        backend_layout.addWidget(self.radio_cloud)

        backend_group.setLayout(backend_layout)
        layout.addWidget(backend_group)

        # Local GPU settings
        self.group_local = QGroupBox("Local GPU Configuration")
        local_layout = QFormLayout()

        self.combo_model_size = QComboBox()
        self.combo_model_size.addItems([
            "tiny", "base", "small", "medium", "large-v2", "large-v3"
        ])
        self.combo_model_size.setToolTip("Larger models are more accurate but slower")
        local_layout.addRow("Model Size:", self.combo_model_size)

        self.combo_device = QComboBox()
        self.combo_device.addItems(["cuda", "cpu"])
        self.combo_device.setToolTip("Use CUDA for GPU acceleration, CPU as fallback")
        local_layout.addRow("Device:", self.combo_device)

        self.combo_compute_type = QComboBox()
        self.combo_compute_type.addItems(["float16", "int8", "float32"])
        self.combo_compute_type.setToolTip("float16 is fastest on GPU, int8 for smaller VRAM")
        local_layout.addRow("Compute Type:", self.combo_compute_type)

        self.group_local.setLayout(local_layout)
        layout.addWidget(self.group_local)

        # OpenAI API settings
        self.group_cloud = QGroupBox("OpenAI API Configuration")
        cloud_layout = QFormLayout()

        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_key.setPlaceholderText("sk-...")
        cloud_layout.addRow("API Key:", self.input_api_key)

        self.btn_show_api_key = QPushButton("Show")
        self.btn_show_api_key.setCheckable(True)
        self.btn_show_api_key.clicked.connect(self._toggle_api_key_visibility)
        cloud_layout.addRow("", self.btn_show_api_key)

        self.group_cloud.setLayout(cloud_layout)
        layout.addWidget(self.group_cloud)

        # Connect radio buttons to show/hide groups
        self.radio_local.toggled.connect(self._update_backend_visibility)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_audio_tab(self) -> QWidget:
        """Create the Audio configuration tab."""
        widget = QWidget()
        layout = QFormLayout()

        self.combo_language = QComboBox()
        self.combo_language.addItems([
            "auto", "en", "pl", "de", "fr", "es", "it", "ru", "ja", "zh"
        ])
        self.combo_language.setToolTip("Language for transcription. 'auto' will detect automatically.")
        layout.addRow("Language:", self.combo_language)

        self.check_vad = QCheckBox("Enable Voice Activity Detection")
        self.check_vad.setToolTip("Filter out silence and non-speech audio")
        layout.addRow("", self.check_vad)

        layout.addRow(QLabel(""))  # Spacer

        # VAD Parameters group
        vad_group = QGroupBox("VAD Parameters")
        vad_layout = QFormLayout()

        self.spin_vad_threshold = QDoubleSpinBox()
        self.spin_vad_threshold.setRange(0.0, 1.0)
        self.spin_vad_threshold.setSingleStep(0.05)
        self.spin_vad_threshold.setValue(0.5)
        vad_layout.addRow("Threshold:", self.spin_vad_threshold)

        self.spin_min_speech = QDoubleSpinBox()
        self.spin_min_speech.setRange(0, 2000)
        self.spin_min_speech.setSuffix(" ms")
        self.spin_min_speech.setValue(250)
        vad_layout.addRow("Min Speech Duration:", self.spin_min_speech)

        self.spin_min_silence = QDoubleSpinBox()
        self.spin_min_silence.setRange(0, 2000)
        self.spin_min_silence.setSuffix(" ms")
        self.spin_min_silence.setValue(700)
        vad_layout.addRow("Min Silence Duration:", self.spin_min_silence)

        vad_group.setLayout(vad_layout)
        layout.addRow(vad_group)

        widget.setLayout(layout)
        return widget

    def _create_hotkey_tab(self) -> QWidget:
        """Create the Hotkey configuration tab."""
        widget = QWidget()
        layout = QFormLayout()

        self.combo_hotkey = QComboBox()
        self.combo_hotkey.addItems([
            "Double Ctrl (default)",
            "Double Alt",
            "Ctrl + Space",
            "Custom"
        ])
        layout.addRow("Activation Hotkey:", self.combo_hotkey)

        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(0.1, 1.0)
        self.spin_threshold.setSingleStep(0.05)
        self.spin_threshold.setValue(0.4)
        self.spin_threshold.setSuffix(" s")
        self.spin_threshold.setToolTip("Time window for double-press detection")
        layout.addRow("Double-Press Threshold:", self.spin_threshold)

        widget.setLayout(layout)
        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create the Advanced settings tab."""
        widget = QWidget()
        layout = QFormLayout()

        self.check_notifications = QCheckBox("Show desktop notifications")
        layout.addRow("", self.check_notifications)

        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("Feedback Widget Offset:"))

        self.spin_offset_x = QDoubleSpinBox()
        self.spin_offset_x.setRange(-100, 100)
        self.spin_offset_x.setValue(2)
        self.spin_offset_x.setSuffix(" px")
        layout.addRow("X Offset:", self.spin_offset_x)

        self.spin_offset_y = QDoubleSpinBox()
        self.spin_offset_y.setRange(-100, 100)
        self.spin_offset_y.setValue(2)
        self.spin_offset_y.setSuffix(" px")
        layout.addRow("Y Offset:", self.spin_offset_y)

        widget.setLayout(layout)
        return widget

    def _update_backend_visibility(self):
        """Update visibility of backend-specific settings."""
        is_local = self.radio_local.isChecked()
        self.group_local.setEnabled(is_local)
        self.group_cloud.setEnabled(not is_local)

    def _toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        if self.btn_show_api_key.isChecked():
            self.input_api_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show_api_key.setText("Hide")
        else:
            self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show_api_key.setText("Show")

    def load_current_settings(self):
        """Load current settings from config into UI."""
        # Backend
        backend = self.config.get("backend", "local")
        if backend == "local":
            self.radio_local.setChecked(True)
        else:
            self.radio_cloud.setChecked(True)

        # Local settings
        self.combo_model_size.setCurrentText(self.config.get("local.model_size", "large-v3"))
        self.combo_device.setCurrentText(self.config.get("local.device", "cuda"))
        self.combo_compute_type.setCurrentText(self.config.get("local.compute_type", "float16"))

        # OpenAI settings
        self.input_api_key.setText(self.config.get("openai.api_key", ""))

        # Audio
        self.combo_language.setCurrentText(self.config.get("audio.language", "pl"))
        self.check_vad.setChecked(self.config.get("audio.vad_enabled", True))
        self.spin_vad_threshold.setValue(self.config.get("audio.vad_parameters.threshold", 0.5))
        self.spin_min_speech.setValue(self.config.get("audio.vad_parameters.min_speech_duration_ms", 250))
        self.spin_min_silence.setValue(self.config.get("audio.vad_parameters.min_silence_duration_ms", 700))

        # Hotkey
        self.spin_threshold.setValue(self.config.get("hotkey.threshold", 0.4))

        # Advanced
        self.check_notifications.setChecked(self.config.get("ui.show_notifications", True))
        self.spin_offset_x.setValue(self.config.get("ui.feedback_widget_offset_x", 2))
        self.spin_offset_y.setValue(self.config.get("ui.feedback_widget_offset_y", 2))

        self._update_backend_visibility()

    def save_settings(self):
        """Save settings from UI to config."""
        try:
            # Backend
            backend = "local" if self.radio_local.isChecked() else "openai"
            self.config.set("backend", backend, save=False)

            # Local settings
            self.config.set("local.model_size", self.combo_model_size.currentText(), save=False)
            self.config.set("local.device", self.combo_device.currentText(), save=False)
            self.config.set("local.compute_type", self.combo_compute_type.currentText(), save=False)

            # OpenAI settings
            api_key = self.input_api_key.text().strip()
            self.config.set("openai.api_key", api_key, save=False)

            # Validate OpenAI config if selected
            if backend == "openai" and not self.config.validate_openai_config():
                QMessageBox.warning(
                    self,
                    "Invalid API Key",
                    "Please enter a valid OpenAI API key (starts with 'sk-')"
                )
                return

            # Audio
            self.config.set("audio.language", self.combo_language.currentText(), save=False)
            self.config.set("audio.vad_enabled", self.check_vad.isChecked(), save=False)
            self.config.set("audio.vad_parameters.threshold", self.spin_vad_threshold.value(), save=False)
            self.config.set("audio.vad_parameters.min_speech_duration_ms", int(self.spin_min_speech.value()), save=False)
            self.config.set("audio.vad_parameters.min_silence_duration_ms", int(self.spin_min_silence.value()), save=False)

            # Hotkey
            self.config.set("hotkey.threshold", self.spin_threshold.value(), save=False)

            # Advanced
            self.config.set("ui.show_notifications", self.check_notifications.isChecked(), save=False)
            self.config.set("ui.feedback_widget_offset_x", int(self.spin_offset_x.value()), save=False)
            self.config.set("ui.feedback_widget_offset_y", int(self.spin_offset_y.value()), save=False)

            # Save all at once
            self.config._save()

            # Emit signal
            self.settings_changed.emit()

            # Show confirmation
            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved successfully.\n\nNote: Some changes may require restarting the application."
            )

            self.close()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings: {e}"
            )

    def reset_to_defaults(self):
        """Reset all settings to default values."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self.load_current_settings()
            QMessageBox.information(self, "Reset Complete", "Settings have been reset to defaults.")
