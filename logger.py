import logging
import logging.handlers
import os
import configparser
from datetime import datetime


class Logger:
    """自定义日志类"""

    def __init__(self, config_path="config.ini"):
        self.config_path = config_path
        self.logger = None
        self._init_logger()

    def _init_logger(self):
        """初始化日志配置"""
        # 创建logger
        self.logger = logging.getLogger("signClass")
        self.logger.setLevel(logging.DEBUG)  # 默认设置最低级别

        # 读取配置
        config = configparser.ConfigParser(
            allow_no_value=False,
            comment_prefixes=('#', ';'),
            inline_comment_prefixes=('#', ';'),
            strict=True,
        )

        try:
            if config.read(self.config_path, encoding='utf-8'):
                # 从配置文件中读取日志设置
                log_level = config.get("logging", "level", fallback="INFO").upper()
                log_file = config.get("logging", "file", fallback="app.log")
                log_to_console = config.getboolean("logging", "console", fallback=True)
                log_to_file = config.getboolean("logging", "file_enabled", fallback=True)
                max_file_size = config.getint("logging", "max_file_size", fallback=10485760)  # 10MB
                backup_count = config.getint("logging", "backup_count", fallback=5)
            else:
                # 配置文件读取失败，使用默认配置
                log_level = "INFO"
                log_file = "app.log"
                log_to_console = True
                log_to_file = True
                max_file_size = 10485760  # 10MB
                backup_count = 5
        except Exception:
            # 配置文件解析失败，使用默认配置
            log_level = "INFO"
            log_file = "app.log"
            log_to_console = True
            log_to_file = True
            max_file_size = 10485760  # 10MB
            backup_count = 5

        # 设置日志级别
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(log_level, logging.INFO))

        # 清除已有的handler
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 文件输出
        if log_to_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 使用RotatingFileHandler实现日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg, *args, **kwargs):
        """DEBUG级别日志"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """INFO级别日志"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """WARNING级别日志"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """ERROR级别日志"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """CRITICAL级别日志"""
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """异常日志（自动包含异常信息）"""
        self.logger.exception(msg, *args, **kwargs)


# 创建全局日志实例
_logger_instance = None


def get_logger():
    """获取全局日志实例（单例模式）"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def setup_logging(config_path="config.ini"):
    """设置日志配置"""
    global _logger_instance
    _logger_instance = Logger(config_path)
    return _logger_instance



# 导出快捷方法
debug = lambda msg, *args, **kwargs: get_logger().debug(msg, *args, **kwargs)
info = lambda msg, *args, **kwargs: get_logger().info(msg, *args, **kwargs)
warning = lambda msg, *args, **kwargs: get_logger().warning(msg, *args, **kwargs)
error = lambda msg, *args, **kwargs: get_logger().error(msg, *args, **kwargs)
critical = lambda msg, *args, **kwargs: get_logger().critical(msg, *args, **kwargs)
exception = lambda msg, *args, **kwargs: get_logger().exception(msg, *args, **kwargs)