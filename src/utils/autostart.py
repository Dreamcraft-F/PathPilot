"""
PathPilot 开机自启动模块

通过启动文件夹实现开机自启动功能。
"""

import sys
import os
import pythoncom
from win32com.client import Dispatch


class AutoStartManager:
    """开机自启动管理器"""
    
    APP_NAME = "PathPilot"
    
    def __init__(self):
        self._logger = None
        self._startup_folder = self._get_startup_folder()
        self._shortcut_path = os.path.join(self._startup_folder, f"{self.APP_NAME}.lnk")
        
    def set_logger(self, logger):
        """设置日志记录器"""
        self._logger = logger
        
    def _log(self, level: str, message: str):
        """内部日志方法"""
        if self._logger:
            getattr(self._logger, level)(message)
            
    def _get_startup_folder(self) -> str:
        """获取启动文件夹路径"""
        appdata = os.environ.get('APPDATA', '')
        return os.path.join(appdata, r'Microsoft\Windows\Start Menu\Programs\Startup')
            
    def is_enabled(self) -> bool:
        """检查是否已启用开机自启动"""
        return os.path.exists(self._shortcut_path)
            
    def enable(self) -> bool:
        """
        启用开机自启动（创建快捷方式）
        
        Returns:
            是否成功
        """
        try:
            exe_path = self._get_exe_path()
            
            # 创建快捷方式
            pythoncom.CoInitialize()
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(self._shortcut_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path.strip('"'))
            shortcut.Description = self.APP_NAME
            shortcut.save()
            
            self._log("info", f"已启用开机自启动: {self._shortcut_path}")
            return True
        except Exception as e:
            self._log("error", f"启用开机自启动失败: {e}")
            return False
            
    def disable(self) -> bool:
        """
        禁用开机自启动（删除快捷方式）
        
        Returns:
            是否成功
        """
        try:
            if os.path.exists(self._shortcut_path):
                os.remove(self._shortcut_path)
            
            self._log("info", "已禁用开机自启动")
            return True
        except Exception as e:
            self._log("error", f"禁用开机自启动失败: {e}")
            return False
            
    def toggle(self, enable: bool) -> bool:
        """
        切换开机自启动状态
        
        Args:
            enable: 是否启用
            
        Returns:
            是否成功
        """
        if enable:
            return self.enable()
        else:
            return self.disable()
            
    def _get_exe_path(self) -> str:
        """
        获取可执行文件路径（不带引号）
        
        Returns:
            可执行文件路径
        """
        return sys.executable
