# AI Features

Chuscraper includes a "Pilot" agent that can navigate websites using LLMs (Large Language Models).

## The AI Pilot

The `AIPilot` takes a high-level goal (e.g., "Login with user X") and autonomously executes clicks and keystrokes to achieve it.

### Setup

You need an AI Provider (currently supports Gemini).

```python
from chuscraper.ai.agent import AIPilot
from chuscraper.ai.providers import GeminiProvider

api_key = "YOUR_GEMINI_API_KEY"
provider = GeminiProvider(api_key=api_key)

# Attach pilot to a tab
pilot = AIPilot(tab, provider=provider)
```

### Running the Pilot

```python
success = await pilot.run("Search for 'Chuscraper' on Google and click the first result")

if success:
    print("AI completed the task!")
else:
    print("AI failed.")
```

## Vision Capabilities

Chuscraper also supports vision-based extraction (if configured).

*(Documentation in progress)*
