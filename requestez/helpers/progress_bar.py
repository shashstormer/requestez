import datetime
import sys
import time
from ..parsers import secondsToText


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

    def get_code(self, color):
        if color:
            color = color.upper()
        if color and hasattr(self, color):
            color_code = getattr(self, color)
        else:
            color_code = self.RESET
        return color_code


Colors = Colors()


class pbar:
    def __init__(self, total, prefix='', suffix='', decimals=1, length=50, fill='█', unit="it", color="reset"):
        self.recent_rates = []
        self.rate = "Unknown"
        self.average_rate = "Unknown"
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.unit = unit
        self.last_progress = 0
        self.start_time = datetime.datetime.now()
        self.total_time = datetime.datetime.now()
        self.last_time = datetime.datetime.now()
        self.recent_times = []
        self.color = color
        self.started = False
        self.update(0)

    def update(self, progress=None, color=None, plus=None, new_line=False, finish="\n"):
        """

        :param progress: to set it relative to 0 progress
        :param color: to set the color of the progress bar
        :param plus: to set it relative to last progress
        :param new_line: will keep the progress bar on the same line if set to False otherwise will print a new line each time it is updated
        :param finish: will print this at the end of the progress bar
        :return:
        """
        if color is None:
            color = self.color
        if progress is None:
            progress = self.last_progress + 1
        if plus is not None and type(plus) == int:
            progress = self.last_progress + plus
        color = Colors.get_code(color)
        self.last_progress = progress
        update_time = datetime.datetime.now()
        rate_time = update_time - self.last_time
        if self.started:
            self.recent_times.append(rate_time)
        if len(self.recent_times) > 10:
            self.recent_times = self.recent_times[-10:]
        sum_recent = sum([_.total_seconds() for _ in self.recent_times])
        rate = (len(self.recent_times) / sum_recent if sum_recent > 0 else 1) if len(self.recent_times) > 0 else 0
        self.total_time = (update_time - self.start_time)
        self.last_time = update_time
        elapsed_time = secondsToText(self.total_time.total_seconds())
        if elapsed_time == "00:00:00":
            elapsed_time = "Unknown"
        if self.total == 0:
            return
        percent = (progress / self.total) * 100
        self.rate = rate
        if self.started:
            self.recent_rates.append(rate)
        completed_length = int(self.length * progress // self.total)
        if completed_length > self.length:
            completed_length = int(self.length * self.total // self.total)
        progress_bar = self.fill * completed_length + '-' * (self.length - completed_length)
        progress_info = f'{percent:.{self.decimals}f}%'
        num_left = self.total - progress
        if num_left < 0:
            eta = "Error"
        else:
            eta = (num_left / rate) if rate else 0
            eta = f"{secondsToText(int(eta))}"
            if eta == "":
                eta = "00:00:00"
            if eta == "00:00:00":
                eta = "Unknown"
        avg_rate = (sum(self.recent_rates) if sum(self.recent_rates) > 0 else 1) / len(self.recent_rates) if len(
            self.recent_rates) else 1
        self.average_rate = avg_rate
        rate = float(f"{rate:.2f}")
        if rate == 0.00:
            rate = "Unknown"
        rate_info = f'Rate: {Colors.UNDERLINE}{rate}{Colors.RESET}{color} {self.unit}(s)/s'
        print(
            f'\r{color}{self.prefix} | {progress_info} |{progress_bar}| {progress}/{self.total} |{self.suffix + " | " if self.suffix else ""} | Elapsed Time: {Colors.UNDERLINE}{str(elapsed_time).split(".")[0]}{Colors.RESET}{color} | ETA: {Colors.UNDERLINE}{eta}{Colors.RESET}{color} | {rate_info}{Colors.RESET}',
            end="\n" if new_line else "", file=sys.stdout)
        if progress == self.total:
            print(f'\n{color}Average {self.unit}(s) per second: {avg_rate:.2f}{Colors.RESET}', end="", file=sys.stdout)
            print('', end=finish, file=sys.stdout)
        self.started = True


if __name__ == "__main__":
    progress_printer = pbar(total=10, prefix='Progress:', suffix='', length=35, color="green", unit="page")
    for i in range(11):
        time.sleep(0.5)  # Simulate some work
        progress_printer.update(i)
