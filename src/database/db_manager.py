"""
PathPilot 数据库管理模块

负责数据库的初始化、连接和操作。
"""

import sqlite3
import json
import os
import threading
from typing import List, Optional
from datetime import datetime
from src.database.models import PathRecord, VisitEvent
from src.utils.path_utils import PathUtils


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/pathpilot.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        
    def initialize(self):
        """初始化数据库"""
        # 确保目录存在（内存数据库除外）
        if self.db_path != ":memory:":
            db_dir = os.path.dirname(self.db_path)
            if db_dir:  # 确保目录路径不为空
                os.makedirs(db_dir, exist_ok=True)
        
        # 连接数据库 - 使用 check_same_thread=False 以支持多线程访问
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        # 创建表
        self._create_tables()
        
    def _create_tables(self):
        """创建数据库表"""
        if not self.connection:
            return
            
        cursor = self.connection.cursor()
        
        # 创建路径记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS path_records (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                first_visit DATETIME NOT NULL,
                last_visit DATETIME NOT NULL,
                visit_count INTEGER DEFAULT 1,
                total_time_spent INTEGER DEFAULT 0,
                importance_score INTEGER DEFAULT 100,
                is_favorite BOOLEAN DEFAULT FALSE,
                tags TEXT DEFAULT '[]',
                source TEXT DEFAULT 'auto',
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建访问事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                duration INTEGER DEFAULT 0,
                window_id TEXT,
                previous_path TEXT,
                navigation_type TEXT DEFAULT 'direct',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_records_path ON path_records(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_records_last_visit ON path_records(last_visit)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_records_importance ON path_records(importance_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_visit_events_timestamp ON visit_events(timestamp)")
        
        self.connection.commit()
        
    def insert_path_record(self, record: PathRecord):
        """
        插入路径记录
        
        Args:
            record: 路径记录
        """
        if not self.connection:
            return
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO path_records 
                (id, path, first_visit, last_visit, visit_count, total_time_spent, 
                 importance_score, is_favorite, tags, source, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.path, record.first_visit, record.last_visit,
                record.visit_count, record.total_time_spent, record.importance_score,
                record.is_favorite, json.dumps(record.tags, ensure_ascii=False), record.source, record.status
            ))
            self.connection.commit()
        
    def update_path_record(self, record: PathRecord):
        """
        更新路径记录
        
        Args:
            record: 路径记录
        """
        if not self.connection:
            return
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE path_records 
                SET last_visit = ?, visit_count = ?, total_time_spent = ?,
                    importance_score = ?, is_favorite = ?, tags = ?, status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                record.last_visit, record.visit_count, record.total_time_spent,
                record.importance_score, record.is_favorite, json.dumps(record.tags, ensure_ascii=False), 
                record.status, record.id
            ))
            self.connection.commit()
        
    def get_path_record_by_path(self, path: str) -> Optional[PathRecord]:
        """
        根据路径获取记录
        
        Args:
            path: 路径
            
        Returns:
            路径记录，不存在返回None
        """
        if not self.connection:
            return None
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM path_records WHERE path = ?", (path,))
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)
            return None
        
    def get_path_record_by_id(self, record_id: str) -> Optional[PathRecord]:
        """
        根据ID获取记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            路径记录，不存在返回None
        """
        if not self.connection:
            return None
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM path_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)
            return None
        
    def get_recent_paths(self, limit: int = 100) -> List[PathRecord]:
        """
        获取最近访问的路径
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            路径记录列表
        """
        if not self.connection:
            return []
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE status = 'active'
                ORDER BY last_visit DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [self._row_to_record(row) for row in rows]
        
    def search_paths(self, keyword: str, limit: int = 50) -> List[PathRecord]:
        """
        搜索路径
        
        Args:
            keyword: 搜索关键词
            limit: 返回记录数量限制
            
        Returns:
            路径记录列表
        """
        if not self.connection:
            return []
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE path LIKE ? AND status = 'active'
                ORDER BY importance_score DESC, last_visit DESC
                LIMIT ?
            """, (f'%{keyword}%', limit))
            rows = cursor.fetchall()
            return [self._row_to_record(row) for row in rows]
        
    def delete_path_record(self, record_id: str):
        """
        删除路径记录（软删除）
        
        Args:
            record_id: 记录ID
        """
        if not self.connection:
            return
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE path_records 
                SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (record_id,))
            self.connection.commit()
            
    def delete_paths_by_prefix(self, path_prefix: str):
        """
        级联删除：软删除指定路径及其所有子路径
        
        Args:
            path_prefix: 路径前缀（如 "C:/Users" 会同时删除 "C:/Users/Documents" 等）
        """
        if not self.connection:
            return
            
        # 规范化前缀，确保匹配以 \ 开头的子路径
        normalized = path_prefix.lower().rstrip('\\')
        prefix_pattern = normalized + '%'
        
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE path_records 
                SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'active' AND (
                    LOWER(path) = ? OR LOWER(path) LIKE ?
                )
            """, (normalized, prefix_pattern))
            self.connection.commit()
        
    def toggle_favorite(self, record_id: str):
        """
        切换收藏状态
        
        Args:
            record_id: 记录ID
        """
        if not self.connection:
            return
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE path_records 
                SET is_favorite = NOT is_favorite, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (record_id,))
            self.connection.commit()
        
    def insert_visit_event(self, event: VisitEvent):
        """
        插入访问事件
        
        Args:
            event: 访问事件
        """
        if not self.connection:
            return
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO visit_events 
                (path, timestamp, duration, window_id, previous_path, navigation_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.path, event.timestamp, event.duration,
                event.window_id, event.previous_path, event.navigation_type
            ))
            self.connection.commit()
        
    def get_visit_events(self, path: str, limit: int = 100) -> List[VisitEvent]:
        """
        获取路径的访问事件
        
        Args:
            path: 路径
            limit: 返回记录数量限制
            
        Returns:
            访问事件列表
        """
        if not self.connection:
            return []
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM visit_events 
                WHERE path = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (path, limit))
            rows = cursor.fetchall()
            return [self._row_to_event(row) for row in rows]
        
    def clear_all_records(self):
        """清空所有记录"""
        if not self.connection:
            return
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM path_records")
            cursor.execute("DELETE FROM visit_events")
            self.connection.commit()
        
    def get_favorite_paths(self, limit: int = 50) -> List[PathRecord]:
        """
        获取收藏的路径
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            收藏的路径记录列表
        """
        if not self.connection:
            return []
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE is_favorite = 1 AND status = 'active'
                ORDER BY last_visit DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [self._row_to_record(row) for row in rows]
        
    def get_today_paths(self, limit: int = 10) -> List[PathRecord]:
        """
        获取今日访问的路径
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            今日访问的路径记录列表
        """
        if not self.connection:
            return []
            
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE DATE(last_visit) = DATE('now', 'localtime') AND status = 'active'
                ORDER BY last_visit DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [self._row_to_record(row) for row in rows]
        
    def get_paths_by_directory(self, days: int = 7, limit: int = 50) -> dict:
        """
        按目录分组获取路径
        
        Args:
            days: 时间范围（天）
            limit: 每个分组的最大路径数
            
        Returns:
            目录分组字典 {目录名: [路径记录列表]}
        """
        if not self.connection:
            return {}
            
        with self._lock:
            cursor = self.connection.cursor()
            
            # 获取指定天数内的路径
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE last_visit >= datetime('now', ?) AND status = 'active'
                ORDER BY last_visit DESC
            """, (f'-{days} days',))
            rows = cursor.fetchall()
            
            # 按父目录分组
            groups = {}
            for row in rows:
                record = self._row_to_record(row)
                # 获取父目录
                parent = self._get_parent_directory(record.path)
                
                if parent not in groups:
                    groups[parent] = []
                
                if len(groups[parent]) < limit:
                    groups[parent].append(record)
                    
            return groups
        
    def get_paths_by_time_group(self, limit_per_group: int = 10) -> dict:
        """
        按时间分组获取路径
        
        Args:
            limit_per_group: 每个分组的最大路径数
            
        Returns:
            时间分组字典 {'today': [...], 'yesterday': [...], 'this_week': [...], 'older': [...]}
        """
        if not self.connection:
            return {}
            
        result = {
            'today': [],
            'yesterday': [],
            'this_week': [],
            'older': []
        }
        
        with self._lock:
            cursor = self.connection.cursor()
            
            # 今日
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE DATE(last_visit) = DATE('now', 'localtime') AND status = 'active'
                ORDER BY last_visit DESC
                LIMIT ?
            """, (limit_per_group,))
            result['today'] = [self._row_to_record(row) for row in cursor.fetchall()]
            
            # 昨日
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE DATE(last_visit) = DATE('now', '-1 day', 'localtime') AND status = 'active'
                ORDER BY last_visit DESC
                LIMIT ?
            """, (limit_per_group,))
            result['yesterday'] = [self._row_to_record(row) for row in cursor.fetchall()]
            
            # 本周（不包括今天和昨天）
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE DATE(last_visit) >= DATE('now', 'weekday 0', '-7 days', 'localtime') 
                    AND DATE(last_visit) < DATE('now', '-1 day', 'localtime')
                    AND status = 'active'
                ORDER BY last_visit DESC
                LIMIT ?
            """, (limit_per_group,))
            result['this_week'] = [self._row_to_record(row) for row in cursor.fetchall()]
            
            # 更早
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE DATE(last_visit) < DATE('now', 'weekday 0', '-7 days', 'localtime') 
                    AND status = 'active'
                ORDER BY last_visit DESC
                LIMIT ?
            """, (limit_per_group,))
            result['older'] = [self._row_to_record(row) for row in cursor.fetchall()]
            
        return result
        
    def get_paths_by_frequency_group(self, limit_per_group: int = 10) -> dict:
        """
        按频率分组获取路径
        
        Args:
            limit_per_group: 每个分组的最大路径数
            
        Returns:
            频率分组字典 {'high': [...], 'medium': [...], 'low': [...]}
        """
        if not self.connection:
            return {}
            
        result = {
            'high': [],    # > 10次
            'medium': [],  # 3-10次
            'low': []      # < 3次
        }
        
        with self._lock:
            cursor = self.connection.cursor()
            
            # 高频 (>10次)
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE visit_count > 10 AND status = 'active'
                ORDER BY visit_count DESC
                LIMIT ?
            """, (limit_per_group,))
            result['high'] = [self._row_to_record(row) for row in cursor.fetchall()]
            
            # 中频 (3-10次)
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE visit_count BETWEEN 3 AND 10 AND status = 'active'
                ORDER BY visit_count DESC
                LIMIT ?
            """, (limit_per_group,))
            result['medium'] = [self._row_to_record(row) for row in cursor.fetchall()]
            
            # 低频 (<3次)
            cursor.execute("""
                SELECT * FROM path_records 
                WHERE visit_count < 3 AND status = 'active'
                ORDER BY last_visit DESC
                LIMIT ?
            """, (limit_per_group,))
            result['low'] = [self._row_to_record(row) for row in cursor.fetchall()]
            
        return result
        
    def _get_parent_directory(self, path: str) -> str:
        """
        获取父目录名
        
        Args:
            path: 路径
            
        Returns:
            父目录名
        """
        parent = PathUtils.get_parent_path(path)
        return parent if parent else path
        
    def _row_to_record(self, row: sqlite3.Row) -> PathRecord:
        """
        将数据库行转换为路径记录
        
        Args:
            row: 数据库行
            
        Returns:
            路径记录
        """
        return PathRecord(
            id=row['id'],
            path=row['path'],
            first_visit=datetime.fromisoformat(row['first_visit']),
            last_visit=datetime.fromisoformat(row['last_visit']),
            visit_count=row['visit_count'],
            total_time_spent=row['total_time_spent'],
            importance_score=row['importance_score'],
            is_favorite=bool(row['is_favorite']),
            tags=json.loads(row['tags']) if row['tags'] else [],
            source=row['source'],
            status=row['status']
        )
        
    def _row_to_event(self, row: sqlite3.Row) -> VisitEvent:
        """
        将数据库行转换为访问事件
        
        Args:
            row: 数据库行
            
        Returns:
            访问事件
        """
        return VisitEvent(
            id=row['id'],
            path=row['path'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            duration=row['duration'],
            window_id=row['window_id'] or '',
            previous_path=row['previous_path'] or '',
            navigation_type=row['navigation_type']
        )
        
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def reconnect(self):
        """重新连接数据库"""
        self.close()
        self.initialize()