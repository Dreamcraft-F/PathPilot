"""
PathPilot 设置页面模块

使用 PySide6-Fluent-Widgets 实现设置界面。
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QScrollArea
from PySide6.QtCore import Qt, Signal

from qfluentwidgets import (
    CardWidget, BodyLabel, CaptionLabel,
    SwitchButton, PushButton, PrimaryPushButton,
    InfoBar, InfoBarPosition,
    FluentIcon as FIF
)


class SettingsPage(QWidget):
    """设置页面"""
    
    # 信号
    autostart_changed = Signal(bool)  # 自启动开关变更
    export_requested = Signal(str)  # 导出请求 (格式: csv/json)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_page")
        
        # 创建滚动区域
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("settings_scroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # 创建内容容器
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(16, 8, 16, 8)
        self.layout.setSpacing(12)
        
        # 初始化各个设置卡片
        self._setup_autostart_card()
        self._setup_export_card()
        
        # 添加弹性空间
        self.layout.addStretch()
        
        # 设置滚动区域
        scroll_area.setWidget(content_widget)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
    def _setup_autostart_card(self):
        """设置开机自启动卡片"""
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(8)
        
        # 标题行
        title_layout = QHBoxLayout()
        title_label = BodyLabel("开机自启动")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 开关
        self.autostart_switch = SwitchButton(self)
        self.autostart_switch.setOnText("开启")
        self.autostart_switch.setOffText("关闭")
        self.autostart_switch.checkedChanged.connect(self._on_autostart_changed)
        title_layout.addWidget(self.autostart_switch)
        
        card_layout.addLayout(title_layout)
        
        # 描述
        desc_label = CaptionLabel("启动 Windows 时自动运行 PathPilot")
        card_layout.addWidget(desc_label)
        
        self.layout.addWidget(card)
        
    def _setup_export_card(self):
        """设置导出功能卡片"""
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(8)
        
        # 标题
        title_label = BodyLabel("导出历史记录")
        title_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(title_label)
        
        # 描述
        desc_label = CaptionLabel("将访问历史导出为文件")
        card_layout.addWidget(desc_label)
        
        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.export_csv_btn = PushButton("导出 CSV", self)
        self.export_csv_btn.setIcon(FIF.DOCUMENT)
        self.export_csv_btn.clicked.connect(lambda: self._on_export("csv"))
        button_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = PushButton("导出 JSON", self)
        self.export_json_btn.setIcon(FIF.CODE)
        self.export_json_btn.clicked.connect(lambda: self._on_export("json"))
        button_layout.addWidget(self.export_json_btn)
        
        button_layout.addStretch()
        
        card_layout.addLayout(button_layout)
        
        self.layout.addWidget(card)
        
    def _on_autostart_changed(self, checked: bool):
        """自启动开关变更"""
        self.autostart_changed.emit(checked)
        
    def _on_export(self, format_type: str):
        """导出按钮点击"""
        # 弹出文件保存对话框
        if format_type == "csv":
            file_filter = "CSV 文件 (*.csv)"
            default_name = "pathpilot_export.csv"
        else:
            file_filter = "JSON 文件 (*.json)"
            default_name = "pathpilot_export.json"
            
        # 获取文档目录作为默认路径
        default_dir = os.path.join(os.path.expanduser("~"), "Documents")
        default_path = os.path.join(default_dir, default_name)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出历史记录",
            default_path,
            file_filter
        )
        
        if file_path:
            self.export_requested.emit(file_path)
            
    def set_autostart_state(self, enabled: bool):
        """设置自启动开关状态（不触发信号）"""
        self.autostart_switch.blockSignals(True)
        self.autostart_switch.setChecked(enabled)
        self.autostart_switch.blockSignals(False)
        
    def show_success(self, message: str):
        """显示成功提示"""
        InfoBar.success(
            title="成功",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def show_error(self, message: str):
        """显示错误提示"""
        InfoBar.error(
            title="错误",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
