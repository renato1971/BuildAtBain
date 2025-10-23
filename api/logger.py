"""
Centralized logging configuration for the AIS Masterclass Newsletter API.

This module provides a consistent logging interface across the entire application,
following best practices for production-ready logging.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LoggerConfig:
    """Configuration class for centralized logging."""
    
    # Log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    # Default format
    DEFAULT_FORMAT = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(funcName)s:%(lineno)d | %(message)s"
    )
    
    # Simple format for console
    SIMPLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
    
    # Date format
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    @staticmethod
    def get_log_directory() -> Path:
        """Get or create the logs directory."""
        project_root = Path(__file__).resolve().parents[1]
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        
        # Format the message
        result = super().format(record)
        
        # Reset levelname to original (for other handlers)
        record.levelname = levelname
        
        return result


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    use_colors: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.
    
    Args:
        name: Logger name (typically __name__ of the module)
        level: Logging level (default: INFO)
        log_to_file: Whether to log to file (default: True)
        use_colors: Whether to use colored console output (default: True)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> from api.logger import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if use_colors:
        console_formatter = ColoredFormatter(
            fmt=LoggerConfig.SIMPLE_FORMAT,
            datefmt=LoggerConfig.DATE_FORMAT
        )
    else:
        console_formatter = logging.Formatter(
            fmt=LoggerConfig.SIMPLE_FORMAT,
            datefmt=LoggerConfig.DATE_FORMAT
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        log_dir = LoggerConfig.get_log_directory()
        log_file = log_dir / f"api_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        file_formatter = logging.Formatter(
            fmt=LoggerConfig.DEFAULT_FORMAT,
            datefmt=LoggerConfig.DATE_FORMAT
        )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. Convenience function for getting loggers.
    
    Args:
        name: Logger name (default: calling module's __name__)
    
    Returns:
        Logger instance
    
    Example:
        >>> from api.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request")
    """
    if name is None:
        # Get the name of the calling module
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'api')
        else:
            name = 'api'
    
    return setup_logger(name)


# Create default logger for the API
api_logger = setup_logger('api')


def log_request(method: str, path: str, status_code: int, duration_ms: float):
    """
    Log HTTP request in a structured format.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    api_logger.info(
        f"{method} {path} - Status: {status_code} - Duration: {duration_ms:.2f}ms"
    )


def log_error(error: Exception, context: Optional[str] = None):
    """
    Log an error with optional context.
    
    Args:
        error: The exception that occurred
        context: Optional context information
    """
    message = f"Error: {str(error)}"
    if context:
        message = f"{context} - {message}"
    
    api_logger.error(message, exc_info=True)


def log_startup(service_name: str, version: str, port: int):
    """
    Log application startup information.
    
    Args:
        service_name: Name of the service
        version: Service version
        port: Port number
    """
    api_logger.info("=" * 60)
    api_logger.info(f"Starting {service_name} v{version}")
    api_logger.info(f"Port: {port}")
    api_logger.info(f"Log Level: {logging.getLevelName(api_logger.level)}")
    api_logger.info("=" * 60)


def log_shutdown(service_name: str):
    """
    Log application shutdown.
    
    Args:
        service_name: Name of the service
    """
    api_logger.info("=" * 60)
    api_logger.info(f"Shutting down {service_name}")
    api_logger.info("=" * 60)


# Export commonly used items
__all__ = [
    'setup_logger',
    'get_logger',
    'api_logger',
    'log_request',
    'log_error',
    'log_startup',
    'log_shutdown',
    'LoggerConfig'
]

