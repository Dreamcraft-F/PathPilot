"""
PathPilot 图标生成模块

直接使用用户提供的透明背景图标。
"""

import os
import sys
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon, QImage
from PySide6.QtCore import Qt


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


def _load_pixmap(size: int) -> QPixmap:
    """加载图标并缩放"""
    img = QImage(_ICON_PATH)
    if img.isNull():
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(80, 140, 230))
        return pixmap
    return QPixmap.fromImage(img).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def create_icon(size: int = 64) -> QIcon:
    """正常图标"""
    return QIcon(_load_pixmap(size))


def create_privacy_icon(size: int = 64) -> QIcon:
    """隐私模式图标（灰度）"""
    img = QImage(_ICON_PATH)
    if img.isNull():
        return create_icon(size)

    gray = img.convertToFormat(QImage.Format_Grayscale8).convertToFormat(QImage.Format_ARGB32)
    pixmap = QPixmap.fromImage(gray).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QIcon(pixmap)


def create_pulse_icon(size: int = 64) -> QIcon:
    """脉冲图标（正常图标即可）"""
    return create_icon(size)
