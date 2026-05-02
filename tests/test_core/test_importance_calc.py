"""
重要性计算器模块单元测试
"""

import pytest
from datetime import datetime
from src.core.importance_calc import ImportanceCalculator
from src.database.models import PathRecord


class TestImportanceCalculator:
    """ImportanceCalculator 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        config = {
            'importance': {
                'weights': {
                    'time': 0.4,
                    'frequency': 0.3,
                    'depth': 0.3
                },
                'favorite_bonus': 100
            }
        }
        self.calculator = ImportanceCalculator(config)
        
    def test_basic_score(self):
        """测试基础分数"""
        record = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=0,
            importance_score=100
        )
        
        score = self.calculator.calculate(record)
        assert score >= 100  # 基础分
        
    def test_time_weight(self):
        """测试时间权重"""
        # 短时间停留
        record1 = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=1000,  # 1秒
            importance_score=100
        )
        
        # 长时间停留
        record2 = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=60000,  # 1分钟
            importance_score=100
        )
        
        score1 = self.calculator.calculate(record1)
        score2 = self.calculator.calculate(record2)
        
        # 长时间停留应该有更高的分数
        assert score2 > score1
        
    def test_frequency_weight(self):
        """测试频率权重"""
        # 少量访问
        record1 = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=0,
            importance_score=100
        )
        
        # 多次访问
        record2 = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=10,
            total_time_spent=0,
            importance_score=100
        )
        
        score1 = self.calculator.calculate(record1)
        score2 = self.calculator.calculate(record2)
        
        # 多次访问应该有更高的分数
        assert score2 > score1
        
    def test_depth_weight(self):
        """测试深度权重"""
        # 适中深度（3-5层）
        record1 = PathRecord(
            path="c:\\users\\test\\documents",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=0,
            importance_score=100
        )
        
        # 深层路径
        record2 = PathRecord(
            path="c:\\a\\b\\c\\d\\e\\f",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=0,
            importance_score=100
        )
        
        score1 = self.calculator.calculate(record1)
        score2 = self.calculator.calculate(record2)
        
        # 适中深度应该有更高的分数
        assert score1 > score2
        
    def test_favorite_bonus(self):
        """测试收藏加分"""
        # 未收藏
        record1 = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=0,
            importance_score=100,
            is_favorite=False
        )
        
        # 已收藏
        record2 = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=1,
            total_time_spent=0,
            importance_score=100,
            is_favorite=True
        )
        
        score1 = self.calculator.calculate(record1)
        score2 = self.calculator.calculate(record2)
        
        # 收藏应该有更高的分数
        assert score2 > score1
        assert score2 - score1 == 100  # 收藏加分
        
    def test_get_importance_level(self):
        """测试获取重要性级别"""
        assert self.calculator.get_importance_level(250) == "★★★"
        assert self.calculator.get_importance_level(180) == "★★"
        assert self.calculator.get_importance_level(120) == "★"
        assert self.calculator.get_importance_level(80) == ""
        
    def test_calculate_batch(self):
        """测试批量计算"""
        records = [
            PathRecord(
                path="c:\\test1",
                first_visit=datetime.now(),
                last_visit=datetime.now(),
                visit_count=1,
                total_time_spent=0,
                importance_score=100
            ),
            PathRecord(
                path="c:\\test2",
                first_visit=datetime.now(),
                last_visit=datetime.now(),
                visit_count=5,
                total_time_spent=30000,
                importance_score=100
            )
        ]
        
        results = self.calculator.calculate_batch(records)
        
        assert len(results) == 2
        assert all(isinstance(score, int) for _, score in results)
        
    def test_update_record_score(self):
        """测试更新记录分数"""
        record = PathRecord(
            path="c:\\test",
            first_visit=datetime.now(),
            last_visit=datetime.now(),
            visit_count=5,
            total_time_spent=30000,
            importance_score=100,
            is_favorite=True
        )
        
        updated_record = self.calculator.update_record_score(record)
        
        assert updated_record.importance_score > 100