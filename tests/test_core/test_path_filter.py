"""
路径过滤器模块单元测试
"""

import pytest
from src.core.path_filter import (
    SystemPathFilter,
    TemporaryPathFilter,
    DevelopmentPathFilter,
    ApplicationDataFilter,
    PathDepthFilter,
    CompositePathFilter,
    CustomPathFilter,
    create_default_filter
)


class TestSystemPathFilter:
    """SystemPathFilter 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.filter = SystemPathFilter()
        
    def test_windows_directory(self):
        """测试Windows目录"""
        assert self.filter.should_exclude("c:\\windows\\system32") == True
        assert self.filter.should_exclude("c:\\windows\\drivers") == True
        
    def test_program_files(self):
        """测试Program Files目录"""
        assert self.filter.should_exclude("c:\\program files\\test") == True
        assert self.filter.should_exclude("c:\\program files (x86)\\test") == True
        
    def test_recycle_bin(self):
        """测试回收站"""
        assert self.filter.should_exclude("c:\\$recycle.bin\\test") == True
        
    def test_normal_path(self):
        """测试普通路径"""
        assert self.filter.should_exclude("c:\\users\\test\\documents") == False
        assert self.filter.should_exclude("d:\\projects\\test") == False


class TestTemporaryPathFilter:
    """TemporaryPathFilter 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.filter = TemporaryPathFilter()
        
    def test_temp_directory(self):
        """测试临时目录"""
        assert self.filter.should_exclude("c:\\temp\\test.txt") == True
        assert self.filter.should_exclude("c:\\tmp\\test.txt") == True
        
    def test_temp_files(self):
        """测试临时文件"""
        assert self.filter.should_exclude("c:\\test\\file.tmp") == True
        assert self.filter.should_exclude("c:\\test\\file.temp") == True
        assert self.filter.should_exclude("c:\\test\\file.bak") == True
        
    def test_normal_file(self):
        """测试普通文件"""
        assert self.filter.should_exclude("c:\\test\\file.txt") == False
        assert self.filter.should_exclude("c:\\test\\file.py") == False


class TestDevelopmentPathFilter:
    """DevelopmentPathFilter 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.filter = DevelopmentPathFilter()
        
    def test_git_directory(self):
        """测试.git目录"""
        assert self.filter.should_exclude("c:\\project\\.git\\config") == True
        
    def test_node_modules(self):
        """测试node_modules目录"""
        assert self.filter.should_exclude("c:\\project\\node_modules\\test") == True
        
    def test_build_directory(self):
        """测试build目录"""
        assert self.filter.should_exclude("c:\\project\\build\\output") == True
        
    def test_normal_directory(self):
        """测试普通目录"""
        assert self.filter.should_exclude("c:\\project\\src\\main.py") == False


class TestPathDepthFilter:
    """PathDepthFilter 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.filter = PathDepthFilter(max_depth=5)
        
    def test_shallow_path(self):
        """测试浅层路径"""
        assert self.filter.should_exclude("c:\\users") == False
        assert self.filter.should_exclude("c:\\users\\test") == False
        
    def test_deep_path(self):
        """测试深层路径"""
        assert self.filter.should_exclude("c:\\a\\b\\c\\d\\e\\f") == True
        assert self.filter.should_exclude("c:\\a\\b\\c\\d\\e\\f\\g") == True


class TestCompositePathFilter:
    """CompositePathFilter 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.filter = CompositePathFilter()
        self.filter.add_filter(SystemPathFilter())
        self.filter.add_filter(TemporaryPathFilter())
        
    def test_multiple_filters(self):
        """测试多个过滤器"""
        # 系统路径应该被过滤
        assert self.filter.should_exclude("c:\\windows\\system32") == True
        
        # 临时路径应该被过滤
        assert self.filter.should_exclude("c:\\temp\\test.txt") == True
        
        # 普通路径不应该被过滤
        assert self.filter.should_exclude("c:\\users\\test\\documents") == False
        
    def test_add_remove_filter(self):
        """测试添加和移除过滤器"""
        filter_count = len(self.filter.filters)
        
        # 添加新过滤器
        new_filter = PathDepthFilter(3)
        self.filter.add_filter(new_filter)
        assert len(self.filter.filters) == filter_count + 1
        
        # 移除过滤器
        self.filter.remove_filter(new_filter)
        assert len(self.filter.filters) == filter_count


class TestCustomPathFilter:
    """CustomPathFilter 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.filter = CustomPathFilter(
            excluded_paths=["c:\\test\\excluded", "c:\\test\\wildcard\\*"],
            excluded_patterns=[r'^.*\.log$']
        )
        
    def test_excluded_paths(self):
        """测试排除路径"""
        assert self.filter.should_exclude("c:\\test\\excluded") == True
        assert self.filter.should_exclude("c:\\test\\excluded\\subfolder") == True
        
    def test_wildcard_paths(self):
        """测试通配符路径"""
        assert self.filter.should_exclude("c:\\test\\wildcard\\test") == True
        
    def test_excluded_patterns(self):
        """测试排除模式"""
        assert self.filter.should_exclude("c:\\test\\file.log") == True
        
    def test_normal_paths(self):
        """测试普通路径"""
        assert self.filter.should_exclude("c:\\test\\normal") == False
        assert self.filter.should_exclude("c:\\test\\file.txt") == False


class TestCreateDefaultFilter:
    """create_default_filter 测试类"""
    
    def test_create_default_filter(self):
        """测试创建默认过滤器"""
        config = {
            'engine': {'max路径深度': 8},
            'filters': {
                'excluded_paths': ['c:\\custom\\excluded'],
                'excluded_patterns': [r'^.*\\.tmp$']
            }
        }
        
        filter_obj = create_default_filter(config)
        
        # 验证过滤器创建成功
        assert isinstance(filter_obj, CompositePathFilter)
        assert len(filter_obj.filters) > 0
        
        # 测试系统路径过滤
        assert filter_obj.should_exclude("c:\\windows\\system32") == True
        
        # 测试自定义路径过滤
        assert filter_obj.should_exclude("c:\\custom\\excluded") == True