"""
PathPilot 主程序入口

负责启动应用程序。
"""

import sys
import os


def _get_base_dir() -> str:
    """
    获取基础目录（稳健检测，兼容各种启动方式）
    
    优先级:
    1. PyInstaller (sys._MEIPASS)
    2. Nuitka (__compiled__ + GetModuleFileNameW)
    3. 回退: sys.argv[0]
    """
    # PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS

    # Nuitka standalone: 用 Windows API 获取 exe 真实路径
    import __main__
    if hasattr(__main__, '__compiled__'):
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.kernel32.GetModuleFileNameW(None, buf, 512)
            return os.path.dirname(os.path.abspath(buf.value))
        except Exception:
            pass

    # 回退
    return os.path.dirname(os.path.abspath(sys.argv[0]))


BASE_DIR = _get_base_dir()
sys.path.insert(0, BASE_DIR)

# 切换工作目录到 exe 所在目录，确保所有相对路径（data/config/logs）
# 都写入到 exe 旁边，实现绿色便携
os.chdir(BASE_DIR)


def is_first_run() -> bool:
    """检测是否是首次运行"""
    data_dir = os.path.join(BASE_DIR, "data")
    first_run_flag = os.path.join(data_dir, ".first_run_done")
    return not os.path.exists(first_run_flag)


def _mark_first_run_done():
    """标记首次运行完成"""
    data_dir = os.path.join(BASE_DIR, "data")
    first_run_flag = os.path.join(data_dir, ".first_run_done")
    os.makedirs(data_dir, exist_ok=True)
    if not os.path.exists(first_run_flag):
        with open(first_run_flag, 'w', encoding='utf-8') as f:
            f.write("done")


def main():
    """主函数"""
    try:
        from src.app import PathPilotApp
        
        app = PathPilotApp()
        
        if is_first_run():
            app.show_welcome()
            _mark_first_run_done()
        
        app.initialize()
        sys.exit(app.run())
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
