"""Logging utilities.

This module re-exports from the canonical logging_config module for backwards compatibility.
Use storm_logos.logging_config directly for full functionality.
"""

# Re-export from canonical logging configuration
from storm_logos.logging_config import setup_logging, get_logger, log_request

__all__ = ['setup_logging', 'get_logger', 'log_request']
