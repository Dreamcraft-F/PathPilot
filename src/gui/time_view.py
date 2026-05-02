"""
PathPilot 时间视图组件

按时间分组显示路径。
"""

from typing import List, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from src.database.models import PathRecord
from src.utils.path_utils import PathUtils


class TimeViewItem(QTreeWidgetItem):
    """时间视图项"""
    
    def __init__(self, record: PathRecord, parent=None):
        """初始化时间视图项"""
        super().__init__(parent)
        self.record = record
        
        # 设置显示
        self._update_display()
        
        # 设置标志
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        
    def _update_display(self):
        """更新显示"""
        record = self.record
        
        # 格式化时间
        time_str = self._format_time(record.last_visit)
        
        # 收藏标记
        fav_mark = "★ " if record.is_favorite else ""
        
        # 显示文本
        display_text = f"{record.path}  {time_str}"
        self.setText(0, display_text)
        
        # 设置工具提示
        self.setToolTip(0, f"路径: {record.path}\n"
                          f"访问次数: {record.visit_count}\n"
                          f"最后访问: {record.last_visit.strftime('%Y-%m-%d %H:%M')}")
        
        # 设置字体
        font = QFont()
        if record.is_favorite:
            font.setBold(True)
        self.setFont(0, font)
        
        # 设置颜色
        if record.is_favorite:
            self.setForeground(0, QColor("#0078d7"))
            
    def _format_time(self, dt: datetime) -> str:
        """格式化时间显示"""
        return PathUtils.format_time(dt)


class TimeGroupWidget(QWidget):
    """时间分组组件"""
    
    # 信号
    path_selected = Signal(str)  # 路径被选中
    path_deleted = Signal(str)   # 路径被删除
    favorite_toggled = Signal(str, bool)  # 收藏状态切换
    
    def __init__(self, parent=None):
        """初始化时间分组组件"""
        super().__init__(parent)
        
        # 存储路径记录
        self.all_records = []
        
        # 设置UI
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        self.tree.setRootIsDecorated(True)
        self.tree.setItemsExpandable(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # 设置样式 - 使用 Fluent 默认样式
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                outline: none;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 4px 4px;
                border: none;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: rgba(0, 0, 0, 0.06);
            }
            QTreeWidget::item:hover {
                background-color: rgba(0, 0, 0, 0.04);
            }
        """)
        
        # 连接信号
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        main_layout.addWidget(self.tree)
        
    def update_data(self, time_groups: Dict[str, List[PathRecord]]):
        """
        更新数据
        
        Args:
            time_groups: 时间分组 {时间标签: [路径记录列表]}
        """
        self.tree.clear()
        
        # 时间标签顺序
        label_order = ['today', 'yesterday', 'this_week', 'older']
        label_names = {
            'today': '📅 今日',
            'yesterday': '📅 昨日',
            'this_week': '📅 本周',
            'older': '📅 更早'
        }
        
        for label in label_order:
            if label in time_groups and time_groups[label]:
                # 创建分组项
                group_item = QTreeWidgetItem(self.tree)
                group_item.setText(0, f"{label_names[label]} ({len(time_groups[label])})")
                
                # 设置字体
                font = QFont()
                font.setBold(True)
                group_item.setFont(0, font)
                
                # 添加路径
                for record in time_groups[label]:
                    item = TimeViewItem(record, group_item)
                    
                # 默认展开今日分组
                if label == 'today':
                    group_item.setExpanded(True)
                    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """项被点击"""
        if isinstance(item, TimeViewItem):
            self.path_selected.emit(item.record.path)
            
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.tree.itemAt(pos)
        if not item or not isinstance(item, TimeViewItem):
            return
            
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        
        # 复制路径
        copy_action = QAction("复制路径", menu)
        copy_action.triggered.connect(lambda checked, i=item: self._copy_path(i))
        menu.addAction(copy_action)
        
        # 收藏/取消收藏
        if item.record.is_favorite:
            fav_action = QAction("取消收藏", menu)
        else:
            fav_action = QAction("收藏", menu)
        fav_action.triggered.connect(lambda checked, i=item: self._toggle_favorite(i))
        menu.addAction(fav_action)
        
        menu.addSeparator()
        
        # 删除
        delete_action = QAction("删除", menu)
        delete_action.triggered.connect(lambda checked, i=item: self._delete_path(i))
        menu.addAction(delete_action)
        
        menu.exec_(self.tree.mapToGlobal(pos))
        
    def _copy_path(self, item: TimeViewItem):
        """复制路径"""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(item.record.path)
        
    def _toggle_favorite(self, item: TimeViewItem):
        """Toggle favorite - emit signal only"""
        record = item.record
        new_favorite_state = not record.is_favorite
        self.favorite_toggled.emit(record.id, new_favorite_state)
        
    def _delete_path(self, item: TimeViewItem):
        """Delete path"""
        self.path_deleted.emit(item.record.id)
        
    def flash_item(self, path: str):
        """Flash newly captured path item"""
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QColor
        
        def search_items(parent):
            for i in range(parent.childCount()):
                item = parent.child(i)
                if isinstance(item, TimeViewItem) and item.record.path.lower() == path.lower():
                    original_bg = item.background(0)
                    item.setBackground(0, QColor("#fff3cd"))
                    # 500ms后恢复（检查 item 是否还存在）
                    def restore():
                        try:
                            if item and item.treeWidget():
                                item.setBackground(0, original_bg)
                        except RuntimeError:
                            pass
                    QTimer.singleShot(500, restore)
                    return True
                if search_items(item):
                    return True
            return False
            
        root = self.tree.invisibleRootItem()
        search_items(root)