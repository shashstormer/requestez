"""
Just use the helper methods
set_log_level(log_level) to set log level
and the log() method to log messages
refer to the colors class to know the colors available
"""
import datetime
import logging
import inspect
import os
import json


class LOGGER:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self._format = "%(color)s%(file)s:%(line)s | %(name)s | \033[4m%(level)s%(reset)s%(color)s | %(time)s |" \
                       "|-> %(msg)s%(formatted_args)s%(reset)s"
        self._reset_color = Colors.RESET
        self._color = Colors.RESET
        self._level, self._level_name = convert_log_level("i", True)
        self.place_holders = {
            "color": "%(color)s",
            "reset": "%(reset_color)s",
            "msg": "%(msg)s",
            "args": "%(args)s",
            "file": "%(file)s",
            "line": "%(line)s",
            "time": "%(time)s",
            "level": "%(level)s",
            "arg_number": "%(arg_number)s",
            'arg_message': "%(arg_message)s",
            "formatted_args": "%(formatted_args)s",
            "name": "%(name)s",
        }
        self._args_message = "args : "
        self.args_msg_sep = "\n"
        self._args_format = f"{self.place_holders['arg_number']}. {self.place_holders['arg_message']}"
        self.args_sep = "\n"
        self.arg_msg_arg_Sep = "\n"
        self.initialized = True
        self._log_to_file_enabled = False
        self._log_file_path = None
        self._json_log_file_path = None

    def _log_to_file(self, log_data: dict):
        if not self._log_to_file_enabled or not self._log_file_path:
            return
        log_line = f"{log_data['time']} | {log_data['file']}:{log_data['line']} | {log_data['name']} | {log_data['level']} | {log_data['msg']} | {log_data['print_content']}\n"
        if not log_line.endswith("\n"):
            log_line += "\n"
        with open(self._log_file_path, "a") as f:
            f.write(log_line)

    def _export_json_log(self, log_data: dict):
        if not self._log_to_file_enabled or not self._json_log_file_path:
            return
        # json_log = {
        #     "timestamp": log_data["time"],
        #     "file": log_data["file"],
        #     "line": log_data["line"],
        #     "name": log_data["name"],
        #     "level": log_data["level"],
        #     "message": log_data["msg"],
        #     "args": log_data.get("formatted_args", "").strip(),
        # }
        json_log = log_data
        with open(self._json_log_file_path, "a") as jf:
            jf.write(json.dumps(json_log) + "\n")

    def append_log_to_files(self, log_data: dict):
        self._log_to_file(log_data)
        self._export_json_log(log_data)

    def log(self, level, *args, **kwargs):
        level_num, level = convert_log_level(level, True)
        if level_num >= self._level:
            fmt = self._format
            caller_filename, caller_lineno, caller_name = self._get_caller_location()
            args = self.formatted_args(args)
            if not kwargs.get("formatted_args"):
                kwargs['formatted_args'] = args
            if not kwargs.get("line"):
                kwargs['line'] = str(caller_lineno)
            if not kwargs.get("file"):
                kwargs['file'] = caller_filename
            if not kwargs.get("level"):
                kwargs['level'] = level
            if not kwargs.get("name"):
                kwargs['name'] = caller_name
            if not kwargs.get("time"):
                kwargs['time'] = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            if "color" in kwargs:
                kwargs['color'] = self._get_color(kwargs['color'])
            else:
                kwargs['color'] = self._color
            if "reset" in kwargs:
                kwargs['reset'] = self._get_color(kwargs['reset'])
            else:
                kwargs['reset'] = self._reset_color
            print_content = fmt % kwargs
            if not kwargs.get("only_to_file"):
                print(print_content)
            log_data = {
                "file": caller_filename,
                "line": caller_lineno,
                "name": caller_name,
                "level": level,
                "time": kwargs["time"],
                "msg": args,
                "formatted_args": kwargs["formatted_args"],
                "print_content": print_content,
                "color": kwargs["color"],
            }
            self.append_log_to_files(log_data)

    def enable_file_logging(self, enabled: bool = True, log_path=None, json_path=None):
        self._log_to_file_enabled = enabled
        if log_path is not None:
            self._log_file_path = log_path
            if not os.path.exists(log_path):
                with open(log_path, "w") as f:
                    f.write("")
        if json_path is not None:
            self._json_log_file_path = json_path
            if not os.path.exists(json_path):
                with open(json_path, "w") as f:
                    f.write("")
        if enabled:
            print(f"Logging enabled. Logs will be saved to {log_path} and {json_path}")

    def disable_file_logging(self):
        self._log_to_file_enabled = False
        self._log_file_path = None
        self._json_log_file_path = None

    def set_level(self, level):
        self._level, self._level_name = convert_log_level(level, True)

    @staticmethod
    def _get_color(color):
        if color:
            color = color.upper()
        if color and hasattr(Colors, color):
            color_code = getattr(Colors, color)
        else:
            color_code = Colors.RESET
        return color_code

    def _get_caller_location(self):
        stack = inspect.stack()
        cur_stack = stack[3]
        return self._get_location(cur_stack)

    @staticmethod
    def _get_location(cur_stack):
        name = cur_stack.function
        line = cur_stack.lineno
        file = cur_stack.filename
        try:
            rel_path = os.path.relpath(file, start=os.getcwd())
        except ValueError:
            rel_path = file
        if name == "<module>":
            name = file.split("\\")[-1]
        try:
            f_name = cur_stack[0].f_locals["self"].__class__.__name__
            name = f"{f_name}.{name}"
        except KeyError:
            pass
        return rel_path, line, name

    def set_format(self, log_format):
        self._format = self.place_holders['color'] + log_format + self.place_holders['reset']

    def set_color(self, color, reset_color="white"):
        self._color = self._get_color(color)
        self._reset_color = self._get_color(reset_color)

    def formatted_args(self, args):
        formatted = ""
        for i, arg in enumerate(args, start=1):
            fmt = self._args_format
            formatted += (" " * len(self._args_message)) + fmt % {
                'arg_number': i,
                'arg_message': arg,
            }
            formatted += self.args_sep
        formatted = formatted.strip(self.args_sep)
        if formatted:
            formatted = self.args_msg_sep + self._args_message + self.arg_msg_arg_Sep + formatted
        return formatted

    def stack(self, level, *args, **kwargs):
        level_num, level = convert_log_level(level, True)
        if level_num >= self._level:
            caller_filename, caller_lineno, caller_name = self._get_caller_location()
            args = self.formatted_args(args)
            stack = self._retrieve_formatted_stack()
            args = stack + args
            kwargs['formatted_args'] = args
            kwargs['line'] = str(caller_lineno)
            kwargs['file'] = caller_filename
            # kwargs['level'] = level
            kwargs['name'] = caller_name
            kwargs['time'] = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            self.log(level, *args, **kwargs)

    def _retrieve_formatted_stack(self):
        stack_formatted = "\n\nstack : \n"
        stacks = inspect.stack()
        stacks = stacks[3:]
        last_len = 0
        for stack in stacks:
            file, line, name = self._get_location(stack)
            stack_formatted += (" " * (last_len * 4)) + f"{file}:{line} | {name}\n"
            last_len += 1
        return stack_formatted

    def level(self):
        return self._level

    def get_color(self):
        return self._color


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


def convert_log_level(level, ret_name=False):
    """
    just when you are lazy
    :param level:
    :param ret_name:
    :return:
    """
    level = level.lower()
    if level == "i":
        level = "info"
    elif level == "w":
        level = "warning"
    elif level == "c":
        level = "critical"
    elif level == "e":
        level = "error"
    elif level == "d":
        level = "debug"
    level = level.upper()
    if ret_name:
        return [getattr(logging, level, logging.INFO), level]
    return getattr(logging, level, logging.INFO)


logger = LOGGER()


def set_log_level(log_level="i"):
    """
    This is a helper method which edits the LOGGER instance created on file import and provides a simple interface to set log level
    :param log_level: possible values = "i", "w", "e", "c", "d", "info", "warning", "error", "critical", "debug"
    :return: none
    """
    logger.set_level(log_level)


def get_logger():
    """
    This is a helper method which returns the instance of the LOGGER class created on file import
    :return:
    """
    return logger


def log(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, log_level="info", msg="args : ",
        full_stack=False):
    """
    This is a helper method which creates a LOGGER instance on file import and provides a simple interface to log
    messages
    you can use the get_logger() method to get the instance of the logger and use it directly
    :param messages: messages to be printed
    :param sep: default is " "
    :param end: default is "\n"
    :param flush: if True, flushes the output
    :param color: refer the colour class for available colors
    :param stack: Prints from where the log method was called
    :param log_level: possible values = "i", "w", "e", "c", "d", "info", "warning", "error", "critical", "debug"
    :param msg: message to be printed before the arguments
    :param full_stack: Prints the full stack trace from where the log method was called
    :return:
    """
    if color:
        color = color.upper()
    if stack:
        logger.log(log_level, *messages, msg=msg, color=color)
    elif full_stack:
        logger.stack(log_level, *messages, msg=msg, color=color)
    else:
        level = convert_log_level(log_level)
        if level >= logger.level():
            if color and hasattr(Colors, color):
                color_code = getattr(Colors, color)
                print(color_code, end="")
            else:
                color_code = logger.get_color()
            messages = [i if isinstance(i, str) else i.replace("\r", "\r" + color_code) for i in list(messages).copy()]
            logger.log(log_level, *messages, msg=msg, color=color, only_to_file=True)
            print(*messages, sep=sep, end="", flush=flush)
            if color and hasattr(Colors, color):
                print(Colors.RESET, end="")
            print("", end=end)


def info(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, msg="args : ", full_stack=False):
    """
    Wrapper for log log_level=info
    """
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="info", msg=msg,
        full_stack=full_stack)


def debug(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, msg="args : ", full_stack=False):
    """
    Wrapper for log log_level=debug
    """
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="debug", msg=msg,
        full_stack=full_stack)


def warning(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, msg="args : ", full_stack=False):
    """
        Wrapper for log log_level=warning
    """
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="warning", msg=msg,
        full_stack=full_stack)


def error(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, msg="args : ", full_stack=False):
    """
        Wrapper for log log_level=error
    """
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="error", msg=msg,
        full_stack=full_stack)


def critical(*messages, sep=" ", end="\n", flush=False, color=None, stack=False, msg="args : ", full_stack=False):
    """
    Wrapper for log log_level=critical
    """
    log(*messages, sep=sep, end=end, flush=flush, color=color, stack=stack, log_level="critical", msg=msg,
        full_stack=full_stack)
