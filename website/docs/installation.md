# Installation

Getting Chuscraper up and running is straightforward.

## Requirements

- **Python**: 3.8 or higher
- **Google Chrome**: Recent version installed on your system (Chuscraper will find it automatically).
- **OS**: Windows, macOS, or Linux.

## Install via PIP

Run the following command in your terminal:

```bash
pip install chuscraper
```

Or if you are using `uv` or `poetry`:

```bash
uv add chuscraper
# or
poetry add chuscraper
```

## Verify Installation

To verify that the installation was successful, you can run a quick check in python:

```python
import chuscraper
print(chuscraper.__file__)
```

## Troubleshooting

### Windows `asyncio` Issue
On Windows, you might encounter `RuntimeError: Event loop is closed` or similar asyncio issues. We recommend setting the event loop policy:

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Chrome Not Found
If Chuscraper cannot find your Chrome installation, you can specify the path manually in the `start` function:

```python
browser = await chuscraper.start(
    browser_executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
)
```
