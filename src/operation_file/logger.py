from colorama import Fore, Style
from typing import Callable
import time
from datetime import datetime

class Logger:
    def __init__(self, debug_callback: Callable = None):
        """
        Initialize logger with optional debug callback
        :param debug_callback: Optional callback function for debug messages
        """
        self.debug_callback = debug_callback
        self.start_time = time.time()
    
    def add(self, message: str):
        """
        Log a success message
        :param message: Message to log
        """
        print(f'{Fore.GREEN}[+]{Style.RESET_ALL} {message}')
        if self.debug_callback:
            self.debug_callback(message, "INFO")
    
    def error(self, message: str):
        """
        Log an error message
        :param message: Error message to log
        """
        print(f'{Fore.RED}[ERROR]{Style.RESET_ALL} {message}')
        if self.debug_callback:
            self.debug_callback(message, "ERROR")
    
    def warning(self, message: str):
        """
        Log a warning message
        :param message: Warning message to log
        """
        print(f'{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}')
        if self.debug_callback:
            self.debug_callback(message, "WARNING")
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since logger initialization
        :return: Elapsed time in seconds
        """
        return time.time() - self.start_time