import contextvars
import datetime
import logging
import os
import sys

trace_id_var = contextvars.ContextVar[str]('trace_id', default=None)


def setup_logging(log_dir, log_level=logging.INFO):
    """
    Set up logging to both stdout and a file using the root logger.
    The log file is created in the specified directory with the current date and time as its name.
    """

    os.makedirs(log_dir, exist_ok=True)
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    log_file = os.path.join(log_dir, f"log_{current_time}.log")
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers = []
    log_format = '%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)


def flush_logger():
    """Flush the logger to ensure all messages are written."""
    for handler in logging.getLogger().handlers:
        handler.flush()
    logging.info("Logger flushed.")
