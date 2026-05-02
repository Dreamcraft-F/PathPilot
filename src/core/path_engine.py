"""
PathPilot 无感历史捕获引擎模块

负责整合所有核心组件，实现路径的自动捕获和处理。
"""

import threading
import time
from typing import Optional, Callable
from datetime import datetime
from queue import Queue, Empty

from src.core.window_monitor import WindowMonitor, WindowEvent
from src.core.path_filter import PathFilter, create_default_filter
from src.core.path_dedup import PathDeduplicator
from src.core.importance_calc import ImportanceCalculator
from src.database.db_manager import DatabaseManager
from src.database.models import PathRecord, VisitEvent
from src.utils.path_utils import PathUtils
from src.utils.logger import get_logger


class PathCaptureEngine:
    """无感历史捕获引擎"""
    
    def __init__(self, config: dict, database: DatabaseManager):
        """
        初始化无感历史捕获引擎
        
        Args:
            config: 配置字典
            database: 数据库管理器
        """
        self.config = config
        self.database = database
        self.logger = get_logger()
        
        # 初始化子模块
        self.window_monitor = WindowMonitor()
        self.path_filter = create_default_filter(config)
        self.deduplicator = PathDeduplicator(config)
        self.importance_calc = ImportanceCalculator(config)
        
        # 事件队列
        self.event_queue: Queue[WindowEvent] = Queue()
        
        # 工作线程
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # 上一个路径
        self.previous_path: Optional[str] = None
        
        # 回调函数
        self.on_path_captured: Optional[Callable[[PathRecord], None]] = None
        
        # 设置窗口监控器回调
        self.window_monitor.on_window_activated = self._on_window_activated
        
    def start(self):
        """启动引擎"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("无感历史捕获引擎启动")
        
        # 启动窗口监控
        self.window_monitor.start()
        
        # 启动工作线程
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="PathCaptureEngine"
        )
        self.worker_thread.start()
        
    def stop(self):
        """停止引擎"""
        self.is_running = False
        self.logger.info("无感历史捕获引擎停止")
        
        # 停止窗口监控
        self.window_monitor.stop()
        
        # 等待工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)
            
    def _on_window_activated(self, event: WindowEvent):
        """
        窗口激活事件回调
        
        Args:
            event: 窗口事件
        """
        # 将事件放入队列
        self.event_queue.put(event)
        
    def _worker_loop(self):
        """工作循环"""
        while self.is_running:
            try:
                # 从队列获取事件
                event = self.event_queue.get(timeout=0.1)
                
                # 处理事件
                self._process_window_event(event)
                
            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                # 处理错误
                self.logger.error(f"引擎工作循环错误: {e}")
                
    def _process_window_event(self, event: WindowEvent):
        """
        处理窗口事件
        
        Args:
            event: 窗口事件
        """
        try:
            self.logger.debug(f"处理窗口事件: {event.title}")
            
            # 优先使用事件中已携带的路径（避免重复COM调用）
            if event.path:
                path = event.path
                self.logger.debug(f"使用事件携带的路径: {path}")
            else:
                # 回退：从窗口获取路径
                path = self._get_path_from_window(event)
            
            if path:
                self.logger.debug(f"获取到路径: {path}")
                # 处理路径
                self._process_path(path, event)
            else:
                self.logger.debug(f"未能获取路径，窗口标题: {event.title}")
                
        except Exception as e:
            self.logger.error(f"处理窗口事件错误: {e}")
            import traceback
            traceback.print_exc()
            
    def _get_path_from_window(self, event: WindowEvent) -> Optional[str]:
        """
        从窗口获取路径
        
        Args:
            event: 窗口事件
            
        Returns:
            路径字符串，获取失败返回None
        """
        try:
            import win32com.client
            
            # 使用 Shell.Application COM 对象获取路径
            shell = win32com.client.Dispatch("Shell.Application")
            
            # 记录所有打开的窗口
            windows = list(shell.Windows())
            self.logger.debug(f"Shell.Windows() 返回 {len(windows)} 个窗口")
            
            # 遍历所有窗口
            for window in windows:
                try:
                    window_hwnd = window.HWND
                    self.logger.debug(f"检查窗口: hwnd={window_hwnd}, 目标hwnd={event.hwnd}")
                    
                    # 检查窗口句柄是否匹配
                    if window_hwnd == event.hwnd:
                        # 获取路径
                        location_url = window.LocationURL
                        self.logger.debug(f"匹配成功，LocationURL={location_url}")
                        
                        if location_url:
                            # 转换 URL 为本地路径
                            # 移除 "file:///" 前缀
                            if location_url.startswith("file:///"):
                                path = location_url[8:].replace("/", "\\")
                                # 解码 URL 编码的字符
                                import urllib.parse
                                path = urllib.parse.unquote(path)
                                self.logger.info(f"获取到路径: {path}")
                                return path
                            elif location_url.startswith("::"):
                                # 特殊文件夹（如回收站）
                                self.logger.debug(f"特殊文件夹: {location_url}")
                                return None
                            else:
                                # 可能是本地路径
                                path = location_url.replace("/", "\\")
                                self.logger.info(f"获取到路径: {path}")
                                return path
                        else:
                            self.logger.debug(f"窗口 LocationURL 为空")
                except Exception as e:
                    # 忽略单个窗口的错误
                    self.logger.debug(f"检查窗口时出错: {e}")
                    continue
                    
            self.logger.debug(f"未找到匹配的窗口 (hwnd={event.hwnd})")
            return None
        except Exception as e:
            self.logger.error(f"获取窗口路径错误: {e}")
            return None
            
    def _process_path(self, path: str, event: WindowEvent):
        """
        处理路径
        
        Args:
            path: 路径
            event: 窗口事件
        """
        try:
            # 1. 路径规范化
            normalized_path = PathUtils.normalize_path(path)
            self.logger.debug(f"处理路径: {normalized_path}")
            
            # 2. 过滤检查
            if self.path_filter.should_exclude(normalized_path):
                self.logger.debug(f"路径被过滤: {normalized_path}")
                return
                
            # 3. 去重检查
            if self.deduplicator.is_duplicate(normalized_path):
                self.logger.debug(f"路径被去重: {normalized_path}")
                return
                
            # 4. 获取或创建记录
            record = self.database.get_path_record_by_path(normalized_path)
            
            if record:
                # 更新现有记录
                record.visit_count += 1
                record.last_visit = datetime.now()
                record.importance_score = self.importance_calc.calculate(record)
                self.database.update_path_record(record)
            else:
                # 创建新记录
                now = datetime.now()
                record = PathRecord(
                    path=normalized_path,
                    first_visit=now,
                    last_visit=now,
                    visit_count=1,
                    total_time_spent=0,
                    importance_score=100,
                    is_favorite=False,
                    tags=[],
                    source='auto',
                    status='active'
                )
                record.importance_score = self.importance_calc.calculate(record)
                self.database.insert_path_record(record)
                
            # 5. 记录访问事件
            visit_event = VisitEvent(
                path=normalized_path,
                timestamp=datetime.now(),
                duration=0,
                window_id=str(event.hwnd),
                previous_path=self.previous_path or '',
                navigation_type=self._detect_navigation_type(normalized_path)
            )
            self.database.insert_visit_event(visit_event)
            
            # 6. 更新上一个路径
            self.previous_path = normalized_path
            
            # 7. 调用回调函数
            if self.on_path_captured:
                self.on_path_captured(record)
                
            self.logger.debug(f"捕获路径: {normalized_path}")
            
        except Exception as e:
            self.logger.error(f"处理路径错误: {e}")
            
    def _detect_navigation_type(self, current_path: str) -> str:
        """
        检测导航类型
        
        Args:
            current_path: 当前路径
            
        Returns:
            导航类型 ('direct', 'up', 'down', 'sibling')
        """
        if not self.previous_path:
            return 'direct'
            
        # 检查是否是向上导航
        if PathUtils.is_parent_path(current_path, self.previous_path):
            return 'up'
            
        # 检查是否是向下导航
        if PathUtils.is_parent_path(self.previous_path, current_path):
            return 'down'
            
        # 检查是否是同级导航
        parent1 = PathUtils.get_parent_path(self.previous_path)
        parent2 = PathUtils.get_parent_path(current_path)
        if parent1 and parent2 and parent1 == parent2:
            return 'sibling'
            
        return 'direct'
        
    def get_recent_paths(self, limit: int = 100) -> list[PathRecord]:
        """
        获取最近访问的路径
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            路径记录列表
        """
        return self.database.get_recent_paths(limit)
        
    def search_paths(self, keyword: str, limit: int = 50) -> list[PathRecord]:
        """
        搜索路径
        
        Args:
            keyword: 搜索关键词
            limit: 返回记录数量限制
            
        Returns:
            路径记录列表
        """
        return self.database.search_paths(keyword, limit)
        
    def delete_path(self, record_id: str):
        """
        删除路径记录
        
        Args:
            record_id: 记录ID
        """
        self.database.delete_path_record(record_id)
        
    def toggle_favorite(self, record_id: str):
        """
        切换收藏状态
        
        Args:
            record_id: 记录ID
        """
        self.database.toggle_favorite(record_id)
        
    def get_engine_status(self) -> dict:
        """
        获取引擎状态
        
        Returns:
            状态字典
        """
        return {
            'is_running': self.is_running,
            'queue_size': self.event_queue.qsize(),
            'recent_paths_count': len(self.deduplicator.get_recent_paths()),
            'last_path': self.deduplicator.get_last_path()
        }