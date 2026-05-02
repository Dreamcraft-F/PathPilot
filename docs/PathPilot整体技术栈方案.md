# PathPilot 整体技术栈方案

## 1. 技术栈概述

PathPilot 将使用 Python 作为主要开发语言，结合以下技术栈实现所有功能：

### 1.1 核心技术栈

| 组件 | 技术选择 | 版本要求 | 说明 |
|------|----------|----------|------|
| **编程语言** | Python | 3.9+ | 主要开发语言 |
| **GUI框架** | PySide6 | 6.5+ | Qt for Python，界面开发 |
| **系统交互** | pywin32 | 305+ | Windows API 调用 |
| **UI自动化** | comtypes | 1.4+ | COM 接口调用 |
| **数据库** | SQLite | 内置 | 本地数据存储 |
| **配置管理** | JSON | 内置 | 配置文件处理 |
| **日志系统** | logging | 内置 | 日志记录 |
| **打包工具** | PyInstaller | 5.0+ | 程序打包为exe |

### 1.2 可选依赖

| 组件 | 技术选择 | 用途 |
|------|----------|------|
| **异步处理** | asyncio/threading | 后台任务处理 |
| **正则表达式** | re | 路径模式匹配 |
| **系统监控** | psutil | 系统资源监控 |
| **图标处理** | Pillow | 图标和图像处理 |
| **安装包制作** | NSIS/Inno Setup | 制作安装程序 |

## 2. 项目结构设计

```
PathPilot/
├── src/                          # 源代码目录
│   ├── main.py                   # 程序入口
│   ├── app.py                    # 应用主类
│   ├── core/                     # 核心模块
│   │   ├── __init__.py
│   │   ├── path_engine.py        # 无感历史捕获引擎
│   │   ├── path_filter.py        # 路径过滤器
│   │   ├── path_dedup.py         # 去重处理器
│   │   ├── importance_calc.py    # 重要性计算器
│   │   └── window_monitor.py     # 窗口监控器
│   ├── database/                 # 数据库模块
│   │   ├── __init__.py
│   │   ├── db_manager.py         # 数据库管理器
│   │   ├── models.py             # 数据模型
│   │   └── migrations.py         # 数据库迁移
│   ├── gui/                      # GUI模块
│   │   ├── __init__.py
│   │   ├── main_window.py        # 主窗口
│   │   ├── tray_icon.py          # 系统托盘图标
│   │   ├── floating_ball.py      # 悬浮球
│   │   ├── search_widget.py      # 搜索组件
│   │   ├── path_list.py          # 路径列表组件
│   │   └── settings_dialog.py    # 设置对话框
│   ├── config/                   # 配置模块
│   │   ├── __init__.py
│   │   ├── config_manager.py     # 配置管理器
│   │   └── default_config.json   # 默认配置文件
│   ├── utils/                    # 工具模块
│   │   ├── __init__.py
│   │   ├── win32_utils.py        # Windows API 工具
│   │   ├── path_utils.py         # 路径处理工具
│   │   ├── logger.py             # 日志工具
│   │   └── constants.py          # 常量定义
│   └── resources/                # 资源文件
│       ├── icons/                # 图标文件
│       ├── images/               # 图像文件
│       └── styles/               # 样式文件
├── tests/                        # 测试代码
│   ├── __init__.py
│   ├── test_core/                # 核心模块测试
│   ├── test_database/            # 数据库测试
│   └── test_gui/                 # GUI测试
├── data/                         # 数据目录
│   └── pathpilot.db              # 数据库文件
├── config/                       # 配置目录
│   ├── user_config.json          # 用户配置
│   └── filters.json              # 过滤规则配置
├── logs/                         # 日志目录
│   └── pathpilot.log             # 日志文件
├── docs/                         # 文档目录
├── build/                        # 构建目录
├── dist/                         # 分发目录
├── requirements.txt              # 依赖列表
├── setup.py                      # 安装脚本
├── pyproject.toml                # 项目配置
├── .gitignore                    # Git忽略文件
└── README.md                     # 项目说明
```

## 3. 核心模块设计

### 3.1 应用主类 (app.py)
```python
class PathPilotApp:
    """PathPilot 应用主类"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager()
        self.engine = PathCaptureEngine()
        self.gui = GUIManager()
        
    def initialize(self):
        """初始化应用"""
        self.config.load()
        self.db.initialize()
        self.engine.start()
        self.gui.show_tray_icon()
        
    def run(self):
        """运行应用主循环"""
        self.gui.run()
        
    def shutdown(self):
        """关闭应用"""
        self.engine.stop()
        self.db.close()
        self.gui.cleanup()
```

### 3.2 无感历史捕获引擎 (path_engine.py)
```python
class PathCaptureEngine:
    """无感历史捕获引擎"""
    
    def __init__(self):
        self.window_monitor = WindowMonitor()
        self.path_filter = PathFilter()
        self.deduplicator = PathDeduplicator()
        self.importance_calc = ImportanceCalculator()
        self.event_queue = Queue()
        
    def start(self):
        """启动引擎"""
        self.window_monitor.start()
        self.start_processing_thread()
        
    def stop(self):
        """停止引擎"""
        self.window_monitor.stop()
        self.processing_thread.join()
        
    def process_path_event(self, event):
        """处理路径事件"""
        # 1. 过滤检查
        if not self.path_filter.should_record(event.path):
            return
            
        # 2. 去重检查
        if self.deduplicator.is_duplicate(event.path):
            return
            
        # 3. 计算重要性
        importance = self.importance_calc.calculate(event.path)
        
        # 4. 保存记录
        self.save_path_record(event.path, importance)
```

### 3.3 数据库管理器 (db_manager.py)
```python
class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path="data/pathpilot.db"):
        self.db_path = db_path
        self.connection = None
        
    def initialize(self):
        """初始化数据库"""
        self.connection = sqlite3.connect(self.db_path)
        self.create_tables()
        
    def create_tables(self):
        """创建数据库表"""
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS path_records (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                first_visit DATETIME,
                last_visit DATETIME,
                visit_count INTEGER DEFAULT 1,
                importance_score INTEGER DEFAULT 100,
                is_favorite BOOLEAN DEFAULT FALSE,
                tags TEXT,
                status TEXT DEFAULT 'active'
            )
        """)
        self.connection.commit()
        
    def insert_path_record(self, record):
        """插入路径记录"""
        # 实现插入逻辑
        
    def get_recent_paths(self, limit=100):
        """获取最近访问的路径"""
        # 实现查询逻辑
```

### 3.4 GUI管理器 (gui模块)
```python
class GUIManager:
    """GUI管理器"""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication([])
        self.tray_icon = None
        self.floating_ball = None
        self.main_window = None
        
    def show_tray_icon(self):
        """显示系统托盘图标"""
        self.tray_icon = TrayIcon()
        self.tray_icon.show()
        
    def show_floating_ball(self):
        """显示悬浮球"""
        self.floating_ball = FloatingBall()
        self.floating_ball.show()
        
    def show_main_window(self):
        """显示主窗口"""
        self.main_window = MainWindow()
        self.main_window.show()
        
    def run(self):
        """运行GUI主循环"""
        return self.app.exec()
```

## 4. 技术实现细节

### 4.1 系统交互技术

#### 4.1.1 窗口监控
```python
# 使用 pywin32 监听窗口事件
import win32gui
import win32con
import win32api

class WindowMonitor:
    def __init__(self):
        self.hook = None
        
    def start(self):
        """启动窗口监控"""
        # 设置窗口事件钩子
        self.hook = win32gui.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,
            win32con.EVENT_SYSTEM_FOREGROUND,
            0,
            self._event_callback,
            0,
            0,
            win32con.WINEVENT_OUTOFCONTEXT
        )
        
    def _event_callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        """窗口事件回调"""
        if self._is_explorer_window(hwnd):
            path = self._get_explorer_path(hwnd)
            if path:
                self.on_path_changed(path)
```

#### 4.1.2 路径获取
```python
# 使用 comtypes 调用 UI Automation
import comtypes
from comtypes.client import CreateObject

class ExplorerPathReader:
    def __init__(self):
        self.automation = CreateObject(
            "{FF48DBA4-60EF-4201-AA87-54103EEF594E}",
            interface=comtypes.gen.UIAutomationClient.IUIAutomation
        )
        
    def get_explorer_path(self, hwnd):
        """获取资源管理器路径"""
        try:
            element = self.automation.ElementFromHandle(hwnd)
            # 查找地址栏
            condition = self.automation.CreatePropertyCondition(
                comtypes.gen.UIAutomationClient.UIA_AutomationIdPropertyId,
                1001
            )
            address_bar = element.FindFirst(
                comtypes.gen.UIAutomationClient.TreeScope_Descendants,
                condition
            )
            if address_bar:
                value_pattern = address_bar.GetCurrentPattern(
                    comtypes.gen.UIAutomationClient.UIA_ValuePatternId
                )
                return value_pattern.CurrentValue
        except Exception as e:
            logging.error(f"获取路径失败: {e}")
        return None
```

### 4.2 数据存储技术

#### 4.2.1 数据模型
```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class PathRecord:
    """路径记录数据模型"""
    id: str
    path: str
    first_visit: datetime
    last_visit: datetime
    visit_count: int = 1
    importance_score: int = 100
    is_favorite: bool = False
    tags: List[str] = None
    status: str = 'active'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'path': self.path,
            'first_visit': self.first_visit.isoformat(),
            'last_visit': self.last_visit.isoformat(),
            'visit_count': self.visit_count,
            'importance_score': self.importance_score,
            'is_favorite': self.is_favorite,
            'tags': self.tags or [],
            'status': self.status
        }
```

### 4.3 GUI技术

#### 4.3.1 系统托盘图标
```python
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon("resources/icons/tray.png"))
        self.setup_menu()
        self.activated.connect(self.on_activated)
        
    def setup_menu(self):
        """设置右键菜单"""
        menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_main_window)
        menu.addAction(show_action)
        
        privacy_action = QAction("隐私模式", self)
        privacy_action.setCheckable(True)
        privacy_action.triggered.connect(self.toggle_privacy_mode)
        menu.addAction(privacy_action)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
```

#### 4.3.2 悬浮球
```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor

class FloatingBall(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(16, 16)
        
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_to_tray)
        
        self.move_to_edge()
        
    def paintEvent(self, event):
        """绘制悬浮球"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 120, 215, 180))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 16, 16)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.hide_timer.stop()
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hide_timer.start(10000)  # 10秒后隐藏
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.show_main_window()
```

## 5. 开发环境配置

### 5.1 Python环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 5.2 依赖列表 (requirements.txt)
```
PySide6>=6.5.0
pywin32>=305
comtypes>=1.4.0
psutil>=5.9.0
Pillow>=9.0.0
```

### 5.3 开发工具
- **IDE**: PyCharm 或 VS Code
- **版本控制**: Git
- **代码风格**: PEP 8
- **类型检查**: mypy
- **测试框架**: pytest

## 6. 构建与部署

### 6.1 打包为exe
```bash
# 使用 PyInstaller 打包
pyinstaller --onefile --windowed --icon=resources/icons/app.ico src/main.py

# 或者使用更高级的打包选项
pyinstaller --onefile --windowed --icon=resources/icons/app.ico \
            --add-data="resources;resources" \
            --add-data="config;config" \
            --name=PathPilot \
            src/main.py
```

### 6.2 制作安装程序
```bash
# 使用 NSIS 或 Inno Setup 制作安装程序
# 具体脚本见 installer/ 目录
```

## 7. 测试策略

### 7.1 单元测试
```python
# tests/test_core/test_path_filter.py
import pytest
from src.core.path_filter import PathFilter

class TestPathFilter:
    def setup_method(self):
        self.filter = PathFilter()
        
    def test_system_path_excluded(self):
        assert self.filter.should_exclude("C:\\Windows\\System32") == True
        
    def test_user_path_allowed(self):
        assert self.filter.should_exclude("C:\\Users\\test\\Documents") == False
```

### 7.2 集成测试
```python
# tests/test_integration/test_path_capture.py
import pytest
from src.core.path_engine import PathCaptureEngine

class TestPathCapture:
    def test_path_capture_flow(self):
        # 模拟路径捕获流程
        engine = PathCaptureEngine()
        # 测试完整流程
```

## 8. 性能优化

### 8.1 数据库优化
- 使用连接池
- 批量写入操作
- 定期清理过期数据
- 建立合适的索引

### 8.2 GUI优化
- 使用模型/视图架构
- 延迟加载数据
- 虚拟滚动列表
- 异步数据加载

### 8.3 内存优化
- 使用弱引用
- 及时释放资源
- 限制缓存大小
- 定期垃圾回收

## 9. 安全考虑

### 9.1 数据安全
- 本地存储，不上传云端
- 数据库文件可加密
- 支持隐私模式
- 敏感路径自动过滤

### 9.2 系统安全
- 最小权限原则
- 不修改系统文件
- 不注入其他进程
- 安全的错误处理

## 10. 未来扩展

### 10.1 插件系统
- 支持自定义过滤器
- 支持数据导出
- 支持第三方集成

### 10.2 功能扩展
- 跨设备同步
- 智能推荐
- 语音控制
- 手势操作