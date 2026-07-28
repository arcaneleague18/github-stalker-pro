import logging
import sys
from typing import Optional
from config import settings

# ANSI color codes for terminal formatting
RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
}

class ColoredFormatter(logging.Formatter):
    """Custom logging formatter that adds color to log level names."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_color = COLORS.get(record.levelname, RESET)
        record.levelname = f"{log_color}{record.levelname:<8}{RESET}"
        return super().format(record)

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Create and return a configured logger instance with colored formatting.
    
    Args:
        name: The name of the logger, typically __name__.
        level: Optional log level override. Defaults to config LOG_LEVEL.
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicating handlers if logger already initialized
    if logger.hasHandlers():
        return logger
        
    log_level_str = level or settings.log_level
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate log messages
    logger.propagate = False
    
    return logger
