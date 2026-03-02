import asyncio
import logging
import chuscraper as cs

logging.basicConfig(level=logging.INFO)

async def debug_qs():
    async with await cs.start(headless=True) as browser:
        tab = await browser.get("https://neurofiq.in")
        print("Page loaded!")
        
        try:
            doc = await tab.send(cs.cdp.dom.get_document(-1, True))
            print(f"Doc node id: {doc.node_id}")
            node_id = await tab.send(cs.cdp.dom.query_selector(doc.node_id, "div"))
            print(f"Query selector via CDP node_id: {node_id}")
        except Exception as e:
            print(f"CDP Exception: {e}")

        # Now test the library's actual query_selector
        el = await tab.query_selector("div")
        print(f"Chuscraper Tab query_selector('div'): {el}")

        # Also let's try JS evaluation directly to see if document is present
        res, err = await tab.send(cs.cdp.runtime.evaluate("document.querySelector('div')"))
        print(f"JS runtime evaluate: res={res}, err={err}")
        if res and res.object_id:
            node_id = await tab.send(cs.cdp.dom.request_node(object_id=res.object_id))
            print(f"JS fallback derived node_id: {node_id}")
            # Try to resolve or describe it 
            described = await tab.send(cs.cdp.dom.describe_node(node_id=node_id))
            print(f"Described node: {described}")

if __name__ == "__main__":
    asyncio.run(debug_qs())
