# backend/logging_config.py
import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG = LOG_DIR / "app.log"
ERROR_LOG = LOG_DIR / "error.log"
DETECTOR_LOG = LOG_DIR / "detector.log"
API_LOG = LOG_DIR / "api.log"

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'format': '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'file_app': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': str(APP_LOG),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(ERROR_LOG),
            'maxBytes': 10485760,
            'backupCount': 5
        },
        'file_detector': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(DETECTOR_LOG),
            'maxBytes': 10485760,
            'backupCount': 5
        },
        'file_api': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',  # JSON format for API logs
            'filename': str(API_LOG),
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        'backend': {
            'level': 'DEBUG',
            'handlers': ['console', 'file_app'],
            'propagate': False
        },
        'backend.detector': {
            'level': 'DEBUG',
            'handlers': ['console', 'file_detector'],
            'propagate': False
        },
        'backend.api': {
            'level': 'INFO',
            'handlers': ['console', 'file_api'],
            'propagate': False
        },
        'backend.services': {
            'level': 'DEBUG',
            'handlers': ['console', 'file_app'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'sqlalchemy': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file_app']
    }
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log files location: {LOG_DIR}")
    return logger

# Quick test
if __name__ == "__main__":
    setup_logging()
    test_log = logging.getLogger(__name__)
    test_log.debug("Debug message test")
    test_log.info("Info message test")
    test_log.warning("Warning message test")
    test_log.error("Error message test")
    print(f"Logging test complete. Check {LOG_DIR}")