"""
Feedback Widget for Whisper-Ctrl.

A frameless, transparent widget that follows the cursor and displays
visual feedback for the application state (recording, processing).
"""

import enum
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QCursor
from PySide6.QtCore import Qt, QTimer, QPointF


class FeedbackWidget(QWidget):
    """
    A frameless, transparent widget that displays feedback next to the cursor.

    Shows different animations based on the application state:
    - RECORDING: Pulsing red circle
    - PROCESSING: Spinning blue arc
    - HIDDEN: Not visible
    """

    class Mode(enum.Enum):
        """Widget display modes."""
        HIDDEN = "hidden"
        RECORDING = "recording"
        PROCESSING = "processing"

    def __init__(self, offset_x: int = 2, offset_y: int = 2):
        """
        Initialize the feedback widget.

        Args:
            offset_x: X offset from cursor position (pixels)
            offset_y: Y offset from cursor position (pixels)
        """
        super().__init__()
        self.mode = self.Mode.HIDDEN

        # Window configuration
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Prevents showing up in the taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.setFixedSize(40, 40)

        # Cursor offset configuration
        self.cursor_offset_x = offset_x
        self.cursor_offset_y = offset_y

        # Recording animation (pulsing)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update)
        self.pulse_radius = 5.0
        self.pulse_direction = 1

        # Processing animation (spinning)
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self.update)
        self.spinner_angle = 0

    def set_offset(self, offset_x: int, offset_y: int):
        """
        Update cursor offset.

        Args:
            offset_x: X offset from cursor position
            offset_y: Y offset from cursor position
        """
        self.cursor_offset_x = offset_x
        self.cursor_offset_y = offset_y

    def show_recording(self):
        """Show recording animation (pulsing red circle)."""
        self.spinner_timer.stop()
        self.mode = self.Mode.RECORDING
        if not self.pulse_timer.isActive():
            self.pulse_timer.start(50)  # Pulse speed (50ms = 20 FPS)
        self.show()

    def show_processing(self):
        """Show processing animation (spinning blue arc)."""
        self.pulse_timer.stop()
        self.mode = self.Mode.PROCESSING
        if not self.spinner_timer.isActive():
            self.spinner_timer.start(15)  # Spinner speed (15ms ≈ 67 FPS)
        self.show()

    def hide_feedback(self):
        """Hide the feedback widget."""
        self.mode = self.Mode.HIDDEN
        self.pulse_timer.stop()
        self.spinner_timer.stop()
        self.hide()

    def follow_cursor(self):
        """Update widget position to follow the cursor."""
        if self.isVisible():
            pos = QCursor.pos()
            self.move(
                pos.x() + self.cursor_offset_x,
                pos.y() + self.cursor_offset_y
            )

    def paintEvent(self, event):
        """Paint the widget based on current mode."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.mode == self.Mode.RECORDING:
            self._paint_recording(painter)
        elif self.mode == self.Mode.PROCESSING:
            self._paint_processing(painter)

    def _paint_recording(self, painter: QPainter):
        """Paint the recording animation (pulsing red circle)."""
        # Animate pulse radius
        self.pulse_radius += 0.2 * self.pulse_direction
        if not 5 <= self.pulse_radius <= 8:
            self.pulse_direction *= -1

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 0, 0, 200))  # Red, semi-transparent
        center = QPointF(self.width() / 2, self.height() / 2)
        painter.drawEllipse(center, self.pulse_radius, self.pulse_radius)

    def _paint_processing(self, painter: QPainter):
        """Paint the processing animation (spinning blue arc)."""
        # Animate spinner angle
        self.spinner_angle = (self.spinner_angle + 6) % 360

        pen = QPen(QColor(0, 120, 255, 220))  # Blue
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.drawArc(rect, self.spinner_angle * 16, 90 * 16)
