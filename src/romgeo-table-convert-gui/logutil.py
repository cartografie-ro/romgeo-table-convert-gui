import logging
import functools
import os
from pathlib import Path

# Setup logging once
LOG_DIR = Path(os.getenv('LOCALAPPDATA', os.path.expanduser("~\\AppData\\Local"))) / "romgeo"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "romgeo-table-convert-gui.log"


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("romgeo-table-convert-gui")

def log(message: str, level: str = "info", also_print: bool = False):
    if also_print:
        print (message)

    if level == "info":
        logger.info(message)
    elif level == "debug":
        logger.debug(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "critical":
        logger.critical(message)

def log_function(level: str = "info"):
    """Decorator that logs function calls, arguments, and return values."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args_repr = ", ".join(repr(a) for a in args)
            kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
            all_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
            log(f"{func.__name__}({all_args}) called", level)

            try:
                result = func(*args, **kwargs)
                log(f"{func.__name__} returned {result!r}", level)
                return result
            except Exception as e:
                logger.exception(f"{func.__name__} raised an error: {e}")
                raise
        return wrapper
    return decorator

def set_log_level(level: str):
    """Set the logging level globally for the app."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric)