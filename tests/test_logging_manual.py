import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from requestez.helpers import log, set_log_level, get_logger, info, debug, warning, error, critical

def test_logging():
    print("Testing Console Logging:")
    set_log_level("debug")
    log("This is a generic log message", color="green")
    info("This is an info message")
    debug("This is a debug message")
    warning("This is a warning message")
    error("This is an error message")
    critical("This is a critical message")
    
    print("\nTesting File Logging:")
    log_file = "test_log.txt"
    json_log_file = "test_log.json"
    
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(json_log_file):
        os.remove(json_log_file)
        
    get_logger().enable_file_logging(log_path=log_file, json_path=json_log_file)
    
    info("This message should be in the file")
    error("This error should also be in the file")
    
    get_logger().disable_file_logging()
    
    print(f"\nCheck {log_file} and {json_log_file} for content.")
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            print(f"\nContent of {log_file}:")
            print(f.read())
            
    if os.path.exists(json_log_file):
        with open(json_log_file, 'r') as f:
            print(f"\nContent of {json_log_file}:")
            print(f.read())

    print("\nTesting Restored Behavior:")
    log("This should not have a newline", end="")
    log("... and this continues it.")
    
    log("This should be red", color="red")
    
    print("\nTesting Stack Trace (Formatted):")
    log("This should have stack trace info", stack=True)
    
    print("\nTesting File Logging with Restored Behavior:")
    log_file = "test_log_restored.txt"
    if os.path.exists(log_file):
        os.remove(log_file)
        
    get_logger().enable_file_logging(log_path=log_file)
    log("This should be in file but printed raw to console")
    log("This should be in file and formatted in console", stack=True)
    get_logger().disable_file_logging()
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            print(f"\nContent of {log_file}:")
            print(f.read())

if __name__ == "__main__":
    test_logging()
