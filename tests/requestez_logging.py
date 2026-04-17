import unittest
import os
import tempfile
from requestez.helpers import log, set_log_level, get_logger, info, debug, critical, error, warning


class TestLogger(unittest.TestCase):
    def setUp(self):
        # Create a temporary file to log into
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.log_file = self.temp_log.name
        self.temp_log.close()
        self.logger = get_logger()
        self.logger.enable_file_logging(json_path=self.log_file)

    def tearDown(self):
        self.logger.disable_file_logging()
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def read_log(self):
        with open(self.log_file, "r") as f:
            return f.read()

    def test_logger_instance(self):
        self.assertIsNotNone(self.logger)

    def test_logger_level_setting(self):
        current_level = self.logger.level()
        set_log_level("DEBUG")
        self.assertEqual(self.logger.level(), get_logger().level())
        set_log_level(current_level)  # Reset

    def test_file_logging_enabled(self):
        set_log_level("DEBUG")
        log("Test debug message")
        content = self.read_log()
        self.assertIn("Test debug message", content)

    def test_file_logging_disabled(self):
        set_log_level("DEBUG")
        log("Initial log before disable")
        self.logger.disable_file_logging()
        log("Test no file log message")
        content = self.read_log()
        self.assertNotIn("Test no file log message", content)

    def test_log_levels(self):
        set_log_level("INFO")
        info("Test info message")
        debug("Test debug message")  # Should not be logged
        critical("Test critical message")
        error("Test error message")
        warning("Test warning message")

        content = self.read_log()
        self.assertIn("Test info message", content)
        self.assertNotIn("Test debug message", content)
        self.assertIn("Test critical message", content)
        self.assertIn("Test error message", content)
        self.assertIn("Test warning message", content)

    def test_log_different_types(self):
        set_log_level("i")
        info([1, 2, 3])
        info(["a", "b", "c"])
        info(200)
        info("Test info message")
        info({"key": "value"})
        info(None)
        info(True)
        info(3.14)
        info((1, 2, 3))
        info({1, 2, 3})
        info(bytearray(b"byte"))
        info(bytes("byte", "utf-8"))
        info(range(5))


if __name__ == "__main__":
    unittest.main()
