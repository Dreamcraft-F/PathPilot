"""
PathPilot 集成测试

测试应用的初始化和基本功能。
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.app import PathPilotApp
from src.config.config_manager import ConfigManager
from src.database.db_manager import DatabaseManager
from src.core.path_engine import PathCaptureEngine


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestPathPilotApp:
    """PathPilotApp 集成测试类"""
    
    def test_create_app(self, qapp):
        """测试创建应用"""
        app = PathPilotApp()
        
        # 验证应用创建成功
        assert app is not None
        assert app.app is not None
        
    def test_initialize_app(self, qapp):
        """测试初始化应用"""
        app = PathPilotApp()
        
        # 初始化应用
        app.initialize()
        
        # 验证各模块初始化成功
        assert app.config_manager is not None
        assert app.database_manager is not None
        assert app.path_engine is not None
        assert app.logger is not None
        assert app.tray_icon is not None
        assert app.floating_ball is not None
        assert app.main_window is not None
        
        # 清理
        app.quit()
        
    def test_privacy_mode(self, qapp):
        """测试隐私模式"""
        app = PathPilotApp()
        app.initialize()
        
        # 默认不是隐私模式
        assert app.privacy_mode == False
        
        # 开启隐私模式
        app.toggle_privacy_mode(True)
        assert app.privacy_mode == True
        assert app.tray_icon.privacy_mode == True
        assert app.main_window.privacy_mode == True
        
        # 关闭隐私模式
        app.toggle_privacy_mode(False)
        assert app.privacy_mode == False
        assert app.tray_icon.privacy_mode == False
        assert app.main_window.privacy_mode == False
        
        # 清理
        app.quit()
        
    def test_get_status(self, qapp):
        """测试获取状态"""
        app = PathPilotApp()
        app.initialize()
        
        # 获取状态
        status = app.get_status()
        
        # 验证状态
        assert "privacy_mode" in status
        assert "engine_running" in status
        assert "database_connected" in status
        
        # 清理
        app.quit()


class TestConfigManager:
    """ConfigManager 集成测试类"""
    
    def test_load_config(self):
        """测试加载配置"""
        config_manager = ConfigManager("config")
        config_manager.load()
        
        # 验证配置加载成功
        assert config_manager.config is not None
        assert "version" in config_manager.config
        
    def test_get_config_value(self):
        """测试获取配置值"""
        config_manager = ConfigManager("config")
        config_manager.load()
        
        # 获取配置值
        version = config_manager.get("version")
        assert version is not None
        
        # 获取不存在的配置值
        nonexistent = config_manager.get("nonexistent", "default")
        assert nonexistent == "default"


class TestDatabaseManager:
    """DatabaseManager 集成测试类"""
    
    def test_initialize_database(self):
        """测试初始化数据库"""
        # 使用内存数据库
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize()
        
        # 验证数据库初始化成功
        assert db_manager.connection is not None
        
        # 清理
        db_manager.close()
        
    def test_insert_and_get_record(self):
        """测试插入和获取记录"""
        from datetime import datetime
        from src.database.models import PathRecord
        
        # 使用内存数据库
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize()
        
        # 创建记录
        record = PathRecord(
            path="c:\\test\\path",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        
        # 插入记录
        db_manager.insert_path_record(record)
        
        # 获取记录
        retrieved_record = db_manager.get_path_record_by_path("c:\\test\\path")
        
        # 验证记录
        assert retrieved_record is not None
        assert retrieved_record.path == "c:\\test\\path"
        assert retrieved_record.visit_count == 1
        
        # 清理
        db_manager.close()


class TestPathCaptureEngine:
    """PathCaptureEngine 集成测试类"""
    
    def test_initialize_engine(self):
        """测试初始化引擎"""
        # 使用内存数据库
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize()
        
        # 创建配置
        config = {
            "engine": {
                "时间去重窗口": 5000,
                "最大最近路径": 20
            },
            "filters": {
                "excluded_paths": ["c:\\windows"],
                "excluded_patterns": []
            }
        }
        
        # 创建引擎
        engine = PathCaptureEngine(config, db_manager)
        
        # 验证引擎创建成功
        assert engine is not None
        assert engine.database is db_manager
        assert engine.config is config
        
        # 清理
        db_manager.close()
        
    def test_engine_status(self):
        """测试引擎状态"""
        # 使用内存数据库
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize()
        
        # 创建配置
        config = {
            "engine": {
                "时间去重窗口": 5000,
                "最大最近路径": 20
            },
            "filters": {
                "excluded_paths": ["c:\\windows"],
                "excluded_patterns": []
            }
        }
        
        # 创建引擎
        engine = PathCaptureEngine(config, db_manager)
        
        # 获取状态
        status = engine.get_engine_status()
        
        # 验证状态
        assert "is_running" in status
        assert "queue_size" in status
        
        # 清理
        db_manager.close()