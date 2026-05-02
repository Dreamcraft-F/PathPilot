"""
PathPilot 悬浮球模块

直接显示透明背景图标，无装饰。
"""

import time
import os
import sys
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QMouseEvent, QImage


def _get_icon_path():
    """获取图标路径（兼容打包和开发环境）"""
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # 尝试多个路径
    paths = [
        os.path.join(base_dir, "src", "resources", "icon.png"),
        os.path.join(base_dir, "resources", "icon.png"),
        os.path.join(base_dir, "icon.png"),
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return os.path.join(base_dir, "src", "resources", "icon.png")


_ICON_PATH = _get_icon_path()


def _fix_win11_window(hwnd):
    """修复 Windows 11 窗口背景问题"""
    try:
        # 关闭圆角
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), 33,
            ctypes.byref(ctypes.c_int(1)), 4
        )
        # 关闭系统背景
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), 38,
            ctypes.byref(ctypes.c_int(1)), 4
        )
        # 去掉边框颜色
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), 34,
            ctypes.byref(ctypes.c_int(0)), 4
        )
    except Exception:
        pass


class FloatingBall(QWidget):
    """悬浮球"""

    clicked_signal = Signal()

    def __init__(self, parent=None, size: int = 48, opacity: float = 0.9):
        super().__init__(parent)

        self.ball_size = size
        self.opacity = opacity
        self.today_count = 0
        self.last_capture_time = time.time()

        # 加载图标
        self._icon_image = QImage(_ICON_PATH)

        # 窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(size, size)

        # 拖拽
        self._dragging = False
        self._drag_position = QPoint()
        self._drag_threshold = 5
        self._mouse_press_pos = QPoint()

        self.move_to_edge()

    def showEvent(self, event):
        """窗口显示时修复 Windows 11 背景"""
        super().showEvent(event)
        _fix_win11_window(int(self.winId()))

    def paintEvent(self, event):
        """绘制图标"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setOpacity(self.opacity)

        if not self._icon_image.isNull():
            # 使用高质量缩放
            scaled = self._icon_image.scaled(
                self.ball_size, self.ball_size,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            # 居中绘制
            x = (self.ball_size - scaled.width()) // 2
            y = (self.ball_size - scaled.height()) // 2
            painter.drawImage(x, y, scaled)
        else:
            # 图标加载失败，绘制默认圆形
            from PySide6.QtGui import QColor, QBrush
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#0078d7")))
            painter.drawEllipse(self.rect())

    # ── 鼠标 ──────────────────────────────────────────────

    def enterEvent(self, event):
        self.setWindowOpacity(min(self.opacity + 0.1, 1.0))

    def leaveEvent(self, event):
        self.setWindowOpacity(self.opacity)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._mouse_press_pos = event.globalPosition().toPoint()
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            if not self._dragging:
                delta = event.globalPosition().toPoint() - self._mouse_press_pos
                if abs(delta.x()) > self._drag_threshold or abs(delta.y()) > self._drag_threshold:
                    self._dragging = True
            if self._dragging:
                self.move(event.globalPosition().toPoint() - self._drag_position)
                event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if not self._dragging:
                self.clicked_signal.emit()
            self._dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked_signal.emit()

    # ── 位置 ──────────────────────────────────────────────

    def move_to_edge(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.ball_size - 16
        y = screen.height() // 2 - self.ball_size // 2
        self.move(x, y)

    # ── 接口 ──────────────────────────────────────────────

    def set_size(self, size: int):
        self.ball_size = size
        self.setFixedSize(size, size)
        self.update()

    def set_opacity(self, opacity: float):
        self.opacity = opacity
        self.setWindowOpacity(opacity)
        self.update()

    def update_usage(self, count: int):
        self.today_count = count
        self.last_capture_time = time.time()
        self.update()
