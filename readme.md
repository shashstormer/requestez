# RequestEZ

RequestEZ is a Python library that simplifies web scraping, provides basic parsing utilities, AES encryption/decryption, and some useful logging utilities.

## Installation

You can install RequestEZ using `pip`. Make sure you have Python 3.9 or later installed.

```bash
pip install requestez
```
# Usage
### 1. Basic Web Scraping:
RequestEZ provides a simple interface for making HTTP requests. You can create a session and use it to fetch web pages. 
```python
from requestez import Session
session = Session()
response: str = session.get("https://example.com")  # refer to inline documentation for more options
print(response)
```
### 2. AES Encryption/Decryption:
You can use RequestEZ to perform AES encryption and decryption of data.

```python
from requestez.encryption import aes_enc, aes_dec

key: bytes = b"your_32_byte_secret_key"
iv: bytes = b"your_16_byte_initialization_vector"
data: str = "your_data_to_encrypt"

encrypted_data: str = aes_enc(key, iv, data)
decrypted_data: str = aes_dec(key, iv, encrypted_data)

print("Encrypted:", encrypted_data)
print("Decrypted:", decrypted_data)

# you need to do from requestez.encryption.unpack import PACKER to find and decrypt p.a.c.k.e.r. encrypted data
# read code to find out more
```
### 3. Parsing Utilities:
RequestEZ provides some basic parsing utilities. You can use them to parse HTML, JSON, and XML data.

```python
from requestez.parsers import html, load
html_data = "<html><body><h1>Hello World</h1></body></html>"
json_data = '{"name": "John Doe", "age": 30}'

# Parse HTML data
parsed_html = html(html_data) # returns a BeautifulSoup object

# Parse JSON data
parsed_json = load(json_data) # returns a dict if valid json otherwise returns the string itsef
```
 There are other parsing utilities available as well. Please read the inline documentation for those.
 some of them are 
 - `m3u8_master` for parsing a M3U8 master playlist
 - `m3u8` for parsing M3U8 data > returns `m3u8.parse(playlist)`
 - `reg_replace` basically `re.sub` just don't have to import re
 - `secondsToRead` for converting seconds to human-readable format like `x day(s) x hour(s)...`
 - `secondsToTime` for converting seconds to `(DD):HH:MM:SS` format
 - `stringify` for converting a dict to a string with optional escaping
 - `load` for loading JSON data which can handle escaped json but is iterative to handle escaped json

### 4. Logging Utilities:
RequestEZ provides some useful and colorful logging utilities. You can use them to log data to a file or to the console.

```python
# it works similar to the logging module but with some extra features
# Logging to a file is now supported
# Color compatibility depends on the terminal
# Works on windows cmd, powershell, and linux terminal (tested) 
# others not tested
import time
from requestez.helpers import log, set_log_level, pbar, get_logger, critical
set_log_level("debug")
log("Hello World", color="green" ,log_level="debug") # logs hello world
set_log_level("info") # sets log level to debug
get_logger().enable_file_logging(json_path="test.json") # enables file logging to that file, each line in the file is a json object
log("Hello World", color="green" ,log_level="info") # logs red hello world to console
log("Hello World", color="red" ,log_level="debug") # logs nothing to console
critical("This is a critical message") # logs red hello world to console with CRITICAL level
# Refer to inline documentation for more options


progress_printer = pbar(total=10, prefix='Progress:', suffix='', length=35, color="green", unit="seconds")
for i in range(11):
    time.sleep(1)  # Simulate some work
    progress_printer.update(i)
    # it is equivalent to 
    # progress_printer.update(plus=1) -> this is done by default in the tqdm module
# Refer to inline documentation for more options
```
#### the order of level priority is as follows:
 
- priority level (alias)
1. CRITICAL (c)
2. ERROR (e)
3. WARNING (w)
4. INFO (i)
5. DEBUG (d)

