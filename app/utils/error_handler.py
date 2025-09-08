"""
Basic error handling utilities
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Callable, Any
import functools

class SimpleProgressTracker:
    """Lightweight progress tracker for operations without UI"""
    
    def __init__(self, title: str = "Processing"):
        self.title = title
        self.start_time = None
        self.current = 0
        self.total = 100
    
    def start(self, total: int = 100):
        """Start progress tracking"""
        self.start_time = datetime.now()
        self.total = total
        self.current = 0
        print(f"{self.title}: Starting...")
    
    def update(self, current: int, status: str = None):
        """Update progress"""
        self.current = current
        percentage = (current / self.total * 100) if self.total > 0 else 0
        
        if status:
            print(f"{self.title}: {status} ({percentage:.1f}%)")
        else:
            print(f"{self.title}: {percentage:.1f}% complete")
    
    def finish(self, status: str = "Complete"):
        """Finish progress tracking"""
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        print(f"{self.title}: {status} in {elapsed:.1f}s")

class BasicErrorHandler:
    """Simple error handling"""
    
    def __init__(self, logger_name: str = "KulaNLP"):
        self.logger_name = logger_name
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with context"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        print(f"ERROR - {error_msg}")
    
    def log_warning(self, message: str, context: str = ""):
        """Log warning message"""
        warning_msg = f"{context}: {message}" if context else message
        print(f"WARNING - {warning_msg}")
    
    def log_info(self, message: str, context: str = ""):
        """Log info message"""
        info_msg = f"{context}: {message}" if context else message
        print(f"INFO - {info_msg}")

def safe_execute(operation_name: str, show_errors: bool = True):
    """Decorator for safe execution with basic error handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            error_handler = BasicErrorHandler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(e, operation_name)
                if show_errors:
                    # Try to show error to user if possible
                    try:
                        # If first argument has a notify method (Textual screen)
                        if hasattr(args[0], 'notify'):
                            args[0].notify(f"{operation_name} failed: {str(e)}", severity="error")
                        else:
                            print(f"ERROR in {operation_name}: {str(e)}")
                    except:
                        print(f"ERROR in {operation_name}: {str(e)}")
                return None
        return wrapper
    return decorator

# Global error handler instance
error_handler = BasicErrorHandler()
