import pytest

from llmcompressor import LoggerConfig, configure_logger, logger


@pytest.fixture(autouse=True)
def reset_logger():
    # Ensure logger is reset before each test
    logger.remove()
    yield
    logger.remove()


def test_default_logger_settings(capsys):
    # Default settings should log to console with INFO level and no file logging
    logger.info("Info message")
    logger.debug("Debug message")

    captured = capsys.readouterr()
    assert "Info message" in captured.out
    assert "Debug message" not in captured.out


def test_configure_logger_console_settings(capsys):
    # Test configuring the logger to change console log level
    config = LoggerConfig(console_log_level="DEBUG")
    configure_logger(config=config)
    logger.info("Info message")
    logger.debug("Debug message")

    captured = capsys.readouterr()
    assert "Info message" in captured.out
    assert "Debug message" in captured.out


def test_configure_logger_file_settings(tmp_path):
    # Test configuring the logger to log to a file
    log_file = tmp_path / "test.log"
    config = LoggerConfig(log_file=str(log_file), log_file_level="DEBUG")
    configure_logger(config=config)
    logger.info("Info message")
    logger.debug("Debug message")

    with open(log_file, "r") as f:
        log_contents = f.read()
    assert "Info message" in log_contents
    assert "Debug message" in log_contents


def test_configure_logger_console_and_file(capsys, tmp_path):
    # Test configuring the logger to change both console and file settings
    log_file = tmp_path / "test.log"
    config = LoggerConfig(
        console_log_level="ERROR", log_file=str(log_file), log_file_level="INFO"
    )
    configure_logger(config=config)
    logger.info("Info message")
    logger.error("Error message")

    captured = capsys.readouterr()
    assert "Info message" not in captured.out
    assert "Error message" in captured.out

    with open(log_file, "r") as f:
        log_contents = f.read()
    assert "Info message" in log_contents
    assert "Error message" in log_contents


def test_environment_variable_override(monkeypatch, capsys, tmp_path):
    # Test environment variables override settings
    monkeypatch.setenv("GUIDE_LLM_LOG_LEVEL", "ERROR")
    monkeypatch.setenv("GUIDE_LLM_LOG_FILE", str(tmp_path / "env_test.log"))
    monkeypatch.setenv("GUIDE_LLM_LOG_FILE_LEVEL", "DEBUG")

    configure_logger(config=LoggerConfig())
    logger.info("Info message")
    logger.error("Error message")
    logger.debug("Debug message")

    captured = capsys.readouterr()
    assert "Info message" not in captured.out
    assert "Error message" in captured.out
    assert "Debug message" not in captured.out

    with open(tmp_path / "env_test.log", "r") as f:
        log_contents = f.read()
    assert "Info message" in log_contents
    assert "Error message" in log_contents
    assert "Debug message" in log_contents


def test_environment_variable_disable_logging(monkeypatch, capsys):
    # Test environment variable to disable logging
    monkeypatch.setenv("GUIDE_LLM_LOG_DISABLED", "true")

    configure_logger(config=LoggerConfig())
    logger.info("Info message")
    logger.error("Error message")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
