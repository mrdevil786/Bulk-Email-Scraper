import logging
from typing import Any

logger = logging.getLogger()

def validate_input(query: str, num_results: int) -> None:
    if not query.strip():
        logger.error("Search query cannot be empty.")
        exit(1)
    if num_results <= 0:
        logger.error("Number of results must be greater than zero.")
        exit(1)
