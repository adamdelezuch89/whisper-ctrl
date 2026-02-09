"""
System Tray Icon for Whisper-Ctrl.

Provides a system tray icon with menu for quick access to settings and controls.
Uses AppIndicator3 on GNOME-based systems, QSystemTrayIcon elsewhere.
"""

import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal


class TrayIcon(QObject):
    """System tray icon with context menu (hybrid Qt/AppIndicator implementation)."""

    # Signals
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, app, parent=None):
        """
        Initialize system tray icon.

        Args:
            app: QApplication instance
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.app = app
        self.parent_widget = parent

        # Detect desktop environment
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        session_desktop = os.environ.get('DESKTOP_SESSION', '').lower()

        self.is_gnome = ('gnome' in desktop or 'zorin' in desktop or
                         'ubuntu' in desktop or 'gnome' in session_desktop)

        if self.is_gnome:
            print("🐧 Detected GNOME-based desktop - using AppIndicator3")
            self._init_appindicator()
        else:
            print("🖥️ Using QSystemTrayIcon")
            self._init_qsystemtray()

    def _init_appindicator(self):
        """Initialize AppIndicator3 (for GNOME/Zorin)."""
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import Gtk, AppIndicator3
            import threading

            self.use_appindicator = True
            self.Gtk = Gtk  # Store for later use

            # Get icon path
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
            icon_dir = os.path.dirname(os.path.dirname(__file__))

            # AppIndicator needs icon name (without extension) and searches in icon_path
            if os.path.exists(icon_path):
                # Set icon theme path to our directory
                self.indicator = AppIndicator3.Indicator.new(
                    "whisper-ctrl",
                    "icon",  # Name without extension
                    AppIndicator3.IndicatorCategory.APPLICATION_STATUS
                )
                self.indicator.set_icon_theme_path(icon_dir)
                print(f"📁 Using custom icon from: {icon_dir}")
            else:
                # Fallback to theme icon
                self.indicator = AppIndicator3.Indicator.new(
                    "whisper-ctrl",
                    "audio-input-microphone",
                    AppIndicator3.IndicatorCategory.APPLICATION_STATUS
                )
                print(f"🎨 Using theme icon: audio-input-microphone")
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_title("Whisper-Ctrl")

            # Create menu
            menu = Gtk.Menu()

            # Settings item
            item_settings = Gtk.MenuItem(label="Settings")
            item_settings.connect("activate", lambda _: self.settings_requested.emit())
            menu.append(item_settings)

            # Separator
            menu.append(Gtk.SeparatorMenuItem())

            # About item
            item_about = Gtk.MenuItem(label="About Whisper-Ctrl")
            item_about.connect("activate", lambda _: self._show_about())
            menu.append(item_about)

            # Separator
            menu.append(Gtk.SeparatorMenuItem())

            # Quit item
            item_quit = Gtk.MenuItem(label="Quit")
            item_quit.connect("activate", lambda _: self.quit_requested.emit())
            menu.append(item_quit)

            menu.show_all()
            self.indicator.set_menu(menu)

            # Start GTK main loop in separate thread (CRITICAL for AppIndicator to work!)
            def gtk_main_loop():
                Gtk.main()

            self.gtk_thread = threading.Thread(target=gtk_main_loop, daemon=True)
            self.gtk_thread.start()

            print("✅ AppIndicator3 initialized + GTK loop started")

        except ImportError as e:
            print(f"⚠️ Failed to load AppIndicator3: {e}")
            print("   Falling back to QSystemTrayIcon")
            self.use_appindicator = False
            self._init_qsystemtray()
        except Exception as e:
            print(f"⚠️ Error initializing AppIndicator3: {e}")
            print("   Falling back to QSystemTrayIcon")
            self.use_appindicator = False
            self._init_qsystemtray()

    def _init_qsystemtray(self):
        """Initialize QSystemTrayIcon (for KDE/Windows/other)."""
        self.use_appindicator = False

        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠️ WARNING: System tray is not available on this system!")
            print("   Make sure AppIndicator extension is enabled (GNOME/Zorin)")
            print("   Install: sudo apt install gnome-shell-extension-appindicator")

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.parent_widget)

        # Load icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = QIcon.fromTheme("audio-input-microphone")
            if icon.isNull():
                icon = self.app.style().standardIcon(self.app.style().StandardPixmap.SP_MediaPlay)

        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Whisper-Ctrl")

        # Create context menu
        self._create_qt_menu()

        # Show tray icon
        self.tray_icon.setVisible(True)
        self.tray_icon.show()

        print(f"✅ QSystemTrayIcon initialized (visible: {self.tray_icon.isVisible()})")

    def _create_qt_menu(self):
        """Create Qt context menu for QSystemTrayIcon."""
        menu = QMenu()

        # Settings action
        action_settings = QAction("Settings", self.app)
        action_settings.triggered.connect(self.settings_requested.emit)
        menu.addAction(action_settings)

        menu.addSeparator()

        # About action
        action_about = QAction("About Whisper-Ctrl", self.app)
        action_about.triggered.connect(self._show_about)
        menu.addAction(action_about)

        menu.addSeparator()

        # Quit action
        action_quit = QAction("Quit", self.app)
        action_quit.triggered.connect(self.quit_requested.emit)
        menu.addAction(action_quit)

        self.tray_icon.setContextMenu(menu)

    def _show_about(self):
        """Show about dialog."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            None,
            "About Whisper-Ctrl",
            "<h3>Whisper-Ctrl</h3>"
            "<p>Voice dictation application with local GPU transcription</p>"
            "<p>Version 2.0</p>"
            "<p>Licensed under MIT</p>"
        )

    def show_message(self, title: str, message: str, icon=None):
        """
        Show a system tray notification.

        Args:
            title: Notification title
            message: Notification message
            icon: Icon type (used only with QSystemTrayIcon)
        """
        if self.use_appindicator:
            # Use notify-send for AppIndicator
            try:
                import subprocess
                subprocess.run([
                    "notify-send",
                    "-i", "audio-input-microphone",
                    title,
                    message
                ], check=False, timeout=2)
            except Exception:
                pass
        else:
            # Use QSystemTrayIcon notification
            if icon is None:
                icon = QSystemTrayIcon.MessageIcon.Information
            if self.tray_icon.isVisible():
                self.tray_icon.showMessage(title, message, icon, 3000)

    def set_tooltip(self, tooltip: str):
        """Update the tray icon tooltip."""
        if self.use_appindicator:
            # AppIndicator doesn't support dynamic tooltips well
            # Tooltip is set via title during initialization
            pass
        else:
            self.tray_icon.setToolTip(tooltip)
