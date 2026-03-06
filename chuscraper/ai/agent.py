import asyncio
import logging
from typing import Optional, Dict, Any, List
from chuscraper.core.tab import Tab
from chuscraper.ai.selectors import generate_selectors

logger = logging.getLogger(__name__)

class Agent:
    """
    Autonomous Agent that drives the browser using LLM instructions.
    Uses 'generate_selectors' to find elements dynamically based on description.
    """

    def __init__(self, tab: Tab, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.tab = tab
        self.api_key = api_key
        self.model = model

    async def act(self, instruction: str) -> bool:
        """
        Executes a natural language action on the page.
        Example: "Click the login button", "Type hello in search"
        """
        logger.info(f"Agent Action: {instruction}")

        # 1. Get simplified HTML context
        # Ideally we'd strip this down to interactive elements only for token savings
        html_content = await self.tab.get_content()
        # Truncate for prototype safety
        snippet = html_content[:20000]

        # 2. Ask LLM to translate instruction to action
        # We reuse the generate_selectors logic but adapt it for actions
        # Actually, let's create a dedicated prompt for actions

        try:
            from openai import AsyncOpenAI
            import json
            import os

            key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                logger.error("Agent requires OPENAI_API_KEY")
                return False

            client = AsyncOpenAI(api_key=key)

            system_prompt = """
            You are a browser automation agent. Given the HTML and an instruction, output a JSON action.
            Supported Actions:
            - {"action": "click", "selector": "css_selector"}
            - {"action": "type", "selector": "css_selector", "text": "value"}
            - {"action": "scroll", "direction": "down"}
            - {"action": "wait", "seconds": 2}

            Return ONLY valid JSON.
            """

            user_prompt = f"""
            Instruction: {instruction}

            HTML Snippet:
            {snippet}
            """

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )

            plan = json.loads(response.choices[0].message.content)
            logger.info(f"Agent Plan: {plan}")

            return await self._execute_plan(plan)

        except Exception as e:
            logger.error(f"Agent Failed: {e}")
            return False

    async def _execute_plan(self, plan: Dict[str, Any]) -> bool:
        action = plan.get("action")
        selector = plan.get("selector")

        try:
            if action == "click" and selector:
                await self.tab.click(selector)
                return True
            elif action == "type" and selector:
                text = plan.get("text", "")
                await self.tab.type(selector, text)
                return True
            elif action == "scroll":
                await self.tab.scroll_down(amount=30)
                return True
            elif action == "wait":
                await self.tab.sleep(plan.get("seconds", 1))
                return True
            else:
                logger.warning(f"Unknown action: {action}")
                return False
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            return False
