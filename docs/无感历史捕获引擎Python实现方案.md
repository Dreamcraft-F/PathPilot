# PathPilot 无感历史捕获引擎 Python 实现方案

## 1. 技术选型

### 1.1 开发语言和框架
- **主语言**：Python 3.9+
- **GUI框架**：PySide6 6.5+
- **系统交互**：pywin32 305+
- **UI自动化**：comtypes 1.4+
- **数据库**：SQLite（Python内置）
- **配置管理**：JSON（Python内置）
- **日志系统**：logging（Python内置）

### 1.2 系统交互技术
- **窗口监听**：Windows API (pywin32)
- **路径获取**：UI Automation API (comtypes)
- **事件钩子**：SetWinEventHook (pywin32)
- **进程管理**：psutil

### 1.3 数据存储
- **主数据库**：SQLite（轻量级，无需安装）
- **缓存**：内存缓存（字典）
- **配置文件**：JSON格式

## 2. 核心实现步骤

### 2.1 窗口事件监听实现

#### 2.1.1 设置事件钩子
```python
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes

# 定义回调函数类型
WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.HWND,
    wintypes.LONG,
    wintypes.LONG,
    wintypes.DWORD,
    wintypes.DWORD
)

class WindowMonitor:
    def __init__(self):
        self.hook = None
        self.callback = None
        
    def start(self):
        """启动窗口监控"""
        # 设置事件钩子
        self.callback = WinEventProcType(self._event_callback)
        self.hook = ctypes.windll.user32.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,  # eventMin
            win32con.EVENT_SYSTEM_FOREGROUND,  # eventMax
            0,  # hmodWinEventProc
            self.callback,  # lpfnWinEventProc
            0,  # idProcess
            0,  # idThread
            win32con.WINEVENT_OUTOFCONTEXT  # dwFlags
        )
        
    def stop(self):
        """停止窗口监控"""
        if self.hook:
            ctypes.windll.user32.UnhookWinEvent(self.hook)
            self.hook = None
            
    def _event_callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        """窗口事件回调"""
        # 检查是否是资源管理器窗口
        if self._is_explorer_window(hwnd):
            path = self._get_explorer_path(hwnd)
            if path:
                self._process_new_path(path, hwnd)
```

#### 2.1.2 窗口识别方法
```python
import win32gui
import win32process
import psutil

class WindowIdentifier:
    @staticmethod
    def is_explorer_window(hwnd):
        """判断是否是资源管理器窗口"""
        # 方法1：检查窗口类名
        class_name = win32gui.GetClassName(hwnd)
        if class_name == "CabinetWClass":
            return True
            
        # 方法2：检查进程名
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name().lower() == "explorer.exe"
        except:
            return False
            
    @staticmethod
    def get_window_class_name(hwnd):
        """获取窗口类名"""
        return win32gui.GetClassName(hwnd)
```

### 2.2 路径获取实现

#### 2.2.1 使用 UI Automation 获取路径
```python
import comtypes
from comtypes.client import CreateObject
from comtypes.gen import UIAutomationClient

class ExplorerPathReader:
    def __init__(self):
        self.automation = CreateObject(
            "{FF48DBA4-60EF-4201-AA87-54103EEF594E}",
            interface=UIAutomationClient.IUIAutomation
        )
        
    def get_explorer_path(self, hwnd):
        """获取资源管理器路径"""
        try:
            # 获取窗口元素
            element = self.automation.ElementFromHandle(hwnd)
            
            # 查找地址栏（AutomationId = 1001）
            condition = self.automation.CreatePropertyCondition(
                UIAutomationClient.UIA_AutomationIdPropertyId,
                1001
            )
            address_bar = element.FindFirst(
                UIAutomationClient.TreeScope_Descendants,
                condition
            )
            
            if address_bar:
                # 获取地址栏的值
                value_pattern = address_bar.GetCurrentPattern(
                    UIAutomationClient.UIA_ValuePatternId
                )
                return value_pattern.CurrentValue
        except Exception as e:
            print(f"获取路径失败: {e}")
            
        return None
```

#### 2.2.2 备用方案：使用 Shell32
```python
import win32com.client

class ShellPathReader:
    def __init__(self):
        self.shell = win32com.client.Dispatch("Shell.Application")
        
    def get_explorer_path(self, hwnd):
        """通过Shell获取资源管理器路径"""
        try:
            # 遍历所有窗口
            for window in self.shell.Windows():
                if window.HWND == hwnd:
                    # 获取路径
                    path = window.LocationURL
                    # 转换URL为本地路径
                    if path.startswith("file:///"):
                        path = path[8:].replace("/", "\\")
                    return path
        except Exception as e:
            print(f"Shell获取路径失败: {e}")
            
        return None
```

### 2.3 路径处理流水线

#### 2.3.1 处理流水线架构
```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class PathRecord:
    """路径记录"""
    path: str
    first_visit: datetime
    last_visit: datetime
    visit_count: int = 1
    importance_score: int = 100
    
class PathProcessingPipeline:
    def __init__(self, config):
        self.config = config
        self.filters = [
            SystemPathFilter(),
            TemporaryPathFilter(),
            DevelopmentPathFilter()
        ]
        self.deduplicator = PathDeduplicator(config)
        self.importance_calculator = ImportanceCalculator(config)
        
    def process_path(self, raw_path: str, hwnd: int) -> Optional[PathRecord]:
        """处理路径"""
        # 1. 路径规范化
        normalized_path = self._normalize_path(raw_path)
        
        # 2. 应用过滤规则
        if not self._should_record_path(normalized_path):
            return None
            
        # 3. 去重处理
        if self.deduplicator.is_duplicate(normalized_path):
            return None
            
        # 4. 计算重要性
        importance = self.importance_calculator.calculate(normalized_path)
        
        # 5. 创建记录
        now = datetime.now()
        return PathRecord(
            path=normalized_path,
            first_visit=now,
            last_visit=now,
            visit_count=1,
            importance_score=importance
        )
        
    def _normalize_path(self, path: str) -> str:
        """规范化路径"""
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
        
    def _should_record_path(self, path: str) -> bool:
        """判断是否应该记录路径"""
        for filter_obj in self.filters:
            if filter_obj.should_exclude(path):
                return False
        return True
```

#### 2.3.2 过滤器实现
```python
import re
from abc import ABC, abstractmethod

class PathFilter(ABC):
    """路径过滤器基类"""
    
    @abstractmethod
    def should_exclude(self, path: str) -> bool:
        """判断是否应该排除路径"""
        pass
        
class SystemPathFilter(PathFilter):
    """系统路径过滤器"""
    
    def __init__(self):
        self.excluded_paths = [
            'c:\\windows',
            'c:\\program files',
            'c:\\program files (x86)',
            'c:\\$recycle.bin',
            'c:\\system volume information'
        ]
        
    def should_exclude(self, path: str) -> bool:
        """检查是否是系统路径"""
        path_lower = path.lower()
        return any(path_lower.startswith(excluded) for excluded in self.excluded_paths)
        
class TemporaryPathFilter(PathFilter):
    """临时路径过滤器"""
    
    def __init__(self):
        self.temp_patterns = [
            r'^.*\\temp\\.*$',
            r'^.*\\tmp\\.*$',
            r'^.*\.tmp$',
            r'^.*\.temp$',
            r'^.*\.bak$'
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.temp_patterns]
        
    def should_exclude(self, path: str) -> bool:
        """检查是否是临时路径"""
        return any(pattern.match(path) for pattern in self.compiled_patterns)
        
class DevelopmentPathFilter(PathFilter):
    """开发路径过滤器"""
    
    def __init__(self):
        self.dev_patterns = [
            r'^.*\\.git\\.*$',
            r'^.*\\.svn\\.*$',
            r'^.*\\node_modules\\.*$',
            r'^.*\\vendor\\.*$',
            r'^.*\\build\\.*$',
            r'^.*\\dist\\.*$'
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.dev_patterns]
        
    def should_exclude(self, path: str) -> bool:
        """检查是否是开发路径"""
        return any(pattern.match(path) for pattern in self.compiled_patterns)
```

### 2.4 智能去重算法

#### 2.4.1 基于时间的去重
```python
from datetime import datetime, timedelta
from typing import Dict

class TimeBasedDeduplicator:
    """基于时间的去重器"""
    
    def __init__(self, time_window_ms: int = 5000):
        self.time_window = timedelta(milliseconds=time_window_ms)
        self.last_access_times: Dict[str, datetime] = {}
        
    def is_duplicate(self, path: str) -> bool:
        """判断是否是重复路径"""
        now = datetime.now()
        
        if path in self.last_access_times:
            last_access = self.last_access_times[path]
            if now - last_access < self.time_window:
                return True
                
        # 更新最后访问时间
        self.last_access_times[path] = now
        return False
```

#### 2.4.2 基于层级的智能过滤
```python
from collections import OrderedDict
from typing import List

class HierarchicalDeduplicator:
    """基于层级的去重器"""
    
    def __init__(self, max_recent_paths: int = 20):
        self.max_recent_paths = max_recent_paths
        self.recent_paths = OrderedDict()
        
    def is_duplicate(self, path: str) -> bool:
        """判断是否是重复路径"""
        if not self.recent_paths:
            self.recent_paths[path] = datetime.now()
            return False
            
        last_path = next(reversed(self.recent_paths))
        
        # 检查是否是向上导航（从子目录返回父目录）
        if self._is_parent_path(path, last_path):
            if path in self.recent_paths:
                # 移动到最新位置
                self.recent_paths.move_to_end(path)
                return True
                
        # 检查是否是向下导航（从父目录进入子目录）
        elif self._is_parent_path(last_path, path):
            if path in self.recent_paths:
                self.recent_paths.move_to_end(path)
                return True
                
        # 新路径，添加到列表
        self.recent_paths[path] = datetime.now()
        
        # 保持列表大小
        while len(self.recent_paths) > self.max_recent_paths:
            self.recent_paths.popitem(last=False)
            
        return False
        
    def _is_parent_path(self, parent: str, child: str) -> bool:
        """判断是否是父路径"""
        parent_lower = parent.lower()
        child_lower = child.lower()
        return child_lower.startswith(parent_lower + '\\') or child_lower == parent_lower
```

#### 2.4.3 综合去重器
```python
class PathDeduplicator:
    """综合去重器"""
    
    def __init__(self, config):
        self.time_deduplicator = TimeBasedDeduplicator(
            config.get('时间去重窗口', 5000)
        )
        self.hierarchical_deduplicator = HierarchicalDeduplicator(
            config.get('最大最近路径', 20)
        )
        
    def is_duplicate(self, path: str) -> bool:
        """判断是否是重复路径"""
        # 1. 时间去重
        if self.time_deduplicator.is_duplicate(path):
            return True
            
        # 2. 层级去重
        if self.hierarchical_deduplicator.is_duplicate(path):
            return True
            
        return False
```

### 2.5 重要性评分算法

```python
class ImportanceCalculator:
    """重要性计算器"""
    
    def __init__(self, config):
        self.weights = config.get('权重', {
            'time': 0.4,
            'frequency': 0.3,
            'depth': 0.3
        })
        self.favorite_bonus = config.get('收藏加分', 100)
        
    def calculate(self, record) -> int:
        """计算重要性分数"""
        score = 100  # 基础分
        
        # 时间权重：停留时间越长，分数越高
        time_weight = min(record.total_time_spent / 60000.0, 1.0)  # 最大1分钟
        score += int(time_weight * 50 * self.weights['time'])
        
        # 频率权重：访问次数越多，分数越高
        freq_weight = min(record.visit_count / 10.0, 1.0)  # 最大10次
        score += int(freq_weight * 30 * self.weights['frequency'])
        
        # 深度权重：路径深度适中（3-5层）加分
        depth = record.path.count('\\')
        if 3 <= depth <= 5:
            score += int(20 * self.weights['depth'])
        elif depth > 5:
            score -= int(10 * self.weights['depth'])
            
        # 收藏加分
        if record.is_favorite:
            score += self.favorite_bonus
            
        return max(0, score)  # 确保分数不为负数
        
    def get_importance_level(self, score: int) -> str:
        """获取重要性级别"""
        if score >= 200:
            return "★★★"
        elif score >= 150:
            return "★★"
        elif score >= 100:
            return "★"
        else:
            return ""
```

## 3. 数据库设计

### 3.1 数据库表结构
```sql
-- 路径记录表
CREATE TABLE path_records (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    first_visit DATETIME NOT NULL,
    last_visit DATETIME NOT NULL,
    visit_count INTEGER DEFAULT 1,
    total_time_spent INTEGER DEFAULT 0,
    importance_score INTEGER DEFAULT 100,
    is_favorite BOOLEAN DEFAULT FALSE,
    tags TEXT DEFAULT '[]',  -- JSON数组
    source TEXT DEFAULT 'auto',
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 访问事件表
CREATE TABLE visit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    duration INTEGER DEFAULT 0,
    window_id TEXT,
    previous_path TEXT,
    navigation_type TEXT DEFAULT 'direct',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_path_records_path ON path_records(path);
CREATE INDEX idx_path_records_last_visit ON path_records(last_visit);
CREATE INDEX idx_path_records_importance ON path_records(importance_score);
CREATE INDEX idx_visit_events_timestamp ON visit_events(timestamp);
```

### 3.2 数据库操作封装
```python
import sqlite3
import os
from typing import List, Optional
from datetime import datetime

class PathDatabase:
    """路径数据库"""
    
    def __init__(self, db_path: str = "data/pathpilot.db"):
        self.db_path = db_path
        self.connection = None
        
    def initialize(self):
        """初始化数据库"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 连接数据库
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        # 创建表
        self._create_tables()
        
    def _create_tables(self):
        """创建数据库表"""
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
        
    def insert_path_record(self, record):
        """插入路径记录"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO path_records 
            (id, path, first_visit, last_visit, visit_count, total_time_spent, 
             importance_score, is_favorite, tags, source, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id, record.path, record.first_visit, record.last_visit,
            record.visit_count, record.total_time_spent, record.importance_score,
            record.is_favorite, str(record.tags), record.source, record.status
        ))
        self.connection.commit()
        
    def get_path_record_by_path(self, path: str) -> Optional[PathRecord]:
        """根据路径获取记录"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM path_records WHERE path = ?", (path,))
        row = cursor.fetchone()
        if row:
            return self._row_to_record(row)
        return None
        
    def get_recent_paths(self, limit: int = 100) -> List[PathRecord]:
        """获取最近访问的路径"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM path_records 
            WHERE status = 'active'
            ORDER BY last_visit DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
        
    def update_path_record(self, record):
        """更新路径记录"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE path_records 
            SET last_visit = ?, visit_count = ?, total_time_spent = ?,
                importance_score = ?, is_favorite = ?, tags = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            record.last_visit, record.visit_count, record.total_time_spent,
            record.importance_score, record.is_favorite, str(record.tags), 
            record.status, record.id
        ))
        self.connection.commit()
        
    def _row_to_record(self, row) -> PathRecord:
        """将数据库行转换为记录对象"""
        return PathRecord(
            id=row['id'],
            path=row['path'],
            first_visit=datetime.fromisoformat(row['first_visit']),
            last_visit=datetime.fromisoformat(row['last_visit']),
            visit_count=row['visit_count'],
            total_time_spent=row['total_time_spent'],
            importance_score=row['importance_score'],
            is_favorite=bool(row['is_favorite']),
            tags=eval(row['tags']) if row['tags'] else [],
            source=row['source'],
            status=row['status']
        )
        
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
```

## 4. 性能优化策略

### 4.1 异步处理
```python
import threading
from queue import Queue, Empty
from typing import Optional

class AsyncPathProcessor:
    """异步路径处理器"""
    
    def __init__(self, process_func):
        self.event_queue = Queue()
        self.process_func = process_func
        self.worker_thread = None
        self.is_running = False
        
    def start(self):
        """启动处理器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
    def stop(self):
        """停止处理器"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1)
            
    def enqueue_event(self, event):
        """添加事件到队列"""
        self.event_queue.put(event)
        
    def _worker_loop(self):
        """工作循环"""
        while self.is_running:
            try:
                # 从队列获取事件
                event = self.event_queue.get(timeout=0.1)
                
                # 处理事件
                self.process_func(event)
                
            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                # 处理错误
                print(f"处理事件错误: {e}")
```

### 4.2 缓存策略
```python
from collections import OrderedDict
from typing import Dict, Any, Optional

class PathCache:
    """路径缓存"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        if key in self.cache:
            # 移动到最新位置
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
        
    def put(self, key: str, value: Any):
        """添加缓存项"""
        if key in self.cache:
            # 更新现有项
            self.cache.move_to_end(key)
            self.cache[key] = value
        else:
            # 添加新项
            self.cache[key] = value
            
            # 检查缓存大小
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
                
    def remove(self, key: str):
        """移除缓存项"""
        if key in self.cache:
            del self.cache[key]
            
    def clear(self):
        """清空缓存"""
        self.cache.clear()
```

### 4.3 批量写入
```python
import threading
from typing import List
from datetime import datetime

class BatchWriter:
    """批量写入器"""
    
    def __init__(self, database, batch_size: int = 50, flush_interval: float = 10.0):
        self.database = database
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self.pending_records = []
        self.lock = threading.Lock()
        
        # 定时刷新定时器
        self.flush_timer = None
        self._start_flush_timer()
        
    def add_record(self, record):
        """添加记录"""
        with self.lock:
            self.pending_records.append(record)
            
            # 检查是否达到批量大小
            if len(self.pending_records) >= self.batch_size:
                self._flush_pending_records()
                
    def _start_flush_timer(self):
        """启动刷新定时器"""
        self.flush_timer = threading.Timer(self.flush_interval, self._flush_pending_records)
        self.flush_timer.daemon = True
        self.flush_timer.start()
        
    def _flush_pending_records(self):
        """刷新待写入记录"""
        with self.lock:
            if not self.pending_records:
                return
                
            # 获取待写入记录
            records_to_write = self.pending_records.copy()
            self.pending_records.clear()
            
        # 批量写入数据库
        try:
            # 开始事务
            self.database.connection.execute("BEGIN TRANSACTION")
            
            for record in records_to_write:
                self.database.insert_path_record(record)
                
            # 提交事务
            self.database.connection.execute("COMMIT")
            
        except Exception as e:
            # 回滚事务
            self.database.connection.execute("ROLLBACK")
            print(f"批量写入失败: {e}")
            
            # 重新添加到待写入列表
            with self.lock:
                self.pending_records.extend(records_to_write)
                
        # 重新启动定时器
        self._start_flush_timer()
```

## 5. 配置管理

### 5.1 配置文件结构
```json
{
  "version": "1.0",
  "general": {
    "enable_logging": true,
    "log_level": "INFO",
    "database_path": "data/pathpilot.db",
    "backup_enabled": true,
    "backup_interval": 86400
  },
  "engine": {
    "min停留时间": 2000,
    "max路径深度": 10,
    "时间去重窗口": 5000,
    "最大历史记录": 10000
  },
  "filters": {
    "excluded_paths": [
      "C:\\Windows\\*",
      "C:\\Program Files\\*",
      "C:\\$Recycle.Bin"
    ],
    "excluded_patterns": [
      "^.*\\.tmp$",
      "^.*\\.temp$"
    ]
  },
  "importance": {
    "weights": {
      "time": 0.4,
      "frequency": 0.3,
      "depth": 0.3
    },
    "favorite_bonus": 100
  }
}
```

### 5.2 配置管理器
```python
import json
import os
from typing import Any, Dict, Optional

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "user_config.json")
        self.default_config_file = os.path.join(config_dir, "default_config.json")
        self.config: Dict[str, Any] = {}
        
    def load(self):
        """加载配置"""
        # 1. 加载默认配置
        default_config = self._load_json(self.default_config_file)
        
        # 2. 加载用户配置（如果存在）
        user_config = {}
        if os.path.exists(self.config_file):
            user_config = self._load_json(self.config_file)
            
        # 3. 合并配置（用户配置覆盖默认配置）
        self.config = self._merge_config(default_config, user_config)
        
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
    def save(self):
        """保存配置"""
        self._save_json(self.config_file, self.config)
        
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
            
    def _save_json(self, file_path: str, data: Dict[str, Any]):
        """保存JSON文件"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """合并配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
```

## 6. 错误处理和日志

### 6.1 错误处理策略
```python
import logging
from typing import Optional

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: logging.Logger, database):
        self.logger = logger
        self.database = database
        
    def handle_path_access_error(self, path: str, error: Exception):
        """处理路径访问错误"""
        # 记录错误但不中断处理
        self.logger.warning(f"无法访问路径: {path}, 错误: {error}")
        
        # 标记路径为不可访问
        self.database.mark_path_as_inaccessible(path)
        
    def handle_database_error(self, error: Exception):
        """处理数据库错误"""
        self.logger.error(f"数据库错误: {error}")
        
        # 尝试重新连接
        try:
            self.database.reconnect()
        except Exception as reconnect_error:
            self.logger.error(f"重新连接数据库失败: {reconnect_error}")
            
    def handle_ui_error(self, error: Exception):
        """处理UI错误"""
        self.logger.error(f"UI错误: {error}")
```

### 6.2 日志记录
```python
import logging
import os
from datetime import datetime

class Logger:
    """日志记录器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.logger = None
        self._setup_logger()
        
    def _setup_logger(self):
        """设置日志器"""
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建日志器
        self.logger = logging.getLogger("PathPilot")
        self.logger.setLevel(logging.DEBUG)
        
        # 创建文件处理器
        log_file = os.path.join(self.log_dir, f"pathpilot_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
        
    def error(self, message: str, exc_info: bool = True):
        """记录错误日志"""
        self.logger.error(message, exc_info=exc_info)
        
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
        
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
```

## 7. 测试策略

### 7.1 单元测试
```python
import pytest
from src.core.path_filter import SystemPathFilter, TemporaryPathFilter
from src.core.path_deduplicator import TimeBasedDeduplicator, HierarchicalDeduplicator

class TestPathFilter:
    """路径过滤器测试"""
    
    def test_system_path_excluded(self):
        """测试系统路径排除"""
        filter_obj = SystemPathFilter()
        assert filter_obj.should_exclude("c:\\windows\\system32") == True
        assert filter_obj.should_exclude("c:\\program files\\test") == True
        assert filter_obj.should_exclude("c:\\users\\test\\documents") == False
        
    def test_temporary_path_excluded(self):
        """测试临时路径排除"""
        filter_obj = TemporaryPathFilter()
        assert filter_obj.should_exclude("c:\\temp\\test.txt") == True
        assert filter_obj.should_exclude("c:\\test\\file.tmp") == True
        assert filter_obj.should_exclude("c:\\test\\file.txt") == False

class TestDeduplicator:
    """去重器测试"""
    
    def test_time_based_deduplicator(self):
        """测试基于时间的去重器"""
        deduplicator = TimeBasedDeduplicator(time_window_ms=1000)
        
        # 第一次访问
        assert deduplicator.is_duplicate("c:\\test") == False
        
        # 立即再次访问（应该被过滤）
        assert deduplicator.is_duplicate("c:\\test") == True
        
    def test_hierarchical_deduplicator(self):
        """测试基于层级的去重器"""
        deduplicator = HierarchicalDeduplicator(max_recent_paths=10)
        
        # 第一次访问
        assert deduplicator.is_duplicate("c:\\test") == False
        
        # 访问子目录
        assert deduplicator.is_duplicate("c:\\test\\subdir") == False
        
        # 返回父目录
        assert deduplicator.is_duplicate("c:\\test") == True
```

### 7.2 集成测试
```python
import pytest
from src.core.path_engine import PathCaptureEngine
from src.database.db_manager import DatabaseManager
from src.config.config_manager import ConfigManager

class TestPathCaptureEngine:
    """路径捕获引擎测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = ConfigManager()
        self.config.load()
        self.database = DatabaseManager(":memory:")  # 使用内存数据库
        self.database.initialize()
        self.engine = PathCaptureEngine(self.config, self.database)
        
    def test_path_capture_flow(self):
        """测试路径捕获流程"""
        # 模拟路径捕获
        self.engine._process_path("c:\\users\\test\\documents", 12345)
        
        # 验证记录
        records = self.database.get_recent_paths()
        assert len(records) == 1
        assert records[0].path == "c:\\users\\test\\documents"
        
    def test_path_filtering(self):
        """测试路径过滤"""
        # 模拟系统路径
        self.engine._process_path("c:\\windows\\system32", 12345)
        
        # 验证记录被过滤
        records = self.database.get_recent_paths()
        assert len(records) == 0
```

## 8. 部署和分发

### 8.1 安装包结构
```
PathPilot/
├── PathPilot.exe              # 主程序（打包后）
├── config/
│   ├── default_config.json    # 默认配置
│   └── user_config.json       # 用户配置（可选）
├── data/
│   └── pathpilot.db           # 数据库文件（运行时创建）
├── logs/
│   └── pathpilot.log          # 日志文件
├── resources/
│   └── icons/                 # 图标文件
└── uninstall.exe              # 卸载程序
```

### 8.2 系统要求
- **操作系统**：Windows 10/11
- **运行时**：Python 3.9+（打包后无需单独安装）
- **权限**：普通用户权限，无需管理员权限
- **磁盘空间**：50MB + 数据库空间

## 9. 未来扩展

### 9.1 插件系统
```python
from abc import ABC, abstractmethod

class PathPilotPlugin(ABC):
    """PathPilot插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
        
    @abstractmethod
    def initialize(self, context):
        """初始化插件"""
        pass
        
    @abstractmethod
    def on_path_recorded(self, record):
        """路径记录时回调"""
        pass
        
    @abstractmethod
    def on_path_deleted(self, path: str):
        """路径删除时回调"""
        pass
```

### 9.2 API接口
```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/paths', methods=['GET'])
def get_paths():
    """获取路径列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    
    # 获取路径记录
    paths = database.get_recent_paths(limit=page_size)
    
    return jsonify([path.to_dict() for path in paths])

@app.route('/api/paths/<path_id>/favorite', methods=['POST'])
def toggle_favorite(path_id):
    """切换收藏状态"""
    database.toggle_favorite(path_id)
    return jsonify({'success': True})
```

## 10. 注意事项

### 10.1 安全性
- 不收集用户敏感信息
- 本地存储，不上传云端
- 可设置隐私模式暂停记录

### 10.2 性能
- 后台运行，CPU占用<1%
- 内存占用<50MB
- 数据库文件定期优化

### 10.3 兼容性
- 支持Windows 10/11所有版本
- 支持多显示器环境
- 支持高DPI显示