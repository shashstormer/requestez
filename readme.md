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

### 2. Asynchronous Scraping with `asynchronous.Session`

For high-performance asynchronous tasks, RequestEZ provides an async session powered by `httpx`. It maintains a similar browser-like context (Referer tracking) and supports state persistence.

```python
import asyncio
from requestez.asynchronous import Session

async def main():
    # Use context manager for automatic client cleanup
    async with Session() as session:
        # Standard GET/POST
        status, headers, body = await session.get("https://httpbin.org/get")
        print(f"Async GET Status: {status}")

        # Browser-like navigation (sets Referer, updates internal current URL)
        await session.navigate("https://httpbin.org/relative-redirect/1")

        # Save/Load state (Cookies + current URL)
        state = await session.save_data()
        
        async with Session() as session2:
            await session2.load_data(state)
            # session2 now has the cookies and referer from session1
            await session2.get("https://httpbin.org/cookies")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Advanced CURL Scraping with `kurl` (Impersonation)

When a website blocks standard `requests` or `httpx` due to TLS/JA3 fingerprinting, use the `kurl` module. It uses `curl_cffi` to impersonate real browsers (Chrome, Edge, Safari).

#### Synchronous kurl
```python
from requestez import kurl

# Impersonate Chrome 124 (Default)
session = kurl.Session(impersonate="chrome124")
resp = session.get("https://tls.browserleaks.com/json")
print(resp)

# Supports all standard Session features:
session.download_m3u8_as_mp4("url", "video.mp4")
```

#### Asynchronous kurl
```python
import asyncio
from requestez import kurl

async def main():
    async with kurl.AsyncSession(impersonate="chrome124") as session:
        status, headers, body = await session.get("https://httpbin.org/get")
        print(f"kurl Async Status: {status}")
        
        # State persistence works identically
        state = await session.save_data()
        await session.load_data(state)

asyncio.run(main())
```

### 4. Logging Utilities

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

### 5. Progress Bar

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

### 6. Parsing Utilities

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

### 7. AES Encryption/Decryption

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
