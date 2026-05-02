"""
日志工具模块单元测试
"""

import os
import tempfile
import pytest
from src.utils.logger import Logger, get_logger, setup_logger


class TestLogger:
    """Logger 测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        
        # 清理所有logger处理器
        import logging
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith("PathPilot_"):
                logger = logging.getLogger(name)
                logger.handlers.clear()
        
    def teardown_method(self):
        """测试后清理"""
        # 关闭所有日志处理器，释放文件句柄
        import logging
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        
        # 清理临时文件
        import shutil
        import time
        time.sleep(0.1)  # 等待文件释放
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except PermissionError:
                pass  # 忽略权限错误
            
    def test_logger_initialization(self):
        """测试日志器初始化"""
        logger = Logger(self.log_dir, "test", use_global=False)
        
        # 验证日志目录创建
        assert os.path.exists(self.log_dir)
        
        # 验证日志器创建
        assert logger.logger is not None
        
    def test_logger_file_creation(self):
        """测试日志文件创建"""
        logger = Logger(self.log_dir, "test", use_global=False)
        
        # 记录一条日志
        logger.info("Test message")
        
        # 验证日志文件创建
        log_files = os.listdir(self.log_dir)
        assert len(log_files) == 1
        assert log_files[0].startswith("test_")
        assert log_files[0].endswith(".log")
        
    def test_logger_levels(self):
        """测试日志级别"""
        logger = Logger(self.log_dir, "test", use_global=False)
        
        # 测试不同级别的日志
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # 验证日志文件存在
        log_files = os.listdir(self.log_dir)
        assert len(log_files) == 1
        
    def test_logger_content(self):
        """测试日志内容"""
        logger = Logger(self.log_dir, "test", use_global=False)
        
        # 记录测试消息
        test_message = "This is a test message"
        logger.info(test_message)
        
        # 读取日志文件内容
        log_files = os.listdir(self.log_dir)
        log_file_path = os.path.join(self.log_dir, log_files[0])
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 验证日志内容包含测试消息
        assert test_message in content
        assert "INFO" in content
        
    def test_logger_multiple_messages(self):
        """测试多条日志消息"""
        logger = Logger(self.log_dir, "test", use_global=False)
        
        # 记录多条消息
        messages = ["Message 1", "Message 2", "Message 3"]
        for msg in messages:
            logger.info(msg)
            
        # 读取日志文件内容
        log_files = os.listdir(self.log_dir)
        log_file_path = os.path.join(self.log_dir, log_files[0])
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 验证所有消息都记录
        for msg in messages:
            assert msg in content
            
    def test_logger_timestamp(self):
        """测试日志时间戳"""
        logger = Logger(self.log_dir, "test", use_global=False)
        
        # 记录测试消息
        logger.info("Timestamp test")
        
        # 读取日志文件内容
        log_files = os.listdir(self.log_dir)
        log_file_path = os.path.join(self.log_dir, log_files[0])
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 验证时间戳格式（YYYY-MM-DD HH:MM:SS）
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        assert re.search(timestamp_pattern, content) is not None