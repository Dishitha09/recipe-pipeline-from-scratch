import logging
import os

os.makedirs(
    "logs",
    exist_ok=True,
)

# Root logger
logging.basicConfig(
    level=logging.WARNING
)

# Project logger
logger = logging.getLogger(
    "recipe_pipeline"
)

logger.setLevel(
    logging.INFO
)

# Prevent duplicate logs
logger.propagate = False

# File handler
file_handler = logging.FileHandler(
    "logs/resolver.log",
    encoding="utf-8",
)

file_handler.setLevel(
    logging.INFO
)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

file_handler.setFormatter(
    formatter
)

# Avoid duplicate handlers
if not logger.handlers:
    logger.addHandler(
        file_handler
    )