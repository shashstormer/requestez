import sys
import time
import datetime
from typing import Optional, Union
from ..parsers import secondsToText
from .logger import Colors

class pbar:
    def __init__(self, total: int, prefix: str = '', suffix: str = '', decimals: int = 1, length: int = 50, fill: str = '█', unit: str = "it", color: str = "reset"):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.unit = unit
        self.color_name = color
        self.color_code = Colors.get_color(color)
        
        self.iteration = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.started = False
        
        # Rate calculation
        self.recent_rates = []
        self.max_recent_rates = 10

        # Initial print
        self._print_progress(0)

    def update(self, progress: Optional[int] = None, plus: Optional[int] = None, color: Optional[str] = None, new_line: bool = False, finish: str = "\n"):
        """
        Update the progress bar.
        
        :param progress: Absolute progress value.
        :param plus: Increment progress by this amount.
        :param color: Override color for this update.
        :param new_line: If True, print a newline after the bar (useful for logging).
        :param finish: String to print when progress is complete (default newline).
        """
        if not self.started:
            self.start_time = time.time()
            self.started = True

        if progress is not None:
            self.iteration = progress
        elif plus is not None:
            self.iteration += plus
        else:
            self.iteration += 1

        current_color_code = self.color_code
        if color:
            current_color_code = Colors.get_color(color)

        self._print_progress(self.iteration, color_code=current_color_code, new_line=new_line)

        if self.iteration >= self.total:
            self._finish(finish)

    def _print_progress(self, iteration, color_code=None, new_line=False):
        if color_code is None:
            color_code = self.color_code

        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (iteration / float(self.total)))
        filled_length = int(self.length * iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)

        # Time calculations
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # Rate calculation
        if iteration > 0 and elapsed_time > 0:
            rate = iteration / elapsed_time
        else:
            rate = 0
            
        # ETA calculation
        remaining = self.total - iteration
        if rate > 0:
            eta_seconds = remaining / rate
            eta = secondsToText(int(eta_seconds))
        else:
            eta = "Unknown"
            
        elapsed_str = secondsToText(int(elapsed_time))
        
        # Rate string
        rate_str = f"{rate:.2f} {self.unit}/s"

        # Construct the line
        # Format: Prefix | Percent% |Bar| Iteration/Total | Suffix | Elapsed | ETA | Rate
        line = f"\r{color_code}{self.prefix} | {percent}% |{bar}| {iteration}/{self.total} | {self.suffix} | Elapsed: {elapsed_str} | ETA: {eta} | {rate_str}{Colors.RESET}"
        
        end = "\n" if new_line else ""
        sys.stdout.write(line + end)
        sys.stdout.flush()

    def _finish(self, finish_str):
        sys.stdout.write(finish_str)
        sys.stdout.flush()

if __name__ == "__main__":
    # Test
    total_items = 50
    pb = pbar(total_items, prefix='Progress:', suffix='Complete', length=30, color="green")
    for i in range(total_items):
        time.sleep(0.1)
        pb.update()
