import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import re

class JSONFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
            
        return json.dumps(self._redact_pii(log_data))
    
    def _redact_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sensitive_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
            (r'api[_-]?key["\s:=]+["\']?([a-zA-Z0-9_-]+)', 'api_key="[KEY_REDACTED]"'),
            (r'token["\s:=]+["\']?([a-zA-Z0-9_.-]+)', 'token="[TOKEN_REDACTED]"'),
            (r'password["\s:=]+["\']?([^\s"\']+)', 'password="[PASSWORD_REDACTED]"'),
        ]
        
        data_str = json.dumps(data)
        for pattern, replacement in sensitive_patterns:
            data_str = re.sub(pattern, replacement, data_str, flags=re.IGNORECASE)
        
        return json.loads(data_str)

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(
        logs_dir / f"{name}_{datetime.utcnow().strftime('%Y%m%d')}.log"
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger

def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs):
    extra_data = kwargs
    log_record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "(unknown file)",
        0,
        message,
        (),
        None,
    )
    log_record.extra_data = extra_data
    logger.handle(log_record)

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = setup_logger(name, level)
        self.name = name
    
    def debug(self, message: str, **kwargs):
        log_with_context(self.logger, "DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        log_with_context(self.logger, "INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        log_with_context(self.logger, "WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        log_with_context(self.logger, "ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        log_with_context(self.logger, "CRITICAL", message, **kwargs)

def get_logger(name: str, level: str = "INFO") -> StructuredLogger:
    return StructuredLogger(name, level)
