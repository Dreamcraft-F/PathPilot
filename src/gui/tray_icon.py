"""
PathPilot 系统托盘图标模块

负责系统托盘图标的显示和交互。
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, Qt, QTimer

from src.gui.icons import create_icon, create_privacy_icon, create_pulse_icon


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标"""

    show_main_window_signal = Signal()
    toggle_privacy_mode_signal = Signal(bool)
    quit_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.icon_normal = create_icon(32)
        self.icon_privacy = create_privacy_icon(32)
        self.icon_pulse = create_pulse_icon(32)

        self.setIcon(self.icon_normal)
        self.setToolTip("PathPilot")

        self._setup_menu()
        self.activated.connect(self._on_activated)
        self.privacy_mode = False

    def _setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)

        show_action = menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window_signal.emit)

        menu.addSeparator()

        self.privacy_action = menu.addAction("隐私模式")
        self.privacy_action.setCheckable(True)
        self.privacy_action.triggered.connect(self._toggle_privacy_mode)

        menu.addSeparator()

        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self.quit_signal.emit)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window_signal.emit()

    def _toggle_privacy_mode(self, checked):
        self.privacy_mode = checked
        self.toggle_privacy_mode_signal.emit(checked)
        self._update_icon()

    def _update_icon(self):
        if self.privacy_mode:
            self.setIcon(self.icon_privacy)
            self.setToolTip("PathPilot · 隐私模式")
        else:
            self.setIcon(self.icon_normal)
            self.setToolTip("PathPilot")

    def set_privacy_mode(self, enabled: bool):
        self.privacy_mode = enabled
        self.privacy_action.setChecked(enabled)
        self._update_icon()

    def flash(self):
        """记录脉冲"""
        if self.privacy_mode:
            return
        self.setIcon(self.icon_pulse)
        QTimer.singleShot(300, self._restore_icon)

    def _restore_icon(self):
        if self.privacy_mode:
            self._update_icon()
        else:
            self.setIcon(self.icon_normal)
