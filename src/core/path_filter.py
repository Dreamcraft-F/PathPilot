"""
PathPilot 路径过滤器模块

负责过滤不应记录的路径，如系统路径、临时路径等。
"""

import re
from abc import ABC, abstractmethod
from typing import List, Optional
from src.utils.path_utils import PathUtils


class PathFilter(ABC):
    """路径过滤器基类"""
    
    @abstractmethod
    def should_exclude(self, path: str) -> bool:
        """
        判断是否应该排除路径
        
        Args:
            path: 路径
            
        Returns:
            如果应该排除返回True
        """
        pass


class SystemPathFilter(PathFilter):
    """系统路径过滤器"""
    
    def __init__(self):
        """初始化系统路径过滤器"""
        self.excluded_paths = [
            'c:\\windows',
            'c:\\program files',
            'c:\\program files (x86)',
            'c:\\$recycle.bin',
            'c:\\system volume information',
            'c:\\recovery',
            'c:\\boot',
            'c:\\documents and settings',
            'c:\\perflogs'
        ]
        
    def should_exclude(self, path: str) -> bool:
        """
        检查是否是系统路径
        
        Args:
            path: 路径
            
        Returns:
            如果是系统路径返回True
        """
        path_lower = path.lower()
        return any(path_lower.startswith(excluded) for excluded in self.excluded_paths)


class TemporaryPathFilter(PathFilter):
    """临时路径过滤器"""
    
    def __init__(self):
        """初始化临时路径过滤器"""
        self.temp_patterns = [
            r'^.*\\temp\\.*$',
            r'^.*\\tmp\\.*$',
            r'^.*\\temporary internet files\\.*$',
            r'^.*\.tmp$',
            r'^.*\.temp$',
            r'^.*\.bak$',
            r'^.*\.swp$',
            r'^.*~$'
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.temp_patterns]
        
    def should_exclude(self, path: str) -> bool:
        """
        检查是否是临时路径
        
        Args:
            path: 路径
            
        Returns:
            如果是临时路径返回True
        """
        # 将路径转换为小写进行匹配
        path_lower = path.lower()
        return any(pattern.match(path_lower) for pattern in self.compiled_patterns)


class DevelopmentPathFilter(PathFilter):
    """开发路径过滤器"""
    
    def __init__(self):
        """初始化开发路径过滤器"""
        self.dev_patterns = [
            r'^.*\\.git\\.*$',
            r'^.*\\.svn\\.*$',
            r'^.*\\.hg\\.*$',
            r'^.*\\node_modules\\.*$',
            r'^.*\\vendor\\.*$',
            r'^.*\\build\\.*$',
            r'^.*\\dist\\.*$',
            r'^.*\\out\\.*$',
            r'^.*\\target\\.*$',
            r'^.*\\__pycache__\\.*$',
            r'^.*\\.pytest_cache\\.*$',
            r'^.*\\.mypy_cache\\.*$'
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.dev_patterns]
        
    def should_exclude(self, path: str) -> bool:
        """
        检查是否是开发路径
        
        Args:
            path: 路径
            
        Returns:
            如果是开发路径返回True
        """
        return any(pattern.match(path) for pattern in self.compiled_patterns)


class ApplicationDataFilter(PathFilter):
    """应用数据路径过滤器"""
    
    def __init__(self):
        """初始化应用数据路径过滤器"""
        self.app_data_patterns = [
            r'^.*\\appdata\\.*$',
            r'^.*\\application data\\.*$',
            r'^.*\\local settings\\.*$',
            r'^.*\\cookies\\.*$',
            r'^.*\\recent\\.*$',
            r'^.*\\sendto\\.*$',
            r'^.*\\start menu\\.*$',
            r'^.*\\templates\\.*$'
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.app_data_patterns]
        
    def should_exclude(self, path: str) -> bool:
        """
        检查是否是应用数据路径
        
        Args:
            path: 路径
            
        Returns:
            如果是应用数据路径返回True
        """
        return any(pattern.match(path) for pattern in self.compiled_patterns)


class PathDepthFilter(PathFilter):
    """路径深度过滤器"""
    
    def __init__(self, max_depth: int = 10):
        """
        初始化路径深度过滤器
        
        Args:
            max_depth: 最大路径深度
        """
        self.max_depth = max_depth
        
    def should_exclude(self, path: str) -> bool:
        """
        检查路径深度是否超过限制
        
        Args:
            path: 路径
            
        Returns:
            如果路径深度超过限制返回True
        """
        return PathUtils.get_path_depth(path) > self.max_depth


class CompositePathFilter(PathFilter):
    """组合路径过滤器"""
    
    def __init__(self, filters: Optional[List[PathFilter]] = None):
        """
        初始化组合路径过滤器
        
        Args:
            filters: 过滤器列表
        """
        self.filters = filters or []
        
    def add_filter(self, path_filter: PathFilter):
        """
        添加过滤器
        
        Args:
            path_filter: 路径过滤器
        """
        self.filters.append(path_filter)
        
    def remove_filter(self, path_filter: PathFilter):
        """
        移除过滤器
        
        Args:
            path_filter: 路径过滤器
        """
        if path_filter in self.filters:
            self.filters.remove(path_filter)
            
    def should_exclude(self, path: str) -> bool:
        """
        检查是否应该排除路径
        
        Args:
            path: 路径
            
        Returns:
            如果任一过滤器认为应该排除返回True
        """
        return any(f.should_exclude(path) for f in self.filters)


class CustomPathFilter(PathFilter):
    """自定义路径过滤器"""
    
    def __init__(self, excluded_paths: Optional[List[str]] = None, 
                 excluded_patterns: Optional[List[str]] = None):
        """
        初始化自定义路径过滤器
        
        Args:
            excluded_paths: 排除的路径列表
            excluded_patterns: 排除的模式列表（正则表达式）
        """
        self.excluded_paths = [p.lower() for p in (excluded_paths or [])]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in (excluded_patterns or [])]
        
    def should_exclude(self, path: str) -> bool:
        """
        检查是否应该排除路径
        
        Args:
            path: 路径
            
        Returns:
            如果应该排除返回True
        """
        path_lower = path.lower()
        
        # 检查排除路径
        for excluded in self.excluded_paths:
            if '*' in excluded or '?' in excluded:
                # 通配符匹配：先转义正则表达式特殊字符，然后替换通配符
                escaped = re.escape(excluded)
                pattern = escaped.replace(r'\*', '.*').replace(r'\?', '.')
                if re.fullmatch(pattern, path_lower):
                    return True
            else:
                # 精确匹配或前缀匹配
                if path_lower == excluded or path_lower.startswith(excluded + '\\'):
                    return True
                    
        # 检查排除模式
        return any(pattern.match(path_lower) for pattern in self.compiled_patterns)


def create_default_filter(config: Optional[dict] = None) -> CompositePathFilter:
    """
    创建默认的组合过滤器
    
    Args:
        config: 配置字典
        
    Returns:
        组合路径过滤器
    """
    config = config or {}
    filters_config = config.get('filters', {})
    
    # 创建组合过滤器
    composite_filter = CompositePathFilter()
    
    # 添加系统路径过滤器
    composite_filter.add_filter(SystemPathFilter())
    
    # 添加临时路径过滤器
    composite_filter.add_filter(TemporaryPathFilter())
    
    # 添加开发路径过滤器
    composite_filter.add_filter(DevelopmentPathFilter())
    
    # 添加应用数据路径过滤器
    composite_filter.add_filter(ApplicationDataFilter())
    
    # 添加路径深度过滤器
    max_depth = config.get('engine', {}).get('max路径深度', 10)
    composite_filter.add_filter(PathDepthFilter(max_depth))
    
    # 添加自定义过滤器
    excluded_paths = filters_config.get('excluded_paths', [])
    excluded_patterns = filters_config.get('excluded_patterns', [])
    if excluded_paths or excluded_patterns:
        composite_filter.add_filter(CustomPathFilter(excluded_paths, excluded_patterns))
        
    return composite_filter