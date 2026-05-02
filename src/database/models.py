"""
PathPilot 数据模型模块

定义数据库中使用的数据模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class PathRecord:
    """路径记录数据模型"""
    
    id: str = ""
    path: str = ""
    first_visit: datetime = field(default_factory=datetime.now)
    last_visit: datetime = field(default_factory=datetime.now)
    visit_count: int = 1
    total_time_spent: int = 0  # 毫秒
    importance_score: int = 100
    is_favorite: bool = False
    tags: List[str] = field(default_factory=list)
    source: str = 'auto'  # 'auto' 或 'manual'
    status: str = 'active'  # 'active', 'archived', 'deleted'
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())
            
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            'id': self.id,
            'path': self.path,
            'first_visit': self.first_visit.isoformat(),
            'last_visit': self.last_visit.isoformat(),
            'visit_count': self.visit_count,
            'total_time_spent': self.total_time_spent,
            'importance_score': self.importance_score,
            'is_favorite': self.is_favorite,
            'tags': self.tags,
            'source': self.source,
            'status': self.status
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'PathRecord':
        """
        从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            PathRecord实例
        """
        return cls(
            id=data.get('id', ''),
            path=data.get('path', ''),
            first_visit=datetime.fromisoformat(data['first_visit']) if 'first_visit' in data else datetime.now(),
            last_visit=datetime.fromisoformat(data['last_visit']) if 'last_visit' in data else datetime.now(),
            visit_count=data.get('visit_count', 1),
            total_time_spent=data.get('total_time_spent', 0),
            importance_score=data.get('importance_score', 100),
            is_favorite=data.get('is_favorite', False),
            tags=data.get('tags', []),
            source=data.get('source', 'auto'),
            status=data.get('status', 'active')
        )


@dataclass
class VisitEvent:
    """访问事件数据模型"""
    
    id: Optional[int] = None
    path: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    duration: int = 0  # 毫秒
    window_id: str = ""
    previous_path: str = ""
    navigation_type: str = 'direct'  # 'direct', 'up', 'down', 'sibling'
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            'id': self.id,
            'path': self.path,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration,
            'window_id': self.window_id,
            'previous_path': self.previous_path,
            'navigation_type': self.navigation_type
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'VisitEvent':
        """
        从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            VisitEvent实例
        """
        return cls(
            id=data.get('id'),
            path=data.get('path', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(),
            duration=data.get('duration', 0),
            window_id=data.get('window_id', ''),
            previous_path=data.get('previous_path', ''),
            navigation_type=data.get('navigation_type', 'direct')
        )


@dataclass
class PathGroup:
    """路径分组数据模型"""
    
    name: str = ""  # 分组名称（目录名或时间标签）
    paths: List[PathRecord] = field(default_factory=list)  # 该分组下的路径
    count: int = 0  # 路径数量
    last_visit: Optional[datetime] = None  # 该分组最后访问时间
    
    def __post_init__(self):
        """初始化后处理"""
        if self.count == 0:
            self.count = len(self.paths)
        if self.last_visit is None and self.paths:
            self.last_visit = max(p.last_visit for p in self.paths)


@dataclass
class GroupedPaths:
    """分组后的路径数据"""
    
    favorites: List[PathRecord] = field(default_factory=list)  # 收藏路径
    today_paths: List[PathRecord] = field(default_factory=list)  # 今日访问
    directory_groups: List[PathGroup] = field(default_factory=list)  # 按目录分组
    time_groups: dict = field(default_factory=dict)  # 按时间分组
    frequency_groups: dict = field(default_factory=dict)  # 按频率分组