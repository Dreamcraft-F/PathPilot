"""
PathPilot 配置管理模块

负责加载、保存和管理应用程序配置。
"""

import json
import os
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "user_config.json")
        self.default_config_file = os.path.join(config_dir, "default_config.json")
        self.config: Dict[str, Any] = {}
        
    def load(self):
        """加载配置"""
        # 1. 加载默认配置
        default_config = self._load_json(self.default_config_file)
        
        # 2. 加载用户配置（如果存在）
        user_config = {}
        if os.path.exists(self.config_file):
            user_config = self._load_json(self.config_file)
            
        # 3. 合并配置（用户配置覆盖默认配置）
        self.config = self._merge_config(default_config, user_config)
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔的层级键（如 'general.database_path'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any):
        """
        设置配置项
        
        Args:
            key: 配置键，支持点号分隔的层级键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
    def save(self):
        """保存配置到文件"""
        self._save_json(self.config_file, self.config)
        
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """
        加载JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
            
    def _save_json(self, file_path: str, data: Dict[str, Any]):
        """
        保存数据到JSON文件
        
        Args:
            file_path: JSON文件路径
            data: 要保存的数据
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
            
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """
        合并配置（用户配置覆盖默认配置）
        
        Args:
            default: 默认配置
            user: 用户配置
            
        Returns:
            合并后的配置
        """
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result