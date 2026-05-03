"""
PathPilot 主程序入口

负责启动应用程序。
"""

import sys
import os

# 确定基础目录
if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    # 使用 sys.argv[0] 获取 exe 所在目录
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

sys.path.insert(0, BASE_DIR)


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
