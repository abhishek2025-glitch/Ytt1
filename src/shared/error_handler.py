import functools
import traceback
from typing import Any, Callable, Optional, Type, Union
from .logger import get_logger

logger = get_logger(__name__)

class ViralosError(Exception):
    pass

class SenseLayerError(ViralosError):
    pass

class ValidationError(ViralosError):
    pass

class ScoringError(ViralosError):
    pass

class GenerationError(ViralosError):
    pass

class ProductionError(ViralosError):
    pass

class PublishingError(ViralosError):
    pass

class QuotaExceededError(ViralosError):
    pass

class RateLimitError(ViralosError):
    pass

def handle_errors(
    fallback_value: Any = None,
    reraise: bool = False,
    exception_types: Optional[tuple] = None,
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if exception_types and not isinstance(e, exception_types):
                    raise
                
                logger.error(
                    f"Error in {func.__name__}: {str(e)}",
                    function=func.__name__,
                    error_type=type(e).__name__,
                    traceback=traceback.format_exc(),
                    args=str(args)[:200],
                    kwargs=str(kwargs)[:200],
                )
                
                if reraise:
                    raise
                    
                return fallback_value
        
        return wrapper
    return decorator

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exponential: bool = True,
    exception_types: Optional[tuple] = None,
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if exception_types and not isinstance(e, exception_types):
                        raise
                    
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt if exponential else 1)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s",
                            function=func.__name__,
                            attempt=attempt + 1,
                            delay=delay,
                            error=str(e),
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All retries exhausted for {func.__name__}",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e),
                        )
            
            raise last_exception
        
        return wrapper
    return decorator

class ErrorContext:
    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
    
    def __enter__(self):
        logger.debug(f"Starting: {self.operation}", **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"Failed: {self.operation}",
                error_type=exc_type.__name__,
                error=str(exc_val),
                **self.context,
            )
            return False
        
        logger.debug(f"Completed: {self.operation}", **self.context)
        return True
