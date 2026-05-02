"""
PathPilot 窗口监控器模块

负责监听 Windows 窗口焦点变化事件，识别资源管理器窗口。
"""

import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass
import win32gui
import win32process
import psutil

from src.utils.logger import get_logger


@dataclass
class WindowEvent:
    """窗口事件数据"""
    hwnd: int
    class_name: str
    title: str
    process_id: int
    process_name: str
    path: str = ""  # 已获取的资源管理器路径
    timestamp: float = 0.0


class WindowMonitor:
    """窗口监控器 - 使用定时轮询方式"""
    
    def __init__(self, poll_interval: float = 0.5):
        """
        初始化窗口监控器
        
        Args:
            poll_interval: 轮询间隔（秒）
        """
        self.is_running = False
        self.stop_event = threading.Event()
        self.monitor_thread: Optional[threading.Thread] = None
        self.on_window_activated: Optional[Callable[[WindowEvent], None]] = None
        self.logger = get_logger()
        self.poll_interval = poll_interval
        
        # 记录上一次的窗口信息，用于检测变化
        self.last_hwnd = None
        self.last_path = None
        
    def start(self):
        """启动监控"""
        if self.is_running:
            return
            
        self.is_running = True
        self.stop_event.clear()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            daemon=True,
            name="WindowMonitor"
        )
        self.monitor_thread.start()
        self.logger.info("窗口监控器已启动 (轮询模式)")
        
    def stop(self):
        """停止监控"""
        self.is_running = False
        self.stop_event.set()
            
        # 等待监控线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
            
        self.logger.info("窗口监控器已停止")
        
    def _monitor_loop(self):
        """监控循环 - 定期轮询"""
        shell = None
        try:
            # 创建 Shell COM 对象（一次创建，循环复用）
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
        except Exception as e:
            self.logger.error(f"创建Shell COM对象失败: {e}")
            
        try:
            while not self.stop_event.is_set():
                try:
                    # 获取当前前台窗口
                    hwnd = win32gui.GetForegroundWindow()
                    
                    if hwnd:
                        # 检查是否是资源管理器窗口
                        if self._is_explorer_window(hwnd):
                            # 获取当前路径（使用缓存的shell对象）
                            current_path = self._get_explorer_path(hwnd, shell)
                            
                            # 检查是否发生了变化（窗口或路径）
                            if hwnd != self.last_hwnd or current_path != self.last_path:
                                if current_path:  # 只在成功获取到路径时触发
                                    # 更新记录
                                    self.last_hwnd = hwnd
                                    self.last_path = current_path
                                    
                                    # 创建事件（包含已获取的路径）
                                    window_event = WindowEvent(
                                        hwnd=hwnd,
                                        class_name=self._get_window_class_name(hwnd),
                                        title=self._get_window_text(hwnd),
                                        process_id=self._get_window_process_id(hwnd),
                                        process_name=self._get_window_process_name(hwnd),
                                        path=current_path,
                                        timestamp=time.time()
                                    )
                                    
                                    # 调用回调函数
                                    if self.on_window_activated:
                                        self.on_window_activated(window_event)
                                    
                except Exception as e:
                    self.logger.debug(f"轮询检查出错: {e}")
                    
                # 等待下一次轮询
                self.stop_event.wait(self.poll_interval)
                    
        except Exception as e:
            self.logger.error(f"窗口监控循环错误: {e}")
            import traceback
            traceback.print_exc()
            
    def _is_explorer_window(self, hwnd: int) -> bool:
        """判断是否是资源管理器窗口"""
        try:
            class_name = self._get_window_class_name(hwnd)
            
            # 检查窗口类名
            if class_name == "CabinetWClass":
                return True
                
            # 检查进程名
            process_name = self._get_window_process_name(hwnd)
            return process_name and process_name.lower() == "explorer.exe"
        except Exception:
            return False
            
    def _get_explorer_path(self, hwnd: int, shell=None) -> Optional[str]:
        """获取资源管理器当前路径"""
        try:
            import urllib.parse
            
            if shell is None:
                import win32com.client
                shell = win32com.client.Dispatch("Shell.Application")
            
            for window in shell.Windows():
                try:
                    if window.HWND == hwnd:
                        location_url = window.LocationURL
                        if location_url and location_url.startswith("file:///"):
                            path = location_url[8:].replace("/", "\\")
                            path = urllib.parse.unquote(path)
                            return path
                        elif location_url and not location_url.startswith("::"):
                            return location_url.replace("/", "\\")
                except Exception as e:
                    self.logger.debug(f"遍历COM窗口出错: {e}")
                    continue
                    
            return None
        except Exception as e:
            self.logger.debug(f"获取路径失败: {e}")
            return None
            
    def _get_window_class_name(self, hwnd: int) -> str:
        """获取窗口类名"""
        try:
            return win32gui.GetClassName(hwnd)
        except Exception:
            return ""
            
    def _get_window_text(self, hwnd: int) -> str:
        """获取窗口标题"""
        try:
            return win32gui.GetWindowText(hwnd)
        except Exception:
            return ""
            
    def _get_window_process_id(self, hwnd: int) -> int:
        """获取窗口进程ID"""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return pid
        except Exception:
            return 0
            
    def _get_window_process_name(self, hwnd: int) -> str:
        """获取窗口进程名"""
        try:
            pid = self._get_window_process_id(hwnd)
            if pid:
                process = psutil.Process(pid)
                return process.name()
        except Exception:
            pass
        return ""