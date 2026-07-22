"""Unit tests for logging configuration (``logging_setup``)."""

import logging

from opengate_gate_macro_fold import logging_setup


def test_configure_logging_is_idempotent() -> None:
    """Repeated configuration should not duplicate handlers."""
    # Arrange
    logger = logging.getLogger(logging_setup.LOGGER_NAME)
    original_handlers = list(logger.handlers)
    original_level = logger.level
    logger.handlers.clear()

    try:
        # Act
        logging_setup.configure_logging()
        logging_setup.configure_logging()

        # Assert
        assert len(logger.handlers) == 1
    finally:
        logger.handlers.clear()
        logger.handlers.extend(original_handlers)
        logger.setLevel(original_level)


def test_configure_logging_updates_level() -> None:
    """configure_logging should apply the requested log level."""
    # Arrange
    logger = logging.getLogger(logging_setup.LOGGER_NAME)
    original_level = logger.level

    try:
        # Act
        logging_setup.configure_logging(logging.DEBUG)

        # Assert
        assert logger.level == logging.DEBUG
    finally:
        logger.setLevel(original_level)


def test_get_logger_returns_named_logger() -> None:
    """get_logger should return a logger with the requested name."""
    # Arrange / Act
    logger = logging_setup.get_logger("example")

    # Assert
    assert logger.name == "example"
