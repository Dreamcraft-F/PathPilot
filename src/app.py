"""
PathPilot 应用主模块

负责整合所有模块，管理应用生命周期。
"""

import sys
import os
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import (
    QObject, Signal, QTimer, QPoint, Qt,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
)

from src.config.config_manager import ConfigManager
from src.database.db_manager import DatabaseManager
from src.core.path_engine import PathCaptureEngine
from src.gui.tray_icon import TrayIcon
from src.gui.floating_ball import FloatingBall
from src.gui.main_window import MainWindow
from src.utils.logger import Logger, setup_logger
from src.utils.autostart import AutoStartManager
from src.utils.export import ExportManager


class PathPilotApp(QObject):
    """PathPilot 应用主类"""
    
    # 信号
    quit_signal = Signal()
    path_captured_signal = Signal()  # 路径捕获信号（用于跨线程安全刷新）
    path_newly_captured_signal = Signal(str)  # 新路径信号（用于闪光效果）
    
    def __init__(self):
        """初始化应用"""
        super().__init__()
        
        # 设置应用信息
        QApplication.setApplicationName("PathPilot")
        QApplication.setApplicationVersion("1.0.0")
        QApplication.setOrganizationName("PathPilot")
        
        # 创建应用实例
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 初始化模块
        self.config_manager: Optional[ConfigManager] = None
        self.database_manager: Optional[DatabaseManager] = None
        self.path_engine: Optional[PathCaptureEngine] = None
        self.logger: Optional[Logger] = None
        
        # GUI 组件
        self.tray_icon: Optional[TrayIcon] = None
        self.floating_ball: Optional[FloatingBall] = None
        self.main_window: Optional[MainWindow] = None
        
        # 工具管理器
        self.autostart_manager: Optional[AutoStartManager] = None
        self.export_manager: Optional[ExportManager] = None
        
        # 隐私模式状态
        self.privacy_mode = False
        
        # 缓存数据
        self.cached_records = []
        self.cached_time_groups = {}
        self.cache_dirty = True
        
        # 今日路径计数
        self.today_count = 0
        
        # 启动标志
        self._show_main_on_start = False
        
    def initialize(self):
        """初始化应用"""
        # 1. 初始化日志
        self.logger = setup_logger("logs", "pathpilot")
        self.logger.info("PathPilot 启动中...")
        
        # 2. 初始化配置管理器
        self.config_manager = ConfigManager("config")
        self.config_manager.load()
        self.logger.info("配置加载完成")
        
        # 3. 初始化数据库管理器
        db_path = self.config_manager.get("general.database_path", "data/pathpilot.db")
        self.database_manager = DatabaseManager(db_path)
        self.database_manager.initialize()
        self.logger.info("数据库初始化完成")
        
        # 4. 初始化无感历史捕获引擎
        self.path_engine = PathCaptureEngine(
            self.config_manager.config,
            self.database_manager
        )
        self.logger.info("核心引擎初始化完成")
        
        # 5. 初始化工具管理器
        self._init_managers()
        self.logger.info("工具管理器初始化完成")
        
        # 6. 初始化 GUI 组件
        self._init_gui()
        self.logger.info("GUI 组件初始化完成")
        
        # 7. 连接信号
        self._setup_connections()
        self.logger.info("信号连接完成")
        
        self.logger.info("PathPilot 初始化完成")
        
    def show_welcome(self):
        """显示欢迎向导（阻塞直到关闭）"""
        from src.gui.welcome_wizard import WelcomeWizard
        
        # 创建欢迎向导
        wizard = WelcomeWizard()
        wizard.finished.connect(wizard.close)
        wizard.show()
        
        # 使用循环等待向导关闭
        while wizard.isVisible():
            self.app.processEvents()
        
        # 设置标志，启动时显示主窗口
        self._show_main_on_start = True
        
    def _init_gui(self):
        """初始化 GUI 组件"""
        # 获取配置
        gui_config = self.config_manager.get("gui", {})
        ball_size = gui_config.get("悬浮球大小", 40)
        ball_opacity = gui_config.get("悬浮球透明度", 0.8)
        
        # 创建系统托盘图标
        self.tray_icon = TrayIcon()
        
        # 创建悬浮球
        self.floating_ball = FloatingBall(size=ball_size, opacity=ball_opacity)
        
        # 创建主窗口
        self.main_window = MainWindow()
        
        # 初始化设置页面状态
        autostart_enabled = self.config_manager.get("general.autostart_enabled", True)
        self.main_window.settings_page.set_autostart_state(autostart_enabled)
        
    def _init_managers(self):
        """初始化工具管理器"""
        # 初始化自启动管理器
        self.autostart_manager = AutoStartManager()
        self.autostart_manager.set_logger(self.logger)
        
        # 如果配置中启用自启动，设置注册表
        autostart_enabled = self.config_manager.get("general.autostart_enabled", True)
        if autostart_enabled:
            self.autostart_manager.enable()
            
        # 初始化导出管理器
        self.export_manager = ExportManager(self.database_manager)
        self.export_manager.set_logger(self.logger)
        
    def _setup_connections(self):
        """设置信号连接"""
        # 托盘图标信号
        self.tray_icon.show_main_window_signal.connect(self.show_main_window)
        self.tray_icon.toggle_privacy_mode_signal.connect(self.toggle_privacy_mode)
        self.tray_icon.quit_signal.connect(self.quit)
        
        # 悬浮球信号
        self.floating_ball.clicked_signal.connect(self.show_main_window)
        
        # 主窗口信号
        self.main_window.path_selected_signal.connect(self.open_path)
        self.main_window.path_deleted_signal.connect(self.delete_path)
        self.main_window.privacy_mode_toggled_signal.connect(self.toggle_privacy_mode)
        self.main_window.window_hidden_signal.connect(self.show_floating_ball)
        self.main_window.clear_history_signal.connect(self.clear_history)
        self.main_window.favorite_toggled_signal.connect(self.toggle_favorite)
        self.main_window.open_this_pc_signal.connect(self.open_this_pc)
        self.main_window.view_changed_signal.connect(self.switch_view)
        
        # 设置页面信号
        self.main_window.autostart_changed_signal.connect(self.toggle_autostart)
        self.main_window.export_requested_signal.connect(self.export_data)
        
        # 核心引擎信号
        self.path_engine.on_path_captured = self._on_path_captured
        
        # 路径捕获信号（跨线程安全刷新）
        self.path_captured_signal.connect(self._on_path_captured_main_thread)
        self.path_newly_captured_signal.connect(self._on_new_path)
        
    def run(self):
        """运行应用"""
        # 显示托盘图标
        self.tray_icon.show()
        
        # 启动核心引擎
        self.path_engine.start()
        
        # 根据标志决定显示主窗口还是悬浮球
        if self._show_main_on_start:
            self.show_main_window()
        else:
            self.show_floating_ball()
        
        self.logger.info("PathPilot 已启动")
        
        # 运行应用主循环
        return self.app.exec()
        
    def show_main_window(self):
        """显示主窗口"""
        # 使用当前视图模式加载数据（强制更新）
        self.switch_view(self.main_window.current_view, force_update=True)
        
        # 获取悬浮球中心坐标
        ball_geo = self.floating_ball.frameGeometry()
        ball_center = ball_geo.center()
        
        # 目标窗口位置和大小
        target_width = 460
        target_height = 560
        screen = self.app.primaryScreen().geometry()
        target_x = screen.width() // 2 - target_width // 2
        target_y = screen.height() // 2 - target_height // 2
        
        # 设置初始位置（从悬浮球展开）
        self.main_window.resize(1, 1)
        self.main_window.move(ball_center.x(), ball_center.y())
        self.main_window.setWindowOpacity(0.0)
        self.main_window.show()
        
        # 位置动画
        pos_anim = QPropertyAnimation(self.main_window, b"pos")
        pos_anim.setDuration(200)
        pos_anim.setStartValue(ball_center)
        pos_anim.setEndValue(QPoint(target_x, target_y))
        pos_anim.setEasingCurve(QEasingCurve.OutQuad)
        
        # 大小动画
        size_anim = QPropertyAnimation(self.main_window, b"size")
        size_anim.setDuration(200)
        size_anim.setStartValue(QPoint(1, 1))
        size_anim.setEndValue(QPoint(target_width, target_height))
        size_anim.setEasingCurve(QEasingCurve.OutQuad)
        
        # 透明度动画
        opacity_anim = QPropertyAnimation(self.main_window, b"windowOpacity")
        opacity_anim.setDuration(200)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        
        # 并行动画组
        self._show_anim_group = QParallelAnimationGroup()
        self._show_anim_group.addAnimation(pos_anim)
        self._show_anim_group.addAnimation(size_anim)
        self._show_anim_group.addAnimation(opacity_anim)
        self._show_anim_group.start()
        
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        # 隐藏悬浮球
        self.floating_ball.hide()
        
    def hide_main_window(self):
        """隐藏主窗口"""
        self.main_window.hide()
        # 显示悬浮球
        self.show_floating_ball()
        
    def show_floating_ball(self):
        """显示悬浮球"""
        self.floating_ball.show()
        self.floating_ball.move_to_edge()
        
    def toggle_privacy_mode(self, enabled: bool):
        """
        切换隐私模式
        
        Args:
            enabled: 是否启用
        """
        self.privacy_mode = enabled
        
        # 更新托盘图标
        self.tray_icon.set_privacy_mode(enabled)
        
        # 更新主窗口
        self.main_window.set_privacy_mode(enabled)
        
        # 更新核心引擎
        if enabled:
            self.path_engine.stop()
            self.logger.info("隐私模式已开启，暂停记录")
        else:
            self.path_engine.start()
            self.logger.info("隐私模式已关闭，恢复记录")
            
    def open_path(self, path: str):
        """
        打开路径（智能跳转：优先激活已有窗口）
        
        Args:
            path: 路径
        """
        try:
            import win32gui
            import urllib.parse
            
            # 规范化路径
            normalized_path = path.lower().replace('/', '\\')
            if normalized_path.endswith('\\'):
                normalized_path = normalized_path.rstrip('\\')
            
            # 先检查是否有打开该路径的资源管理器窗口
            if not hasattr(self, '_shell'):
                import win32com.client
                self._shell = win32com.client.Dispatch("Shell.Application")
            
            found = False
            
            for window in self._shell.Windows():
                try:
                    location_url = window.LocationURL
                    if location_url and location_url.startswith("file:///"):
                        # 获取窗口路径
                        window_path = location_url[8:].replace("/", "\\")
                        window_path = urllib.parse.unquote(window_path).lower()
                        if window_path.endswith('\\'):
                            window_path = window_path.rstrip('\\')
                        
                        # 检查路径是否匹配
                        if window_path == normalized_path:
                            # 找到匹配的窗口，激活它
                            hwnd = window.HWND
                            win32gui.SetForegroundWindow(hwnd)
                            # 如果窗口最小化，恢复它
                            if win32gui.IsIconic(hwnd):
                                win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                            found = True
                            self.logger.info(f"激活已有窗口: {path}")
                            break
                except Exception as e:
                    self.logger.debug(f"检查窗口出错: {e}")
                    continue
            
            # 如果没有找到匹配的窗口，打开新窗口
            if not found:
                import subprocess
                subprocess.Popen(["explorer.exe", path])
                self.logger.info(f"打开新窗口: {path}")
            
            # 隐藏主窗口
            self.hide_main_window()
            
        except Exception as e:
            self.logger.error(f"打开路径失败: {e}")
            # 出错时使用默认方式打开
            import subprocess
            subprocess.Popen(["explorer.exe", path])
            self.hide_main_window()
            
    def delete_path(self, record_id: str):
        """
        删除路径记录
        
        Args:
            record_id: 记录ID
        """
        self.path_engine.delete_path(record_id)
        self.logger.info(f"删除路径记录: {record_id}")
        
        # 立即刷新所有视图
        self.refresh_all_views()
        
    def toggle_favorite(self, record_id: str, is_favorite: bool):
        """
        切换收藏状态
        
        Args:
            record_id: 记录ID
            is_favorite: 是否收藏
        """
        try:
            # 获取记录并更新重要性分数
            record = self.database_manager.get_path_record_by_id(record_id)
            if record:
                record.is_favorite = is_favorite
                if is_favorite:
                    record.importance_score += self.path_engine.importance_calc.favorite_bonus
                else:
                    record.importance_score = max(0, record.importance_score - self.path_engine.importance_calc.favorite_bonus)
                self.database_manager.update_path_record(record)
                self.logger.info(f"{'收藏' if is_favorite else '取消收藏'}路径: {record_id}")
            
            # 刷新所有视图
            self.refresh_all_views()
        except Exception as e:
            self.logger.error(f"更新收藏状态失败: {e}")
        
    def clear_history(self):
        """清空所有历史记录"""
        try:
            self.database_manager.clear_all_records()
            # 重置去重器状态
            self.path_engine.deduplicator.reset()
            self.logger.info("已清空所有历史记录")
            
            # 立即刷新所有视图
            self.refresh_all_views()
        except Exception as e:
            self.logger.error(f"清空历史记录失败: {e}")
            
    def open_this_pc(self):
        """打开此电脑"""
        try:
            import subprocess
            subprocess.Popen(["explorer.exe", "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}"])
            self.logger.info("打开此电脑")
            # 隐藏主窗口
            self.hide_main_window()
        except Exception as e:
            self.logger.error(f"打开此电脑失败: {e}")
            
    def toggle_autostart(self, enabled: bool):
        """
        切换开机自启动
        
        Args:
            enabled: 是否启用
        """
        try:
            success = self.autostart_manager.toggle(enabled)
            if success:
                # 保存配置
                self.config_manager.set("general.autostart_enabled", enabled)
                self.config_manager.save()
                self.logger.info(f"{'启用' if enabled else '禁用'}开机自启动")
                self.main_window.settings_page.show_success(
                    f"已{'启用' if enabled else '禁用'}开机自启动"
                )
            else:
                self.main_window.settings_page.show_error("设置开机自启动失败")
        except Exception as e:
            self.logger.error(f"切换开机自启动失败: {e}")
            self.main_window.settings_page.show_error(f"设置失败: {e}")
            
    def export_data(self, file_path: str):
        """
        导出历史记录
        
        Args:
            file_path: 输出文件路径
        """
        try:
            # 根据文件扩展名判断格式
            if file_path.endswith('.csv'):
                success = self.export_manager.export_to_csv(file_path)
            else:
                success = self.export_manager.export_to_json(file_path)
                
            if success:
                self.logger.info(f"导出历史记录成功: {file_path}")
                self.main_window.settings_page.show_success(
                    f"已导出历史记录到: {os.path.basename(file_path)}"
                )
            else:
                self.main_window.settings_page.show_error("导出失败")
        except Exception as e:
            self.logger.error(f"导出历史记录失败: {e}")
            self.main_window.settings_page.show_error(f"导出失败: {e}")
            
    def switch_view(self, view: str, force_update: bool = False):
        """
        切换视图模式
        
        Args:
            view: 视图模式 (directory, time)
            force_update: 是否强制更新
        """
        # 如果视图没有变化且不强制更新，跳过
        if view == self.main_window.current_view and not force_update:
            return
            
        self.logger.info(f"切换视图: {view}")
        
        # 切换视图显示
        self.main_window.switch_view(view)
        
        # 刷新所有视图数据
        self.refresh_all_views()
        
    def refresh_all_views(self):
        """刷新所有视图的数据（带缓存）"""
        # 标记缓存为脏
        self.cache_dirty = True
        
        # 使用 QTimer 延迟更新，避免频繁刷新
        if not hasattr(self, '_refresh_timer'):
            self._refresh_timer = QTimer()
            self._refresh_timer.setSingleShot(True)
            self._refresh_timer.timeout.connect(self._do_refresh)
        
        # 延迟 500ms 执行刷新（防抖，避免频繁重建UI）
        self._refresh_timer.start(500)
        
    def _do_refresh(self):
        """实际执行刷新"""
        if not self.cache_dirty:
            return
            
        # 获取最新数据
        self.cached_records = self.database_manager.get_recent_paths(1000)
        self.cached_time_groups = self.database_manager.get_paths_by_time_group(limit_per_group=20)
        
        # 更新目录视图
        self.main_window.update_path_list(self.cached_records)
        
        # 更新时间视图
        self.main_window.update_time_view(self.cached_time_groups)
        
        self.cache_dirty = False
        
    def _on_path_captured(self, record):
        """
        路径捕获回调（在引擎工作线程中调用）
        
        Args:
            record: 路径记录
        """
        self.logger.debug(f"捕获路径: {record.path}")
        
        # 更新今日计数（通过信号安全地在主线程执行）
        self.path_captured_signal.emit()
        self.path_newly_captured_signal.emit(record.path)
        
    def _on_path_captured_main_thread(self):
        """路径捕获后的主线程处理"""
        self.today_count += 1
        self.floating_ball.update_usage(self.today_count)
        self.refresh_all_views()
        
    def _on_new_path(self, path: str):
        """新路径捕获（主线程）- 用于闪光效果"""
        # 托盘图标脉冲
        self.tray_icon.flash()
        # 通知视图组件对新路径做闪光
        self.main_window.directory_page.flash_item(path)
        self.main_window.time_page.flash_item(path)
        
    def quit(self):
        """退出应用"""
        self.logger.info("PathPilot 正在退出...")
        
        # 停止核心引擎
        if self.path_engine:
            self.path_engine.stop()
            
        # 关闭数据库
        if self.database_manager:
            self.database_manager.close()
            
        # 隐藏所有GUI组件
        if self.floating_ball:
            self.floating_ball.hide()
            
        if self.main_window:
            self.main_window.hide()
            
        # 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()
            
        # 退出应用
        self.app.quit()
        
    def get_status(self) -> dict:
        """
        获取应用状态
        
        Returns:
            状态字典
        """
        status = {
            "privacy_mode": self.privacy_mode,
            "engine_running": self.path_engine.is_running if self.path_engine else False,
            "database_connected": self.database_manager.connection is not None if self.database_manager else False
        }
        
        if self.path_engine:
            status.update(self.path_engine.get_engine_status())
            
        return status
