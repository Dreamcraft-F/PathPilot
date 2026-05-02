"""
PathPilot 去重处理器模块

负责去除重复的路径记录，包括基于时间和基于层级的去重。
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, Optional
from src.utils.path_utils import PathUtils


class TimeBasedDeduplicator:
    """基于时间的去重器"""
    
    def __init__(self, time_window_ms: int = 5000):
        """
        初始化基于时间的去重器
        
        Args:
            time_window_ms: 时间窗口（毫秒）
        """
        self.time_window = timedelta(milliseconds=time_window_ms)
        self.last_access_times: Dict[str, datetime] = {}
        
    def is_duplicate(self, path: str) -> bool:
        """
        判断是否是重复路径
        
        Args:
            path: 路径
            
        Returns:
            如果是重复路径返回True
        """
        now = datetime.now()
        
        if path in self.last_access_times:
            last_access = self.last_access_times[path]
            if now - last_access < self.time_window:
                return True
                
        # 更新最后访问时间
        self.last_access_times[path] = now
        return False
        
    def reset(self):
        """重置去重器"""
        self.last_access_times.clear()
        
    def get_last_access_time(self, path: str) -> Optional[datetime]:
        """
        获取路径的最后访问时间
        
        Args:
            path: 路径
            
        Returns:
            最后访问时间，不存在返回None
        """
        return self.last_access_times.get(path)


class HierarchicalDeduplicator:
    """基于层级的去重器"""
    
    def __init__(self, max_recent_paths: int = 20):
        """
        初始化基于层级的去重器
        
        Args:
            max_recent_paths: 最大最近路径数量
        """
        self.max_recent_paths = max_recent_paths
        self.recent_paths: OrderedDict[str, datetime] = OrderedDict()
        
    def is_duplicate(self, path: str) -> bool:
        """
        判断是否是重复路径
        
        Args:
            path: 路径
            
        Returns:
            如果是重复路径返回True
        """
        if not self.recent_paths:
            self.recent_paths[path] = datetime.now()
            return False
            
        last_path = next(reversed(self.recent_paths))
        
        # 检查是否是向上导航（从子目录返回父目录）
        if PathUtils.is_parent_path(path, last_path):
            # 如果父路径已经在最近列表中，移动到最新位置并返回True
            if path in self.recent_paths:
                self.recent_paths.move_to_end(path)
                return True
            # 否则，添加到列表（这是新的父路径访问）
            else:
                self.recent_paths[path] = datetime.now()
                # 保持列表大小
                while len(self.recent_paths) > self.max_recent_paths:
                    self.recent_paths.popitem(last=False)
                return False
                
        # 检查是否是向下导航（从父目录进入子目录）
        elif PathUtils.is_parent_path(last_path, path):
            # 如果子路径已经在最近列表中，移动到最新位置并返回True
            if path in self.recent_paths:
                self.recent_paths.move_to_end(path)
                return True
            # 否则，添加到列表（这是新的子路径访问）
            else:
                self.recent_paths[path] = datetime.now()
                # 保持列表大小
                while len(self.recent_paths) > self.max_recent_paths:
                    self.recent_paths.popitem(last=False)
                return False
                
        # 新路径，添加到列表
        self.recent_paths[path] = datetime.now()
        
        # 保持列表大小
        while len(self.recent_paths) > self.max_recent_paths:
            self.recent_paths.popitem(last=False)
            
        return False
        
    def reset(self):
        """重置去重器"""
        self.recent_paths.clear()
        
    def get_recent_paths(self) -> list:
        """
        获取最近访问的路径列表
        
        Returns:
            路径列表
        """
        return list(self.recent_paths.keys())
        
    def get_last_path(self) -> Optional[str]:
        """
        获取最后访问的路径
        
        Returns:
            最后访问的路径，不存在返回None
        """
        if self.recent_paths:
            return next(reversed(self.recent_paths))
        return None


class PathDeduplicator:
    """综合去重器"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        初始化综合去重器
        
        Args:
            config: 配置字典
        """
        config = config or {}
        engine_config = config.get('engine', {})
        
        # 创建基于时间的去重器
        time_window = engine_config.get('时间去重窗口', 5000)
        self.time_deduplicator = TimeBasedDeduplicator(time_window)
        
        # 创建基于层级的去重器
        max_recent_paths = engine_config.get('最大最近路径', 20)
        self.hierarchical_deduplicator = HierarchicalDeduplicator(max_recent_paths)
        
    def is_duplicate(self, path: str) -> bool:
        """
        判断是否是重复路径
        
        Args:
            path: 路径
            
        Returns:
            如果是重复路径返回True
        """
        # 1. 时间去重
        if self.time_deduplicator.is_duplicate(path):
            return True
            
        # 2. 层级去重
        if self.hierarchical_deduplicator.is_duplicate(path):
            return True
            
        return False
        
    def reset(self):
        """重置去重器"""
        self.time_deduplicator.reset()
        self.hierarchical_deduplicator.reset()
        
    def get_recent_paths(self) -> list:
        """
        获取最近访问的路径列表
        
        Returns:
            路径列表
        """
        return self.hierarchical_deduplicator.get_recent_paths()
        
    def get_last_path(self) -> Optional[str]:
        """
        获取最后访问的路径
        
        Returns:
            最后访问的路径，不存在返回None
        """
        return self.hierarchical_deduplicator.get_last_path()