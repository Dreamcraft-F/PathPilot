"""
PathPilot 重要性计算器模块

负责计算路径的重要性分数，用于排序和推荐。
"""

from typing import Optional
from src.utils.path_utils import PathUtils
from src.database.models import PathRecord


class ImportanceCalculator:
    """重要性计算器"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        初始化重要性计算器
        
        Args:
            config: 配置字典
        """
        config = config or {}
        importance_config = config.get('importance', {})
        
        # 权重配置
        self.weights = importance_config.get('weights', {
            'time': 0.4,
            'frequency': 0.3,
            'depth': 0.3
        })
        
        # 收藏加分
        self.favorite_bonus = importance_config.get('favorite_bonus', 100)
        
    def calculate(self, record: PathRecord) -> int:
        """
        计算重要性分数
        
        Args:
            record: 路径记录
            
        Returns:
            重要性分数
        """
        score = 100  # 基础分
        
        # 时间权重：停留时间越长，分数越高
        # 将停留时间转换为分钟，最大1分钟
        time_weight = min(record.total_time_spent / 60000.0, 1.0)
        score += int(time_weight * 50 * self.weights['time'])
        
        # 频率权重：访问次数越多，分数越高
        # 最大10次
        freq_weight = min(record.visit_count / 10.0, 1.0)
        score += int(freq_weight * 30 * self.weights['frequency'])
        
        # 深度权重：路径深度适中（3-5层）加分
        depth = PathUtils.get_path_depth(record.path)
        if 3 <= depth <= 5:
            score += int(20 * self.weights['depth'])
        elif depth > 5:
            score -= int(10 * self.weights['depth'])
            
        # 收藏加分
        if record.is_favorite:
            score += self.favorite_bonus
            
        return max(0, score)  # 确保分数不为负数
        
    def get_importance_level(self, score: int) -> str:
        """
        获取重要性级别
        
        Args:
            score: 重要性分数
            
        Returns:
            重要性级别字符串
        """
        if score >= 200:
            return "★★★"
        elif score >= 150:
            return "★★"
        elif score >= 100:
            return "★"
        else:
            return ""
            
    def calculate_batch(self, records: list[PathRecord]) -> list[tuple[PathRecord, int]]:
        """
        批量计算重要性分数
        
        Args:
            records: 路径记录列表
            
        Returns:
            (记录, 分数) 元组列表
        """
        results = []
        for record in records:
            score = self.calculate(record)
            results.append((record, score))
        return results
        
    def update_record_score(self, record: PathRecord) -> PathRecord:
        """
        更新记录的重要性分数
        
        Args:
            record: 路径记录
            
        Returns:
            更新后的记录
        """
        record.importance_score = self.calculate(record)
        return record