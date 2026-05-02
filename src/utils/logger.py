"""
PathPilot 日志工具模块

提供统一的日志记录功能。
"""

import logging
import os
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler


class Logger:
    """日志工具类"""
    
    def __init__(self, log_dir: str = "logs", log_name: str = "pathpilot", use_global: bool = True):
        """
        初始化日志工具
        
        Args:
            log_dir: 日志文件目录
            log_name: 日志文件名前缀
            use_global: 是否使用全局logger（用于测试时可设置为False）
        """
        self.log_dir = log_dir
        self.log_name = log_name
        self.use_global = use_global
        self.logger: Optional[logging.Logger] = None
        self._setup_logger()
        
    def _setup_logger(self):
        """设置日志器"""
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建日志器
        if self.use_global:
            self.logger = logging.getLogger("PathPilot")
        else:
            # 为测试创建独立的logger
            self.logger = logging.getLogger(f"PathPilot_{id(self)}")
            
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if self.logger.handlers:
            return
            
        # 创建文件处理器（最大 2MB，保留 3 个备份）
        log_file = os.path.join(
            self.log_dir, 
            f"{self.log_name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = RotatingFileHandler(
            log_file, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)  # 生产环境只记录 INFO 及以上
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def info(self, message: str):
        """记录信息日志"""
        if self.logger:
            self.logger.info(message)
        
    def error(self, message: str, exc_info: bool = True):
        """记录错误日志"""
        if self.logger:
            self.logger.error(message, exc_info=exc_info)
        
    def warning(self, message: str):
        """记录警告日志"""
        if self.logger:
            self.logger.warning(message)
        
    def debug(self, message: str):
        """记录调试日志"""
        if self.logger:
            self.logger.debug(message)
            
    def critical(self, message: str):
        """记录严重错误日志"""
        if self.logger:
            self.logger.critical(message)


# 全局日志实例
_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """
    获取全局日志实例
    
    Returns:
        Logger实例
    """
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger


def setup_logger(log_dir: str = "logs", log_name: str = "pathpilot") -> Logger:
    """
    设置全局日志实例
    
    Args:
        log_dir: 日志文件目录
        log_name: 日志文件名前缀
        
    Returns:
        Logger实例
    """
    global _logger
    _logger = Logger(log_dir, log_name)
    return _logger