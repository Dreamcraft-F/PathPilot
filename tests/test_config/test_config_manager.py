"""
配置管理模块单元测试
"""

import os
import json
import tempfile
import pytest
from src.config.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 创建默认配置文件
        self.default_config = {
            "version": "1.0.0",
            "general": {
                "enable_logging": True,
                "log_level": "INFO",
                "database_path": "data/pathpilot.db"
            },
            "gui": {
                "悬浮球大小": 16,
                "自动隐藏时间": 10000
            }
        }
        
        default_config_path = os.path.join(self.config_dir, "default_config.json")
        with open(default_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.default_config, f, indent=2, ensure_ascii=False)
            
        # 初始化配置管理器
        self.config_manager = ConfigManager(self.config_dir)
        
    def teardown_method(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_load_default_config(self):
        """测试加载默认配置"""
        self.config_manager.load()
        
        # 验证配置加载成功
        assert self.config_manager.get("version") == "1.0.0"
        assert self.config_manager.get("general.enable_logging") == True
        assert self.config_manager.get("general.log_level") == "INFO"
        assert self.config_manager.get("general.database_path") == "data/pathpilot.db"
        assert self.config_manager.get("gui.悬浮球大小") == 16
        assert self.config_manager.get("gui.自动隐藏时间") == 10000
        
    def test_get_with_default(self):
        """测试获取配置项时使用默认值"""
        self.config_manager.load()
        
        # 测试存在的配置项
        assert self.config_manager.get("version") == "1.0.0"
        
        # 测试不存在的配置项，返回默认值
        assert self.config_manager.get("nonexistent", "default") == "default"
        assert self.config_manager.get("general.nonexistent", 123) == 123
        
    def test_set_config(self):
        """测试设置配置项"""
        self.config_manager.load()
        
        # 设置新值
        self.config_manager.set("general.log_level", "DEBUG")
        assert self.config_manager.get("general.log_level") == "DEBUG"
        
        # 设置新配置项
        self.config_manager.set("general.new_setting", "new_value")
        assert self.config_manager.get("general.new_setting") == "new_value"
        
    def test_save_and_reload(self):
        """测试保存和重新加载配置"""
        self.config_manager.load()
        
        # 修改配置
        self.config_manager.set("general.log_level", "DEBUG")
        self.config_manager.set("general.new_setting", "new_value")
        
        # 保存配置
        self.config_manager.save()
        
        # 创建新的配置管理器实例
        new_config_manager = ConfigManager(self.config_dir)
        new_config_manager.load()
        
        # 验证配置已保存并重新加载
        assert new_config_manager.get("general.log_level") == "DEBUG"
        assert new_config_manager.get("general.new_setting") == "new_value"
        
    def test_merge_config(self):
        """测试配置合并"""
        # 创建用户配置文件
        user_config = {
            "general": {
                "log_level": "WARNING",
                "user_setting": "user_value"
            },
            "gui": {
                "悬浮球大小": 24
            }
        }
        
        user_config_path = os.path.join(self.config_dir, "user_config.json")
        with open(user_config_path, 'w', encoding='utf-8') as f:
            json.dump(user_config, f, indent=2, ensure_ascii=False)
            
        # 重新加载配置
        self.config_manager.load()
        
        # 验证配置合并
        assert self.config_manager.get("general.log_level") == "WARNING"  # 用户配置覆盖默认配置
        assert self.config_manager.get("general.user_setting") == "user_value"  # 新增用户配置
        assert self.config_manager.get("gui.悬浮球大小") == 24  # 用户配置覆盖默认配置
        assert self.config_manager.get("general.enable_logging") == True  # 保留默认配置
        
    def test_load_nonexistent_config(self):
        """测试加载不存在的配置文件"""
        # 使用不存在的配置目录
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        config_manager = ConfigManager(nonexistent_dir)
        
        # 加载配置（应该使用空配置）
        config_manager.load()
        
        # 验证配置为空
        assert config_manager.get("version") is None
        assert config_manager.get("nonexistent", "default") == "default"