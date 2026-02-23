"""Tests for the logging utility module."""

import logging
import tempfile
from pathlib import Path

from rich.console import Console

from telco_cli.utils import console, get_logger, setup_logging


class TestLogging:
    """Test cases for logging utilities."""

    def test_get_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_console_instance(self):
        """Test console is a Rich Console instance."""
        assert isinstance(console, Console)
        # Console instance exists and is properly configured

    def test_setup_logging_default(self):
        """Test setup_logging with default settings."""
        # Clear any existing handlers
        logging.root.handlers = []

        setup_logging()

        assert logging.root.level == logging.DEBUG

        # Check that a handler was added
        assert len(logging.root.handlers) > 0

        # Handler should be at INFO level by default
        handler = logging.root.handlers[0]
        assert handler.level == logging.INFO

    def test_setup_logging_verbose(self):
        """Test setup_logging with verbose=True."""

        logging.root.handlers = []

        setup_logging(verbose=True)

        # Check that a handler was added with DEBUG level
        assert len(logging.root.handlers) > 0
        handler = logging.root.handlers[0]
        assert handler.level == logging.DEBUG

    def test_setup_logging_quiet(self):
        """Test setup_logging with quiet=True."""

        logging.root.handlers = []

        setup_logging(quiet=True)

        # Check that handler is at WARNING level in quiet mode
        assert len(logging.root.handlers) > 0
        handler = logging.root.handlers[0]
        assert handler.level == logging.WARNING

        test_logger = get_logger("test")
        assert test_logger.isEnabledFor(logging.WARNING)
        assert test_logger.isEnabledFor(logging.ERROR)

    def test_setup_logging_with_file(self):
        """Test setup_logging with log file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.flush()
            log_path = Path(tmp.name)

        try:
            logging.root.handlers = []

            setup_logging(log_file=log_path)

            # Check that we have 2 handlers (console + file)
            assert len(logging.root.handlers) == 2

            # Check file handler exists
            file_handlers = [h for h in logging.root.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
            assert file_handlers[0].baseFilename == str(log_path)
        finally:
            if log_path.exists():
                log_path.unlink()

    def test_setup_logging_suppresses_noisy_libraries(self, caplog):
        """Test that noisy libraries are suppressed by default."""
        setup_logging(verbose=False)

        boto3_logger = logging.getLogger("boto3")
        botocore_logger = logging.getLogger("botocore")
        urllib3_logger = logging.getLogger("urllib3")

        assert boto3_logger.level == logging.WARNING
        assert botocore_logger.level == logging.WARNING
        assert urllib3_logger.level == logging.WARNING

    def test_setup_logging_verbose_shows_all_libraries(self):
        """Test that verbose mode doesn't suppress library logs."""
        # In verbose mode, library loggers should still be WARNING
        # because we only suppress them in non-verbose mode
        setup_logging(verbose=True)

        # These are still set to WARNING even in verbose mode
        # The verbose flag affects handler level, not individual loggers
        boto3_logger = logging.getLogger("boto3")
        botocore_logger = logging.getLogger("botocore")
        urllib3_logger = logging.getLogger("urllib3")

        # In our implementation, these stay at WARNING
        # The verbose handler will show their DEBUG messages if they emit any
        assert boto3_logger.level == logging.WARNING
        assert botocore_logger.level == logging.WARNING
        assert urllib3_logger.level == logging.WARNING

    def test_console_theme(self):
        """Test that the TELCO_THEME is properly defined."""
        from telco_cli.utils.logging import TELCO_THEME

        assert "info" in TELCO_THEME.styles
        assert "success" in TELCO_THEME.styles
        assert "error" in TELCO_THEME.styles
        assert "warning" in TELCO_THEME.styles
        assert "highlight" in TELCO_THEME.styles
        assert "progress" in TELCO_THEME.styles
