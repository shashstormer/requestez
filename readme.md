# RequestEZ

RequestEZ is a Python library designed to simplify web scraping, provide robust parsing utilities, offer easy-to-use AES encryption/decryption, and feature a powerful, flexible logging system.

## Installation

You can install RequestEZ using `pip`. Make sure you have Python 3.9 or later installed.

```bash
pip install requestez
```

## Usage

### 1. Web Scraping with `Session`

RequestEZ provides a `Session` class that wraps `requests.Session` with additional features like automatic header management, anti-bot sleeping, and m3u8 downloading.

```python
from requestez import Session

# Initialize session (human_browsing=True adds random delays to mimic human behavior)
session = Session(human_browsing=True)

# Basic GET request
response = session.get("https://example.com")
print(response)

# POST request
session.post("https://example.com/api", body={"key": "value"})

# Download file
session.download("https://example.com/file.zip", "file.zip")

# Download M3U8 (HLS) stream
# This downloads segments and optionally joins them (requires moviepy)
session.download_m3u8_as_mp4("https://example.com/video.m3u8", "video.mp4")
```

### 2. Logging Utilities

RequestEZ features a powerful logging system that integrates with Python's standard `logging` module while providing a simple, colorful API.

```python
from requestez.helpers import log, info, debug, warning, error, critical, set_log_level, get_logger

# Set log level (default is INFO)
set_log_level("debug")

# Basic logging (prints to console with color)
info("This is an info message")
debug("This is a debug message")
error("Something went wrong!", color="red")

# The 'log' helper is versatile:
# 1. Like print(): Raw output, supports end, flush, color
log("Loading...", end="", flush=True, color="yellow")
log("Done!", color="green")

# 2. Like logger: structured output with stack trace info
log("System status normal", stack=True) 

# File Logging
# Enable logging to file (text and/or JSON)
get_logger().enable_file_logging(log_path="app.log", json_path="app.json")

info("This goes to console AND file")
log("This goes to file ONLY (raw print to console)", stack=False)

# Disable file logging
get_logger().disable_file_logging()
```

**Log Levels:**
1.  CRITICAL (c)
2.  ERROR (e)
3.  WARNING (w)
4.  INFO (i)
5.  DEBUG (d)

### 3. Progress Bar

A clean, customizable progress bar for tracking operations.

```python
import time
from requestez.helpers import pbar

total_items = 50
# Initialize
pb = pbar(total_items, prefix='Processing:', suffix='Complete', length=30, color="cyan")

for i in range(total_items):
    time.sleep(0.1)
    # Update progress
    pb.update() 
    # Or update with specific value: pb.update(i)
    # Or increment: pb.update(plus=1)
```

### 4. Parsing Utilities

Utilities to parse HTML, JSON, XML, and more.

```python
from requestez.parsers import html, load, stringify, seconds_to_text, merge

# HTML Parsing (returns BeautifulSoup object)
soup = html("<html><body><h1>Hi</h1></body></html>")

# JSON Loading (handles escaped strings and nested JSON strings)
data = load('{"key": "value"}')

# Merge Data Structures
list1 = [1, 2]
list2 = [3, 4]
merged = merge(list1, list2) # [1, 2, 3, 4]

# Time Formatting
print(seconds_to_text(3665)) # 01:01:05
```

### 5. AES Encryption/Decryption

Simple wrapper for AES encryption.

```python
from requestez.encryption import aes_enc, aes_dec

key = b"your_32_byte_secret_key_12345678"
iv = b"your_16_byte_iv_"
data = "Secret Message"

encrypted = aes_enc(key, iv, data)
decrypted = aes_dec(key, iv, encrypted)
```

## Advanced Features

-   **M3U8 Parsing**: `requestez.parsers.m3u8` and `m3u8_master` for handling HLS playlists.
-   **Regex Helpers**: `requestez.parsers.regex` for quick extraction.
-   **JavaScript Extraction**: `requestez.parsers.get_val_js_var` to extract variables from inline JS in HTML.
