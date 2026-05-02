"""
PathPilot 路径处理工具模块

提供路径规范化、验证和处理功能。
"""

import os
import re
from typing import Optional
from datetime import datetime, timedelta


class PathUtils:
    """路径处理工具类"""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        规范化路径
        
        Args:
            path: 原始路径
            
        Returns:
            规范化后的路径
        """
        # 转换为小写
        path = path.lower()
        
        # 统一路径分隔符
        path = path.replace('/', '\\')
        
        # 去除尾部斜杠
        if path.endswith('\\'):
            path = path.rstrip('\\')
            
        # 解析环境变量
        path = os.path.expandvars(path)
        
        return path
        
    @staticmethod
    def get_path_depth(path: str) -> int:
        """
        获取路径深度
        
        Args:
            path: 路径
            
        Returns:
            路径深度（层级数）
        """
        return path.count('\\')
        
    @staticmethod
    def is_parent_path(parent: str, child: str) -> bool:
        """
        判断是否是父路径
        
        Args:
            parent: 父路径
            child: 子路径
            
        Returns:
            如果child是parent的子路径返回True
        """
        parent_lower = parent.lower()
        child_lower = child.lower()
        return child_lower.startswith(parent_lower + '\\') or child_lower == parent_lower
        
    @staticmethod
    def matches_pattern(path: str, pattern: str) -> bool:
        """
        匹配路径模式（支持通配符 * 和 ?）
        
        Args:
            path: 路径
            pattern: 模式
            
        Returns:
            如果匹配返回True
        """
        # 首先转义反斜杠，然后将通配符转换为正则表达式
        escaped_pattern = pattern.replace('\\', '\\\\')
        regex = escaped_pattern.replace('*', '.*').replace('?', '.')
        # 使用fullmatch确保整个字符串匹配
        return re.fullmatch(regex, path, re.IGNORECASE) is not None
        
    @staticmethod
    def is_valid_path(path: str) -> bool:
        """
        验证路径是否有效
        
        Args:
            path: 路径
            
        Returns:
            如果路径有效返回True
        """
        try:
            # 检查路径是否包含非法字符
            illegal_chars = '<>"|?*'
            for char in illegal_chars:
                if char in path:
                    return False
                    
            # 检查路径长度
            if len(path) > 260:  # Windows最大路径长度
                return False
                
            return True
        except Exception:
            return False
            
    @staticmethod
    def get_parent_path(path: str) -> Optional[str]:
        """
        获取父路径
        
        Args:
            path: 路径
            
        Returns:
            父路径，如果已经是根路径返回None
        """
        parent = os.path.dirname(path)
        if parent == path:  # 已经是根路径
            return None
        return parent
        
    @staticmethod
    def join_paths(*args: str) -> str:
        """
        连接路径
        
        Args:
            *args: 路径部分
            
        Returns:
            连接后的路径
        """
        return os.path.join(*args)
        
    @staticmethod
    def expand_path(path: str) -> str:
        """
        展开路径（处理 ~ 和环境变量）
        
        Args:
            path: 路径
            
        Returns:
            展开后的路径
        """
        # 展开用户目录
        path = os.path.expanduser(path)
        
        # 展开环境变量
        path = os.path.expandvars(path)
        
        return path
        
    @staticmethod
    def get_path_parts(path: str) -> list:
        """
        获取路径的各个部分
        
        Args:
            path: 路径
            
        Returns:
            路径部分列表
        """
        # 分割路径
        parts = path.split('\\')
        
        # 过滤空字符串
        return [part for part in parts if part]
        
    @staticmethod
    def format_time(dt: datetime) -> str:
        """
        格式化时间为友好显示
        
        Args:
            dt: 时间
            
        Returns:
            格式化后的时间字符串
        """
        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        
        if dt.date() == today:
            return dt.strftime("%H:%M")
        elif dt.date() == yesterday:
            return f"昨天 {dt.strftime('%H:%M')}"
        elif (today - dt.date()).days < 7:
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            return f"{weekdays[dt.weekday()]} {dt.strftime('%H:%M')}"
        else:
            return dt.strftime("%m-%d %H:%M")