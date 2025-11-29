"""
Just use the helper methods
set_log_level(log_level) to set log level
and the log() method to log messages
refer to the colors class to know the colors available
"""
import logging
import inspect
import os
import json
import datetime
import sys
from typing import Optional

class Colors:
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Text styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    # Additional colors
    GRAY = '\033[90m'
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_MAGENTA = '\033[95m'
    LIGHT_CYAN = '\033[96m'

    # Additional background colors
    BG_GRAY = '\033[100m'
    BG_LIGHT_RED = '\033[101m'
    BG_LIGHT_GREEN = '\033[102m'
    BG_LIGHT_YELLOW = '\033[103m'
    BG_LIGHT_BLUE = '\033[104m'
    BG_LIGHT_MAGENTA = '\033[105m'
    BG_LIGHT_CYAN = '\033[106m'

    # Additional text styles
    ITALIC = '\033[3m'
    STRIKETHROUGH = '\033[9m'

    @staticmethod
    def get_code(color_name: str) -> str:
        if not color_name:
            return Colors.RESET
        color_name = color_name.upper()
        if hasattr(Colors, color_name):
            return getattr(Colors, color_name)
        return Colors.RESET
    
    @staticmethod
    def get_color(color_name: str) -> str:
         return Colors.get_code(color_name)

class ConsoleFilter(logging.Filter):
    def filter(self, record):
        return not getattr(record, 'skip_console', False)

class CustomFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        self.default_format = "%(color)s%(file)s:%(line)s | %(name)s | \033[4m%(levelname)s%(reset)s%(color)s | %(asctime)s ||-> %(msg)s%(reset)s"

    def format(self, record):
        # Set default color if not present
        if not hasattr(record, 'color'):
            record.color = Colors.RESET
        if not hasattr(record, 'reset'):
            record.reset = Colors.RESET
        
        # Populate custom fields
        record.file = os.path.relpath(record.pathname) if os.path.exists(record.pathname) else record.pathname
        record.line = record.lineno
        
        # Format the message
        log_fmt = self.default_format
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %I:%M:%S %p")
        return formatter.format(record)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %I:%M:%S %p"),
            "file": os.path.relpath(record.pathname) if os.path.exists(record.pathname) else record.pathname,
            "line": record.lineno,
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_data)

class LOGGER:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.logger = logging.getLogger("requestez")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False # Prevent double logging if root logger is configured
        
        # Console Handler
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(CustomFormatter())
        self.console_handler.addFilter(ConsoleFilter())
        self.logger.addHandler(self.console_handler)
        
        self.file_handler = None
        self.json_file_handler = None
        self.initialized = True

    def set_level(self, level):
        level_code = self._convert_log_level(level)
        self.logger.setLevel(level_code)
        # Also set handler levels to ensure they capture everything
        for handler in self.logger.handlers:
            handler.setLevel(level_code)

    def enable_file_logging(self, enabled: bool = True, log_path: Optional[str] = None, json_path: Optional[str] = None):
        if not enabled:
            self.disable_file_logging()
            return

        if log_path:
            if self.file_handler:
                self.logger.removeHandler(self.file_handler)
            self.file_handler = logging.FileHandler(log_path)
            self.file_handler.setFormatter(CustomFormatter()) # Use same format for text file
            self.logger.addHandler(self.file_handler)
            
        if json_path:
            if self.json_file_handler:
                self.logger.removeHandler(self.json_file_handler)
            self.json_file_handler = logging.FileHandler(json_path)
            self.json_file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(self.json_file_handler)

        print(f"Logging enabled. Logs will be saved to {log_path} and {json_path}")

    def disable_file_logging(self):
        if self.file_handler:
            self.logger.removeHandler(self.file_handler)
            self.file_handler = None
        if self.json_file_handler:
            self.logger.removeHandler(self.json_file_handler)
            self.json_file_handler = None

    def _convert_log_level(self, level):
        if isinstance(level, int):
            return level
        level = level.lower()
        mapping = {
            "i": logging.INFO, "info": logging.INFO,
            "w": logging.WARNING, "warning": logging.WARNING,
            "c": logging.CRITICAL, "critical": logging.CRITICAL,
            "e": logging.ERROR, "error": logging.ERROR,
            "d": logging.DEBUG, "debug": logging.DEBUG
        }
        return mapping.get(level, logging.INFO)

    def log(self, level, *messages, **kwargs):
        level_code = self._convert_log_level(level)
        
        # Handle color
        color = kwargs.get('color')
        color_code = Colors.get_color(color)
        
        # Format messages
        sep = kwargs.get('sep', ' ')
        msg = sep.join(map(str, messages))
        
        # Add extra context for the formatter
        extra = {'color': color_code}
        
        if kwargs.get('full_stack'):
             import traceback
             msg += "\n" + "".join(traceback.format_stack()[:-1])

        # Determine stack level
        stack_depth = kwargs.get('stack_depth', 2)
        
        # Check if we should skip console logging (handled by caller if stack=False)
        if kwargs.get('skip_console'):
            extra['skip_console'] = True
        
        self.logger.log(level_code, msg, extra=extra, stacklevel=stack_depth)

    def stack(self, level, *messages, **kwargs):
        kwargs['full_stack'] = True
        kwargs['stack_depth'] = kwargs.get('stack_depth', 2) + 1
        self.log(level, *messages, **kwargs)

    def level(self):
        return self.logger.getEffectiveLevel()

    def get_color(self):
        return Colors.RESET # Default

logger = LOGGER()

def set_log_level(log_level="i"):
    logger.set_level(log_level)

def get_logger():
    return logger

def log(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, log_level="info", msg="args : ", full_stack=False, **kwargs):
    # 'msg' prefix is handled differently, we just prepend it if provided
    if msg and msg != "args : ":
         messages = (msg,) + messages
    
    # If stack or full_stack is True, behave like a logger (formatted)
    if stack or full_stack:
        stack_depth = kwargs.get('stack_depth', 3)
        logger.log(log_level, *messages, sep=sep, color=color, full_stack=full_stack, stack_depth=stack_depth)
    else:
        # Behave like print() but also log to file
        # 1. Print to console manually
        color_code = Colors.get_color(color)
        reset_code = Colors.RESET if color else ""
        
        # Construct message for printing
        print_msg = sep.join(map(str, messages))
        
        if color:
            sys.stdout.write(color_code)
        
        sys.stdout.write(print_msg)
        
        if color:
            sys.stdout.write(reset_code)
            
        sys.stdout.write(end)
        if flush:
            sys.stdout.flush()
            
        # 2. Log to file (skip console)
        # We need to log it so it appears in the file if file logging is enabled
        # But we don't want it to appear in console again.
        # We use a special flag 'skip_console'
        stack_depth = kwargs.get('stack_depth', 3)
        logger.log(log_level, *messages, sep=sep, color=color, full_stack=full_stack, stack_depth=stack_depth, skip_console=True)

def info(*messages, sep=" ", end="\n", flush=False, color="blue", stack=False, msg="args : ", full_stack=False):
    # User -> info -> log -> logger.log
    # Depth: 4
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="info", msg=msg, full_stack=full_stack, stack_depth=4)

def debug(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, msg="args : ", full_stack=False):
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="debug", msg=msg, full_stack=full_stack, stack_depth=4)

def warning(*messages, sep=" ", end="\n", flush=False, color="yellow", stack=False, msg="args : ", full_stack=False):
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="warning", msg=msg, full_stack=full_stack, stack_depth=4)

def error(*messages, sep=" ", end="\n", flush=False, color="red", stack=False, msg="args : ", full_stack=False):
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="error", msg=msg, full_stack=full_stack, stack_depth=4)

def critical(*messages, sep=" ", end="\n", flush=False, color="orange", stack=False, msg="args : ", full_stack=False):
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="critical", msg=msg, full_stack=full_stack, stack_depth=4)
