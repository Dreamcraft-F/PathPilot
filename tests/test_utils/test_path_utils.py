"""
路径工具模块单元测试
"""

import os
import pytest
from src.utils.path_utils import PathUtils


class TestPathUtils:
    """PathUtils 测试类"""
    
    def test_normalize_path(self):
        """测试路径规范化"""
        # 测试转换为小写
        assert PathUtils.normalize_path("C:\\Users\\Test") == "c:\\users\\test"
        
        # 测试统一路径分隔符
        assert PathUtils.normalize_path("C:/Users/Test") == "c:\\users\\test"
        
        # 测试去除尾部斜杠
        assert PathUtils.normalize_path("C:\\Users\\Test\\") == "c:\\users\\test"
        
        # 测试组合操作
        assert PathUtils.normalize_path("C:/Users/Test/") == "c:\\users\\test"
        
    def test_get_path_depth(self):
        """测试获取路径深度"""
        assert PathUtils.get_path_depth("C:") == 0
        assert PathUtils.get_path_depth("C:\\Users") == 1
        assert PathUtils.get_path_depth("C:\\Users\\Test") == 2
        assert PathUtils.get_path_depth("C:\\Users\\Test\\Documents") == 3
        
    def test_is_parent_path(self):
        """测试判断父路径"""
        # 测试父子关系
        assert PathUtils.is_parent_path("C:\\Users", "C:\\Users\\Test") == True
        assert PathUtils.is_parent_path("C:\\Users", "C:\\Users\\Test\\Documents") == True
        
        # 测试非父子关系
        assert PathUtils.is_parent_path("C:\\Users", "C:\\Windows") == False
        assert PathUtils.is_parent_path("C:\\Users\\Test", "C:\\Users") == False
        
        # 测试相同路径
        assert PathUtils.is_parent_path("C:\\Users", "C:\\Users") == True
        
    def test_matches_pattern(self):
        """测试模式匹配"""
        # 测试通配符 *
        assert PathUtils.matches_pattern("C:\\Users\\Test", "C:\\Users\\*") == True
        assert PathUtils.matches_pattern("C:\\Windows\\System32", "C:\\Windows\\*") == True
        assert PathUtils.matches_pattern("C:\\Users\\Test", "C:\\Windows\\*") == False
        
        # 测试通配符 ?
        assert PathUtils.matches_pattern("C:\\Users\\Test", "C:\\Users\\Tes?") == True
        assert PathUtils.matches_pattern("C:\\Users\\Test", "C:\\Users\\Tes") == False
        
    def test_is_valid_path(self):
        """测试路径验证"""
        # 测试有效路径
        assert PathUtils.is_valid_path("C:\\Users\\Test") == True
        assert PathUtils.is_valid_path("D:\\Documents\\file.txt") == True
        
        # 测试无效路径（包含非法字符）
        assert PathUtils.is_valid_path("C:\\Users\\Test<folder>") == False
        assert PathUtils.is_valid_path("C:\\Users\\Test|folder") == False
        
    def test_get_parent_path(self):
        """测试获取父路径"""
        assert PathUtils.get_parent_path("C:\\Users\\Test") == "C:\\Users"
        assert PathUtils.get_parent_path("C:\\Users") == "C:\\"
        assert PathUtils.get_parent_path("C:\\") is None
        
    def test_join_paths(self):
        """测试路径连接"""
        assert PathUtils.join_paths("C:\\Users", "Test") == "C:\\Users\\Test"
        assert PathUtils.join_paths("C:\\Users", "Test", "Documents") == "C:\\Users\\Test\\Documents"
        
    def test_expand_path(self):
        """测试路径展开"""
        # 测试环境变量展开
        os.environ['TEST_PATH'] = 'C:\\Test'
        assert PathUtils.expand_path("%TEST_PATH%\\File") == "C:\\Test\\File"
        del os.environ['TEST_PATH']
        
    def test_get_path_parts(self):
        """测试获取路径部分"""
        assert PathUtils.get_path_parts("C:\\Users\\Test") == ["C:", "Users", "Test"]
        assert PathUtils.get_path_parts("C:\\Users\\Test\\Documents") == ["C:", "Users", "Test", "Documents"]