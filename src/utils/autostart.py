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
            
            # 先删除旧快捷方式，确保干净创建
            if os.path.exists(self._shortcut_path):
                os.remove(self._shortcut_path)
            
            # 创建快捷方式
            pythoncom.CoInitialize()
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(self._shortcut_path)
            
            # 处理路径（开发模式下可能包含引号和参数）
            if '"' in exe_path:
                import shlex
                try:
                    parts = shlex.split(exe_path)
                    shortcut.TargetPath = parts[0]
                    if len(parts) > 1:
                        shortcut.Arguments = ' '.join(parts[1:])
                except ValueError:
                    shortcut.TargetPath = exe_path.strip('"')
            else:
                shortcut.TargetPath = exe_path
            
            # 设置工作目录
            target_dir = os.path.dirname(shortcut.TargetPath)
            if target_dir:
                shortcut.WorkingDirectory = target_dir
            
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
        获取可执行文件路径
        
        Returns:
            可执行文件路径（打包模式下为exe路径，开发模式下为python+脚本路径）
        """
        # 检测是否为 Nuitka 打包后的 exe
        import __main__
        if hasattr(__main__, '__compiled__'):
            # 用 Windows API 获取 exe 真实路径（不依赖 sys.argv[0]）
            try:
                import ctypes
                buf = ctypes.create_unicode_buffer(512)
                ctypes.windll.kernel32.GetModuleFileNameW(None, buf, 512)
                return os.path.abspath(buf.value)
            except Exception:
                return os.path.abspath(sys.argv[0])
        
        # 开发模式：返回 python 解释器 + 脚本路径
        exe = sys.executable
        main_script = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'main.py')
        )
        if os.path.exists(main_script):
            return f'"{exe}" "{main_script}"'
        
        return exe
