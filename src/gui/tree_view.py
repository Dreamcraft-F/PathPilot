"""
PathPilot 树形目录视图组件

以树形结构显示路径，类似VSCode的侧边栏。
使用PySide6的QTreeWidget实现真正的树形结构。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPainter

from src.database.models import PathRecord
from src.utils.path_utils import PathUtils


@dataclass
class PathNode:
    """路径节点"""
    name: str                           # 显示名称
    full_path: str                      # 完整路径
    record: Optional[PathRecord] = None # 关联的路径记录
    children: Dict[str, 'PathNode'] = field(default_factory=dict)
    
    @property
    def is_leaf(self) -> bool:
        """是否是叶子节点"""
        return len(self.children) == 0


class PathTreeItem(QTreeWidgetItem):
    """路径树形项"""
    
    def __init__(self, node: PathNode, parent=None):
        """初始化路径树形项"""
        super().__init__(parent)
        self.node = node
        
        # 设置显示
        self._update_display()
        
        # 设置标志
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        
    def _update_display(self):
        """更新显示"""
        if self.node.record:
            # 有记录的节点：显示路径名、收藏标记、时间
            record = self.node.record
            time_str = self._format_time(record.last_visit)
            fav_mark = "★ " if record.is_favorite else ""
            
            # 显示名称
            display_text = f"{self.node.name}"
            self.setText(0, display_text)
            
            # 设置工具提示
            self.setToolTip(0, f"路径: {self.node.full_path}\n"
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
        else:
            # 目录节点：只显示名称
            self.setText(0, self.node.name)
            self.setToolTip(0, self.node.full_path)
            
            # 设置字体
            font = QFont()
            font.setBold(True)
            self.setFont(0, font)
            
    def _format_time(self, dt: datetime) -> str:
        """格式化时间显示"""
        return PathUtils.format_time(dt)


class DirectoryTreeView(QWidget):
    """目录树形视图"""
    
    # 信号
    path_selected = Signal(str)  # 路径被选中
    path_deleted = Signal(str)   # 路径被删除
    favorite_toggled = Signal(str, bool)  # 收藏状态切换
    
    def __init__(self, parent=None):
        """初始化目录树形视图"""
        super().__init__(parent)
        
        # 存储路径记录
        self.all_records = []
        
        # 存储节点映射
        self.path_to_item = {}
        
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
        self.tree.setAnimated(False)  # 关闭动画，提高响应速度
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
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        main_layout.addWidget(self.tree)
        
    def update_data(self, records: List[PathRecord]):
        """
        更新数据
        
        Args:
            records: 路径记录列表
        """
        self.all_records = records
        self.path_to_item = {}
        self.tree.clear()
        
        # 构建树结构
        root = self._build_tree(records)
        
        # 渲染树
        self._render_tree(root, self.tree.invisibleRootItem())
        
        # 展开前两层
        self.tree.expandToDepth(1)
        
    def _build_tree(self, records: List[PathRecord]) -> PathNode:
        """
        构建树结构
        
        Args:
            records: 路径记录列表
            
        Returns:
            根节点
        """
        import os
        
        root = PathNode(name="", full_path="")
        
        # 按路径排序
        sorted_records = sorted(records, key=lambda r: r.path.lower())
        
        for record in sorted_records:
            # 分割路径 - 使用 os.sep 处理不同系统的路径分隔符
            path = record.path.replace('/', os.sep)
            parts = [p for p in path.split(os.sep) if p]
            
            if not parts:
                continue
                
            # 处理盘符
            if len(parts[0]) == 2 and parts[0][1] == ':':
                drive = parts[0].upper()
                if drive not in root.children:
                    root.children[drive] = PathNode(
                        name=drive,
                        full_path=drive + os.sep
                    )
                current = root.children[drive]
                parts = parts[1:]
            else:
                # 相对路径
                if 'other' not in root.children:
                    root.children['other'] = PathNode(
                        name='其他',
                        full_path=''
                    )
                current = root.children['other']
            
            # 如果没有更多路径部分，说明是盘符本身
            if not parts:
                # 盘符节点，关联记录
                current.record = record
                continue
            
            # 遍历路径部分
            for i, part in enumerate(parts):
                is_last = (i == len(parts) - 1)
                
                if is_last:
                    # 叶子节点
                    if part not in current.children:
                        current.children[part] = PathNode(
                            name=part,
                            full_path=record.path,
                            record=record
                        )
                    else:
                        # 更新现有节点
                        current.children[part].record = record
                        current.children[part].full_path = record.path
                else:
                    # 目录节点
                    if part not in current.children:
                        current.children[part] = PathNode(
                            name=part,
                            full_path=current.full_path + part + os.sep
                        )
                    elif current.children[part].record and not current.children[part].children:
                        # 如果节点之前是叶子节点，但现在需要作为目录节点
                        # 保留记录，但确保它能被展开
                        pass
                    current = current.children[part]
        
        return root
        
    def _render_tree(self, node: PathNode, parent_item: QTreeWidgetItem):
        """
        渲染树
        
        Args:
            node: 路径节点
            parent_item: 父项
        """
        # 排序：有子节点的在前，然后按名称排序
        sorted_children = sorted(
            node.children.values(),
            key=lambda n: (len(n.children) == 0, n.name.lower())
        )
        
        for child in sorted_children:
            item = PathTreeItem(child, parent_item)
            self.path_to_item[child.full_path.lower()] = item
            
            # 递归渲染子节点（如果有）
            if child.children:
                self._render_tree(child, item)
                
    def _on_item_clicked(self, item: PathTreeItem, column: int):
        """项被点击"""
        if item.node.record:
            # 有关联记录的节点（叶子或目录）都可以跳转
            self.path_selected.emit(item.node.full_path)
        
    def _on_item_expanded(self, item: PathTreeItem):
        """项被展开"""
        pass
        
    def _on_item_collapsed(self, item: PathTreeItem):
        """项被收起"""
        pass
        
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.tree.itemAt(pos)
        if not item or not isinstance(item, PathTreeItem):
            return
            
        if not item.node.record:
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
        if item.node.record.is_favorite:
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
        
    def _copy_path(self, item: PathTreeItem):
        """复制路径"""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(item.node.full_path)
        
    def _toggle_favorite(self, item: PathTreeItem):
        """切换收藏状态 - 仅发送信号，由上层处理业务逻辑"""
        record = item.node.record
        new_favorite_state = not record.is_favorite
        self.favorite_toggled.emit(record.id, new_favorite_state)
        
    def _delete_path(self, item: PathTreeItem):
        """删除路径（直接删除，不确认）"""
        self.path_deleted.emit(item.node.record.id)
        
    def flash_item(self, path: str):
        """
        对新捕获的路径做闪光效果
        
        Args:
            path: 路径
        """
        from PySide6.QtCore import QTimer
        
        key = path.lower()
        if key in self.path_to_item:
            item = self.path_to_item[key]
            # 保存原始背景
            original_bg = item.background(0)
            # 设置黄色高亮
            item.setBackground(0, QColor("#fff3cd"))
            # 500ms后恢复（检查 item 是否还存在）
            def restore():
                try:
                    if item and item.treeWidget():
                        item.setBackground(0, original_bg)
                except RuntimeError:
                    pass
            QTimer.singleShot(500, restore)