from requestez.helpers import log, set_log_level, get_logger
import os


def test_log():
    # Test if the logger is set up correctly
    logger = get_logger()
    assert logger is not None

    # Test if the logger has the correct level
    assert logger.level() == get_logger().level()
    log_file = "test_log.log"

    # Test if the logger writes to the file
    get_logger().enable_file_logging(json_path=log_file)
    set_log_level("DEBUG")
    log("Test debug message")
    assert os.path.exists(log_file)

    with open(log_file, "r") as f:
        log_content = f.read()
        assert "Test debug message" in log_content

    # Test if the logger can be disabled
    get_logger().disable_file_logging()
    log("Test no file log message", full_stack=True)
    with open(log_file, "r") as f:
        log_content = f.read()
        assert "Test no file log message" not in log_content
    os.remove(log_file)


if __name__ == "__main__":
    test_log()
    print("All tests passed!")
