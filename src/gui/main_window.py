"""
PathPilot 主窗口模块

使用 PySide6-Fluent-Widgets 的 FluentWindow 实现 Windows 11 原生质感。
"""

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon

from qfluentwidgets import (
    FluentWindow, MSFluentWindow, NavigationItemPosition,
    NavigationPushButton, FluentIcon as FIF,
    PrimaryPushButton, PushButton,
    InfoBar, InfoBarPosition,
    CardWidget, BodyLabel, CaptionLabel,
    SmoothScrollArea
)

from src.database.models import PathRecord
from src.gui.tree_view import DirectoryTreeView
from src.gui.time_view import TimeGroupWidget
from src.gui.settings_page import SettingsPage


class DirectoryPage(QWidget):
    """目录视图页面"""

    path_selected = Signal(str)
    path_deleted = Signal(str)
    favorite_toggled = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("directory_page")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(0)

        self.tree_view = DirectoryTreeView()
        layout.addWidget(self.tree_view)

        # 转发信号
        self.tree_view.path_selected.connect(self.path_selected.emit)
        self.tree_view.path_deleted.connect(self.path_deleted.emit)
        self.tree_view.favorite_toggled.connect(self.favorite_toggled.emit)

    def update_data(self, records: list):
        self.tree_view.update_data(records)

    def flash_item(self, path: str):
        self.tree_view.flash_item(path)


class TimePage(QWidget):
    """时间视图页面"""

    path_selected = Signal(str)
    path_deleted = Signal(str)
    favorite_toggled = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("time_page")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(0)

        self.time_view = TimeGroupWidget()
        layout.addWidget(self.time_view)

        # 转发信号
        self.time_view.path_selected.connect(self.path_selected.emit)
        self.time_view.path_deleted.connect(self.path_deleted.emit)
        self.time_view.favorite_toggled.connect(self.favorite_toggled.emit)

    def update_data(self, time_groups: dict):
        self.time_view.update_data(time_groups)

    def flash_item(self, path: str):
        self.time_view.flash_item(path)


class MainWindow(FluentWindow):
    """PathPilot 主窗口 - Fluent Design 风格"""

    # 信号（保持与 app.py 兼容）
    path_selected_signal = Signal(str)
    path_deleted_signal = Signal(str)
    privacy_mode_toggled_signal = Signal(bool)
    window_hidden_signal = Signal()
    clear_history_signal = Signal()
    favorite_toggled_signal = Signal(str, bool)
    open_this_pc_signal = Signal()
    view_changed_signal = Signal(str)
    
    # 设置页面信号
    autostart_changed_signal = Signal(bool)
    export_requested_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.privacy_mode = False
        self.current_view = "directory"

        # 设置窗口属性
        self.setWindowTitle("PathPilot")
        self.setWindowIcon(QIcon())
        self.resize(460, 560)
        self.setFixedSize(460, 560)

        # 置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # 移除默认标题栏的最小化/最大化按钮
        self.titleBar.minBtn.hide()
        self.titleBar.maxBtn.hide()

        # 创建页面
        self.directory_page = DirectoryPage(self)
        self.time_page = TimePage(self)
        self.settings_page = SettingsPage(self)

        # 添加导航项
        self._setup_navigation()

        # 连接信号
        self._setup_connections()

    def _setup_navigation(self):
        """设置导航面板"""
        # 添加子界面
        self.addSubInterface(
            self.directory_page,
            FIF.FOLDER,
            "目录",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.time_page,
            FIF.CALENDAR,
            "时间",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.settings_page,
            FIF.SETTING,
            "设置",
            position=NavigationItemPosition.BOTTOM
        )

        # 底部按钮
        self.navigationInterface.addItem(
            routeKey="this_pc",
            icon=FIF.HOME,
            text="此电脑",
            onClick=lambda: self.open_this_pc_signal.emit(),
            position=NavigationItemPosition.BOTTOM
        )

        self.navigationInterface.addItem(
            routeKey="clear",
            icon=FIF.DELETE,
            text="清空历史",
            onClick=self._clear_history,
            position=NavigationItemPosition.BOTTOM
        )

        self.navigationInterface.addItem(
            routeKey="privacy",
            icon=FIF.RINGER,
            text="隐私模式",
            onClick=self._toggle_privacy_from_nav,
            position=NavigationItemPosition.BOTTOM
        )

        # 默认选中目录
        self.navigationInterface.setCurrentItem("directory_page")

    def _setup_connections(self):
        """连接信号"""
        # 目录页信号
        self.directory_page.path_selected.connect(self.path_selected_signal.emit)
        self.directory_page.path_deleted.connect(self.path_deleted_signal.emit)
        self.directory_page.favorite_toggled.connect(self.favorite_toggled_signal.emit)

        # 时间页信号
        self.time_page.path_selected.connect(self.path_selected_signal.emit)
        self.time_page.path_deleted.connect(self.path_deleted_signal.emit)
        self.time_page.favorite_toggled.connect(self.favorite_toggled_signal.emit)
        
        # 设置页信号
        self.settings_page.autostart_changed.connect(self.autostart_changed_signal.emit)
        self.settings_page.export_requested.connect(self.export_requested_signal.emit)

    def _toggle_privacy_from_nav(self):
        """从导航栏切换隐私模式"""
        self.privacy_mode = not self.privacy_mode
        self.privacy_mode_toggled_signal.emit(self.privacy_mode)

    def _clear_history(self):
        """清空历史"""
        from qfluentwidgets import Dialog
        dialog = Dialog("确认清空", "确定要清空所有历史记录吗？", self)
        dialog.setTitleBarVisible(False)
        if dialog.exec():
            self.clear_history_signal.emit()

    # ── 公共接口（保持与 app.py 兼容）──────────────────────

    def hide_to_floating_ball(self):
        self.hide()
        self.window_hidden_signal.emit()

    def closeEvent(self, event):
        """重写关闭事件 - 隐藏到悬浮球而不是退出"""
        event.ignore()
        self.hide_to_floating_ball()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide_to_floating_ball()
        else:
            super().keyPressEvent(event)

    def update_path_list(self, records: list):
        self.directory_page.update_data(records)

    def update_time_view(self, time_groups: dict):
        self.time_page.update_data(time_groups)

    def set_privacy_mode(self, enabled: bool):
        self.privacy_mode = enabled

    def switch_view(self, view: str):
        """切换视图（供 app.py 调用）"""
        self.current_view = view
        if view == "directory":
            self.navigationInterface.setCurrentItem("directory_page")
        elif view == "time":
            self.navigationInterface.setCurrentItem("time_page")
