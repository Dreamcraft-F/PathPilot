"""
GUI模块单元测试
"""

import sys
import pytest
from datetime import datetime

# 尝试导入PySide6，如果不可用则跳过测试
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtTest import QTest
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from src.database.models import PathRecord

# 如果PySide6可用，导入GUI模块
if PYSIDE6_AVAILABLE:
    from src.gui.tray_icon import TrayIcon
    from src.gui.floating_ball import FloatingBall
    from src.gui.main_window import MainWindow

# 如果PySide6不可用，跳过所有测试
pytestmark = pytest.mark.skipif(not PYSIDE6_AVAILABLE, reason="PySide6 not installed")


# 创建全局QApplication实例
@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestTrayIcon:
    """TrayIcon 测试类"""
    
    def test_create_tray_icon(self, qapp):
        """测试创建托盘图标"""
        tray_icon = TrayIcon()
        
        # 验证托盘图标创建成功
        assert tray_icon is not None
        assert tray_icon.toolTip() == "PathPilot"
        
    def test_privacy_mode(self, qapp):
        """测试隐私模式"""
        tray_icon = TrayIcon()
        
        # 默认不是隐私模式
        assert tray_icon.privacy_mode == False
        
        # 设置隐私模式
        tray_icon.set_privacy_mode(True)
        assert tray_icon.privacy_mode == True
        assert tray_icon.privacy_action.isChecked() == True
        
        # 取消隐私模式
        tray_icon.set_privacy_mode(False)
        assert tray_icon.privacy_mode == False
        assert tray_icon.privacy_action.isChecked() == False


class TestFloatingBall:
    """FloatingBall 测试类"""
    
    def test_create_floating_ball(self, qapp):
        """测试创建悬浮球"""
        ball = FloatingBall(size=16, opacity=0.7)
        
        # 验证悬浮球创建成功
        assert ball is not None
        assert ball.ball_size == 16
        assert ball.opacity == 0.7
        
    def test_set_size(self, qapp):
        """测试设置大小"""
        ball = FloatingBall(size=16)
        
        # 设置新大小
        ball.set_size(24)
        assert ball.ball_size == 24
        
    def test_set_opacity(self, qapp):
        """测试设置透明度"""
        ball = FloatingBall(opacity=0.7)
        
        # 设置新透明度
        ball.set_opacity(0.5)
        assert ball.opacity == 0.5


class TestMainWindow:
    """MainWindow 测试类"""
    
    def test_create_main_window(self, qapp):
        """测试创建主窗口"""
        window = MainWindow()
        
        # 验证主窗口创建成功
        assert window is not None
        assert window.windowTitle() == "PathPilot"
        assert window.width() == 460
        assert window.height() == 560
        
    def test_update_path_list(self, qapp):
        """测试更新路径列表"""
        window = MainWindow()
        
        # 创建测试数据
        records = [
            PathRecord(
                path="c:\\users\\test\\documents",
                first_visit=datetime.now(),
                last_visit=datetime.now(),
                visit_count=5,
                importance_score=150
            ),
            PathRecord(
                path="c:\\users\\test\\pictures",
                first_visit=datetime.now(),
                last_visit=datetime.now(),
                visit_count=3,
                importance_score=120
            )
        ]
        
        # 更新路径列表
        window.update_path_list(records)
        
        # 验证更新成功（不报错即为成功）
        assert window.directory_page is not None
        
    def test_privacy_mode(self, qapp):
        """测试隐私模式"""
        window = MainWindow()
        
        # 默认不是隐私模式
        assert window.privacy_mode == False
        
        # 设置隐私模式
        window.set_privacy_mode(True)
        assert window.privacy_mode == True