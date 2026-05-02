"""
去重处理器模块单元测试
"""

import time
import pytest
from datetime import datetime, timedelta
from src.core.path_dedup import (
    TimeBasedDeduplicator,
    HierarchicalDeduplicator,
    PathDeduplicator
)


class TestTimeBasedDeduplicator:
    """TimeBasedDeduplicator 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.deduplicator = TimeBasedDeduplicator(time_window_ms=1000)
        
    def test_first_access(self):
        """测试首次访问"""
        assert self.deduplicator.is_duplicate("c:\\test") == False
        
    def test_immediate_duplicate(self):
        """测试立即重复访问"""
        self.deduplicator.is_duplicate("c:\\test")
        assert self.deduplicator.is_duplicate("c:\\test") == True
        
    def test_after_time_window(self):
        """测试时间窗口后访问"""
        self.deduplicator.is_duplicate("c:\\test")
        
        # 模拟时间流逝（修改最后访问时间）
        self.deduplicator.last_access_times["c:\\test"] = datetime.now() - timedelta(seconds=2)
        
        assert self.deduplicator.is_duplicate("c:\\test") == False
        
    def test_different_paths(self):
        """测试不同路径"""
        self.deduplicator.is_duplicate("c:\\test1")
        assert self.deduplicator.is_duplicate("c:\\test2") == False
        
    def test_reset(self):
        """测试重置"""
        self.deduplicator.is_duplicate("c:\\test")
        self.deduplicator.reset()
        assert self.deduplicator.is_duplicate("c:\\test") == False


class TestHierarchicalDeduplicator:
    """HierarchicalDeduplicator 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.deduplicator = HierarchicalDeduplicator(max_recent_paths=5)
        
    def test_first_path(self):
        """测试第一个路径"""
        assert self.deduplicator.is_duplicate("c:\\test") == False
        
    def test_navigation_up_existing(self):
        """测试向上导航到已存在的路径"""
        # 先访问父路径
        self.deduplicator.is_duplicate("c:\\test")
        # 再访问子路径
        self.deduplicator.is_duplicate("c:\\test\\subdir")
        # 再次访问父路径（应该被认为是重复）
        assert self.deduplicator.is_duplicate("c:\\test") == True
        
    def test_navigation_down_existing(self):
        """测试向下导航到已存在的路径"""
        # 先访问子路径
        self.deduplicator.is_duplicate("c:\\test\\subdir")
        # 再访问父路径
        self.deduplicator.is_duplicate("c:\\test")
        # 再次访问子路径（应该被认为是重复）
        assert self.deduplicator.is_duplicate("c:\\test\\subdir") == True
        
    def test_navigation_up_new(self):
        """测试向上导航到新路径"""
        # 先访问子路径
        self.deduplicator.is_duplicate("c:\\test\\subdir")
        # 访问父路径（新路径，不应该被认为是重复）
        assert self.deduplicator.is_duplicate("c:\\test") == False
        
    def test_sibling_navigation(self):
        """测试同级导航"""
        self.deduplicator.is_duplicate("c:\\test1")
        assert self.deduplicator.is_duplicate("c:\\test2") == False
        
    def test_max_recent_paths(self):
        """测试最大最近路径限制"""
        # 添加超过限制的路径
        for i in range(10):
            self.deduplicator.is_duplicate(f"c:\\test{i}")
            
        # 验证列表大小不超过限制
        assert len(self.deduplicator.recent_paths) <= 5
        
    def test_get_recent_paths(self):
        """测试获取最近路径"""
        self.deduplicator.is_duplicate("c:\\test1")
        self.deduplicator.is_duplicate("c:\\test2")
        
        recent = self.deduplicator.get_recent_paths()
        assert len(recent) == 2
        assert "c:\\test1" in recent
        assert "c:\\test2" in recent
        
    def test_get_last_path(self):
        """测试获取最后路径"""
        self.deduplicator.is_duplicate("c:\\test1")
        self.deduplicator.is_duplicate("c:\\test2")
        
        assert self.deduplicator.get_last_path() == "c:\\test2"


class TestPathDeduplicator:
    """PathDeduplicator 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        config = {
            'engine': {
                '时间去重窗口': 1000,
                '最大最近路径': 10
            }
        }
        self.deduplicator = PathDeduplicator(config)
        
    def test_first_access(self):
        """测试首次访问"""
        assert self.deduplicator.is_duplicate("c:\\test") == False
        
    def test_time_duplicate(self):
        """测试时间去重"""
        self.deduplicator.is_duplicate("c:\\test")
        assert self.deduplicator.is_duplicate("c:\\test") == True
        
    def test_hierarchical_duplicate_existing(self):
        """测试层级去重（已存在的路径）"""
        # 先访问父路径
        self.deduplicator.is_duplicate("c:\\test")
        # 再访问子路径
        self.deduplicator.is_duplicate("c:\\test\\subdir")
        # 再次访问父路径（应该被认为是重复）
        assert self.deduplicator.is_duplicate("c:\\test") == True
        
    def test_hierarchical_duplicate_new(self):
        """测试层级去重（新路径）"""
        # 先访问子路径
        self.deduplicator.is_duplicate("c:\\test\\subdir")
        # 访问父路径（新路径，不应该被认为是重复）
        assert self.deduplicator.is_duplicate("c:\\test") == False
        
    def test_normal_path(self):
        """测试普通路径"""
        self.deduplicator.is_duplicate("c:\\test1")
        assert self.deduplicator.is_duplicate("c:\\test2") == False
        
    def test_get_recent_paths(self):
        """测试获取最近路径"""
        self.deduplicator.is_duplicate("c:\\test1")
        self.deduplicator.is_duplicate("c:\\test2")
        
        recent = self.deduplicator.get_recent_paths()
        assert len(recent) == 2