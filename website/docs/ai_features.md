# AI-Ready Extraction

Chuscraper is designed to be the perfect companion for LLM-based data pipelines. Instead of dealing with messy HTML, Chuscraper provides "AI-Ready" formats like clean Markdown and normalized text, which significantly reduce token usage and improve LLM accuracy.

## Converting Pages to Markdown

Markdown is the preferred format for most LLMs (like GPT-4, Gemini, or Claude). Chuscraper uses a high-fidelity conversion engine to turn complex DOM trees into readable Markdown.

### Extracting the Entire Page

```python
import asyncio
import chuscraper as cs

async def main():
    async with await cs.start() as browser:
        tab = await browser.get("https://news.ycombinator.com")

        # Get full page as Markdown
        md_content = await tab.to_markdown()
        print(md_content)
```

### Extracting Specific Elements

You can also convert specific parts of a page, which is even more efficient for LLMs.

```python
# Select the main content div and convert only that
article = await tab.to_markdown(selector=".article-body")

# Or use an Element object directly
item = await tab.select(".product-card")
product_md = await item.to_markdown()
```

## Normalized Text Extraction

If you don't need Markdown formatting, `to_text()` provides a "clean" version of the page content, stripping away scripts, styles, and extra whitespace while maintaining the logical structure.

```python
clean_text = await tab.to_text()
# Returns just the human-readable text
```

## Structured Data (Adaptive Selectors)

While not "AI" in the sense of using a neural network, Chuscraper's **Adaptive Selectors** use a fingerprinting algorithm to ensure your extraction logic survives website redesigns—making your AI pipeline much more resilient.

```python
# 'adaptive=True' allows the locator to survive DOM changes
price_element = await tab.select(".price-tag", adaptive=True)
price = await price_element.text()
```

## Future: Native LLM Integration

The roadmap for Chuscraper includes a `schema` and `prompt` parameter for the Universal Crawler, allowing you to pass extraction instructions directly to an LLM provider:

```python
# Coming Soon
results = await crawler.run(
    prompt="Extract all product names and their prices",
    schema=ProductSchema
)
```

---

> [!TIP]
> **Token Saving Tip:** Always prefer `to_markdown(selector=...)` over a full page crawl. This can reduce your token consumption by up to 90%!
