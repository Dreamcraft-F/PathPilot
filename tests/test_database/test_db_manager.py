"""
数据库模块单元测试
"""

import os
import tempfile
import pytest
from datetime import datetime
from src.database.models import PathRecord, VisitEvent
from src.database.db_manager import DatabaseManager


class TestPathRecord:
    """PathRecord 测试类"""
    
    def test_create_path_record(self):
        """测试创建路径记录"""
        record = PathRecord(
            path="c:\\users\\test\\documents",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        
        # 验证记录创建
        assert record.path == "c:\\users\\test\\documents"
        assert record.visit_count == 1
        assert record.importance_score == 100
        assert record.is_favorite == False
        assert record.status == "active"
        assert record.id != ""  # 自动生成ID
        
    def test_path_record_to_dict(self):
        """测试路径记录转换为字典"""
        now = datetime.now()
        record = PathRecord(
            path="c:\\users\\test",
            first_visit=now,
            last_visit=now,
            visit_count=5,
            importance_score=150,
            is_favorite=True,
            tags=["work", "important"]
        )
        
        # 转换为字典
        data = record.to_dict()
        
        # 验证字典内容
        assert data["path"] == "c:\\users\\test"
        assert data["visit_count"] == 5
        assert data["importance_score"] == 150
        assert data["is_favorite"] == True
        assert data["tags"] == ["work", "important"]
        assert "first_visit" in data
        assert "last_visit" in data
        
    def test_path_record_from_dict(self):
        """测试从字典创建路径记录"""
        now = datetime.now()
        data = {
            "id": "test-id-123",
            "path": "c:\\users\\test",
            "first_visit": now.isoformat(),
            "last_visit": now.isoformat(),
            "visit_count": 3,
            "importance_score": 120,
            "is_favorite": False,
            "tags": ["personal"],
            "source": "auto",
            "status": "active"
        }
        
        # 从字典创建记录
        record = PathRecord.from_dict(data)
        
        # 验证记录内容
        assert record.id == "test-id-123"
        assert record.path == "c:\\users\\test"
        assert record.visit_count == 3
        assert record.importance_score == 120
        assert record.tags == ["personal"]


class TestVisitEvent:
    """VisitEvent 测试类"""
    
    def test_create_visit_event(self):
        """测试创建访问事件"""
        event = VisitEvent(
            path="c:\\users\\test",
            timestamp=datetime.now(),
            duration=5000,
            window_id="12345",
            previous_path="c:\\users",
            navigation_type="down"
        )
        
        # 验证事件创建
        assert event.path == "c:\\users\\test"
        assert event.duration == 5000
        assert event.window_id == "12345"
        assert event.navigation_type == "down"
        
    def test_visit_event_to_dict(self):
        """测试访问事件转换为字典"""
        now = datetime.now()
        event = VisitEvent(
            path="c:\\users\\test",
            timestamp=now,
            duration=3000,
            navigation_type="direct"
        )
        
        # 转换为字典
        data = event.to_dict()
        
        # 验证字典内容
        assert data["path"] == "c:\\users\\test"
        assert data["duration"] == 3000
        assert data["navigation_type"] == "direct"
        assert "timestamp" in data


class TestDatabaseManager:
    """DatabaseManager 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 使用内存数据库进行测试
        self.db_manager = DatabaseManager(":memory:")
        self.db_manager.initialize()
        
    def teardown_method(self):
        """测试后清理"""
        self.db_manager.close()
        
    def test_insert_and_get_path_record(self):
        """测试插入和获取路径记录"""
        # 创建记录
        record = PathRecord(
            path="c:\\users\\test\\documents",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        
        # 插入记录
        self.db_manager.insert_path_record(record)
        
        # 获取记录
        retrieved_record = self.db_manager.get_path_record_by_path("c:\\users\\test\\documents")
        
        # 验证记录
        assert retrieved_record is not None
        assert retrieved_record.path == "c:\\users\\test\\documents"
        assert retrieved_record.visit_count == 1
        assert retrieved_record.importance_score == 100
        
    def test_update_path_record(self):
        """测试更新路径记录"""
        # 创建并插入记录
        record = PathRecord(
            path="c:\\users\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        self.db_manager.insert_path_record(record)
        
        # 更新记录
        record.visit_count = 5
        record.importance_score = 150
        record.is_favorite = True
        self.db_manager.update_path_record(record)
        
        # 获取更新后的记录
        updated_record = self.db_manager.get_path_record_by_path("c:\\users\\test")
        
        # 验证更新
        assert updated_record.visit_count == 5
        assert updated_record.importance_score == 150
        assert updated_record.is_favorite == True
        
    def test_get_recent_paths(self):
        """测试获取最近路径"""
        # 插入多条记录
        paths = ["c:\\users\\test1", "c:\\users\\test2", "c:\\users\\test3"]
        for path in paths:
            record = PathRecord(
                path=path,
                first_visit=datetime.now(),
                last_visit=datetime.now(),
                visit_count=1,
                importance_score=100
            )
            self.db_manager.insert_path_record(record)
            
        # 获取最近路径
        recent_paths = self.db_manager.get_recent_paths(limit=2)
        
        # 验证结果
        assert len(recent_paths) == 2
        
    def test_search_paths(self):
        """测试搜索路径"""
        # 插入测试数据
        test_paths = [
            "c:\\users\\test\\documents",
            "c:\\users\\test\\pictures",
            "c:\\windows\\system32",
            "c:\\program files\\app"
        ]
        
        for path in test_paths:
            record = PathRecord(
                path=path,
                first_visit=datetime.now(),
                last_visit=datetime.now(),
                visit_count=1,
                importance_score=100
            )
            self.db_manager.insert_path_record(record)
            
        # 搜索包含"users"的路径
        results = self.db_manager.search_paths("users")
        
        # 验证搜索结果
        assert len(results) == 2
        for result in results:
            assert "users" in result.path
            
    def test_delete_path_record(self):
        """测试删除路径记录（软删除）"""
        # 创建并插入记录
        record = PathRecord(
            path="c:\\users\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        self.db_manager.insert_path_record(record)
        
        # 删除记录
        self.db_manager.delete_path_record(record.id)
        
        # 验证记录被软删除（状态变为deleted）
        deleted_record = self.db_manager.get_path_record_by_id(record.id)
        assert deleted_record.status == "deleted"
        
    def test_toggle_favorite(self):
        """测试切换收藏状态"""
        # 创建并插入记录
        record = PathRecord(
            path="c:\\users\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100,
            is_favorite=False
        )
        self.db_manager.insert_path_record(record)
        
        # 切换收藏状态
        self.db_manager.toggle_favorite(record.id)
        
        # 验证收藏状态
        updated_record = self.db_manager.get_path_record_by_id(record.id)
        assert updated_record.is_favorite == True
        
        # 再次切换
        self.db_manager.toggle_favorite(record.id)
        updated_record = self.db_manager.get_path_record_by_id(record.id)
        assert updated_record.is_favorite == False
        
    def test_insert_and_get_visit_event(self):
        """测试插入和获取访问事件"""
        # 创建访问事件
        event = VisitEvent(
            path="c:\\users\\test",
            timestamp=datetime.now(),
            duration=5000,
            window_id="12345",
            previous_path="c:\\users",
            navigation_type="down"
        )
        
        # 插入事件
        self.db_manager.insert_visit_event(event)
        
        # 获取事件
        events = self.db_manager.get_visit_events("c:\\users\\test")
        
        # 验证事件
        assert len(events) == 1
        assert events[0].path == "c:\\users\\test"
        assert events[0].duration == 5000
        assert events[0].navigation_type == "down"
        
    def test_get_favorite_paths(self):
        """测试获取收藏路径"""
        # 插入收藏和非收藏记录
        record1 = PathRecord(
            path="c:\\users\\favorite",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100,
            is_favorite=True
        )
        record2 = PathRecord(
            path="c:\\users\\normal",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100,
            is_favorite=False
        )
        self.db_manager.insert_path_record(record1)
        self.db_manager.insert_path_record(record2)
        
        # 获取收藏路径
        favorites = self.db_manager.get_favorite_paths()
        
        # 验证只返回收藏路径
        assert len(favorites) == 1
        assert favorites[0].path == "c:\\users\\favorite"
        assert favorites[0].is_favorite == True
        
    def test_get_today_paths(self):
        """测试获取今日路径"""
        # 插入记录
        record = PathRecord(
            path="c:\\users\\today",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        self.db_manager.insert_path_record(record)
        
        # 获取今日路径
        today_paths = self.db_manager.get_today_paths()
        
        # 验证返回今日路径
        assert len(today_paths) >= 1
        assert any(p.path == "c:\\users\\today" for p in today_paths)
        
    def test_get_paths_by_directory(self):
        """测试按目录分组获取路径"""
        # 插入同一目录下的多条记录
        record1 = PathRecord(
            path="d:\\projects\\project1",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        record2 = PathRecord(
            path="d:\\projects\\project2",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            importance_score=100
        )
        self.db_manager.insert_path_record(record1)
        self.db_manager.insert_path_record(record2)
        
        # 按目录分组获取
        groups = self.db_manager.get_paths_by_directory(days=7)
        
        # 验证分组
        assert "d:\\projects" in groups
        assert len(groups["d:\\projects"]) == 2