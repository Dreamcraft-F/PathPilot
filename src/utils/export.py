"""
PathPilot 导出功能模块

支持将历史记录导出为 CSV 或 JSON 格式。
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Optional
from src.database.models import PathRecord


class ExportManager:
    """导出管理器"""
    
    def __init__(self, db_manager):
        """
        初始化导出管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self._logger = None
        
    def set_logger(self, logger):
        """设置日志记录器"""
        self._logger = logger
        
    def _log(self, level: str, message: str):
        """内部日志方法"""
        if self._logger:
            getattr(self._logger, level)(message)
            
    def export_to_csv(self, output_path: str, records: Optional[List[PathRecord]] = None) -> bool:
        """
        导出为 CSV 文件
        
        Args:
            output_path: 输出文件路径
            records: 要导出的记录列表，为 None 时导出所有记录
            
        Returns:
            是否成功
        """
        try:
            if records is None:
                records = self.db_manager.get_recent_paths(10000)
                
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow([
                    '路径', '首次访问', '最后访问', '访问次数',
                    '重要性分数', '是否收藏', '状态'
                ])
                
                # 写入数据
                for record in records:
                    writer.writerow([
                        record.path,
                        record.first_visit.strftime('%Y-%m-%d %H:%M:%S'),
                        record.last_visit.strftime('%Y-%m-%d %H:%M:%S'),
                        record.visit_count,
                        record.importance_score,
                        '是' if record.is_favorite else '否',
                        record.status
                    ])
                    
            self._log("info", f"已导出 {len(records)} 条记录到 CSV: {output_path}")
            return True
        except Exception as e:
            self._log("error", f"导出 CSV 失败: {e}")
            return False
            
    def export_to_json(self, output_path: str, records: Optional[List[PathRecord]] = None) -> bool:
        """
        导出为 JSON 文件
        
        Args:
            output_path: 输出文件路径
            records: 要导出的记录列表，为 None 时导出所有记录
            
        Returns:
            是否成功
        """
        try:
            if records is None:
                records = self.db_manager.get_recent_paths(10000)
                
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            # 转换为字典列表
            data = []
            for record in records:
                data.append({
                    'path': record.path,
                    'first_visit': record.first_visit.isoformat(),
                    'last_visit': record.last_visit.isoformat(),
                    'visit_count': record.visit_count,
                    'importance_score': record.importance_score,
                    'is_favorite': record.is_favorite,
                    'status': record.status
                })
                
            # 写入 JSON 文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_time': datetime.now().isoformat(),
                    'record_count': len(data),
                    'records': data
                }, f, ensure_ascii=False, indent=2)
                
            self._log("info", f"已导出 {len(records)} 条记录到 JSON: {output_path}")
            return True
        except Exception as e:
            self._log("error", f"导出 JSON 失败: {e}")
            return False
            
    def get_export_filename(self, format_type: str) -> str:
        """
        生成导出文件名
        
        Args:
            format_type: 格式类型 (csv/json)
            
        Returns:
            文件名
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"pathpilot_export_{timestamp}.{format_type}"
