# Quickstart

## Installation

To install, simply use `pip` (or your favorite package manager):

```sh
pip install chuscraper
# or uv add chuscraper, poetry add chuscraper, etc.
```

Open a browser, navigate to a page, and scrape the content:

```python
import asyncio
import chuscraper as zd

async def main():
    # DIRECT START (No Config object needed)
    async with await zd.start(headless=False, stealth=True) as browser:
        
        # New: goto() alias and title() method
        await browser.goto('https://example.com')
        
        print(f"Bhai, Title hai: {await browser.main_tab.title()}")

        # Extract text in one line
        header = await browser.main_tab.select_text("h1")
        print(f"Header: {header}")

if __name__ == '__main__':
    asyncio.run(main())
```

## More complete example

```python
import asyncio
import chuscraper as zd

async def main():
    async with await zd.start(stealth=True) as browser:
        # Easy navigation
        await browser.goto('https://github.com')
        
        # Tab level control
        page = browser.main_tab
        await page.goto('https://google.com', new_tab=True)
        
        for p in browser.tabs:
            title = await p.title()
            print(f"Checking Tab: {title}")
            await p.scroll_down(200)
            await p.close()

if __name__ == '__main__':
    asyncio.run(main())
```

I'll leave out the async boilerplate here

```python
import chuscraper as cs

browser = await cs.start(
    headless=False,
    user_data_dir="/path/to/existing/profile",  # by specifying it, it won't be automatically cleaned up when finished
    browser_executable_path="/path/to/some/other/browser",
    browser_args=['--some-browser-arg=true', '--some-other-option'],
    lang="en-US"   # this could set iso-language-code in navigator, not recommended to change
)
tab = await browser.get('https://somewebsite.com')
```

## Alternative custom options

I'll leave out the async boilerplate here

```python
import chuscraper as cs

config = cs.Config()
config.headless = False
config.user_data_dir="/path/to/existing/profile",  # by specifying it, it won't be automatically cleaned up when finished
config.browser_executable_path="/path/to/some/other/browser",
config.browser_args=['--some-browser-arg=true', '--some-other-option'],
config.lang="en-US"   # this could set iso-language-code in navigator, not recommended to change
```

On Windows, we recommend using `WindowsSelectorEventLoopPolicy` for better compatibility with asyncio:

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

A more concrete example, which can be found in the ./example/ folder,
shows a script for uploading an image to imgur.

```python
import asyncio
from pathlib import Path
import chuscraper as cs

# interesting, this is a typical site which runs completely on javascript, and that causes
# this script to be faster than the js can present the elements. This may be one of the downsides
# of this fast beast. You have to carefully consider timing.
DELAY = 2

async def main():
    browser = await cs.start()
    tab = await browser.get("https://imgur.com")

    # now we first need an image to upload, lets make a screenshot of the project page
    save_path = Path("screenshot.jpg").resolve()
    # create new tab with the project page
    temp_tab = await browser.get(
        "https://github.com/ultrafunkamsterdam/undetected-chromedriver", new_tab=True
    )

    # wait page to load
    await temp_tab
    # save the screenshot to the previously declared path of screenshot.jpg (which is just current directory)
    await temp_tab.save_screenshot(save_path)
    # done, discard the temp_tab
    await temp_tab.close()

    # accept goddamn cookies
    # the best_match flag will filter the best match from
    # matching elements containing "consent" and takes the
    # one having most similar text length
    consent = await tab.find("Consent", best_match=True)
    await consent.click()

    # shortcut
    await (await tab.find("new post", best_match=True)).click()

    file_input = await tab.select("input[type=file]")
    await file_input.send_file(save_path)
    # since file upload takes a while , the next buttons are not available yet

    await tab.wait(DELAY)

    # wait until the grab link becomes clickable, by waiting for the toast message
    await tab.select(".Toast-message--check")

    # this one is tricky. we are trying to find a element by text content
    # usually. the text node itself is not needed, but it's enclosing element.
    # in this case however, the text is NOT a text node, but an "placeholder" attribute of a span element.
    # so for this one, we use the flag return_enclosing_element and set it to False
    title_field = await tab.find("give your post a unique title", best_match=True)
    print(title_field)
    await title_field.send_keys("undetected chuscraper")

    grab_link = await tab.find("grab link", best_match=True)
    await grab_link.click()

    # there is a delay for the link sharing popup.
    # let's pause for a sec
    await tab.wait(DELAY)

    # get inputs of which the value starts with http
    input_thing = await tab.select("input[value^=https]")

    my_link = input_thing.attrs.value

    print(my_link)
    await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
```
