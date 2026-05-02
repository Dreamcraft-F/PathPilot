"""
PathPilot 欢迎向导模块

首次运行时显示的欢迎界面。
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

from qfluentwidgets import (
    PrimaryPushButton, BodyLabel, CaptionLabel,
    TitleLabel, SubtitleLabel, FluentIcon as FIF,
    CardWidget
)


class WelcomeWizard(QWidget):
    """欢迎向导窗口"""
    
    # 信号
    finished = Signal()  # 向导完成
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcome_wizard")
        
        # 设置窗口属性 - 使用 Popup 类型去掉标题栏图标
        self.setWindowTitle("欢迎使用 PathPilot")
        self.setFixedSize(420, 480)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        
        # 设置UI
        self._setup_ui()
        
        # 居中显示
        self._center_window()
        
    def _center_window(self):
        """窗口居中"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def _setup_ui(self):
        """设置UI"""
        # 主布局
        self.setStyleSheet("""
            QWidget#welcome_wizard {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(0)
        
        # 标题区域
        title_label = TitleLabel("PathPilot")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #1a1a1a;")
        layout.addWidget(title_label)
        layout.addSpacing(4)
        
        # 副标题
        subtitle_label = SubtitleLabel("资源管理器隐形导航员")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 15px; color: #666666;")
        layout.addWidget(subtitle_label)
        layout.addSpacing(32)
        
        # 功能介绍卡片
        features_card = CardWidget()
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(20, 16, 20, 16)
        features_layout.setSpacing(12)
        
        features = [
            ("无感记录", "自动记录您在资源管理器中访问的路径"),
            ("快速跳转", "一键跳转到最近访问的文件夹"),
            ("收藏管理", "收藏常用路径，提高工作效率"),
            ("隐私保护", "支持隐私模式，暂停记录功能"),
        ]
        
        for title, desc in features:
            item = self._create_feature_item(title, desc)
            features_layout.addWidget(item)
        
        layout.addWidget(features_card)
        layout.addStretch()
        
        # 分隔线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)
        layout.addSpacing(20)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        start_btn = PrimaryPushButton("开始使用")
        start_btn.setFixedSize(120, 36)
        start_btn.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(start_btn)
        
        layout.addLayout(btn_layout)
        
    def _create_feature_item(self, title: str, desc: str) -> QWidget:
        """创建功能介绍项"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        
        # 标记点
        dot = QLabel("·")
        dot.setFixedWidth(16)
        dot.setAlignment(Qt.AlignCenter)
        dot.setStyleSheet("font-size: 20px; font-weight: bold; color: #0078d7;")
        layout.addWidget(dot)
        
        # 文本区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = BodyLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #1a1a1a;")
        text_layout.addWidget(title_label)
        
        desc_label = CaptionLabel(desc)
        desc_label.setStyleSheet("color: #666666;")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        return widget
        
    def _on_start_clicked(self):
        """开始使用按钮点击"""
        self.finished.emit()
        self.close()
