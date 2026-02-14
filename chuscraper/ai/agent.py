import json
import logging
import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from .providers import AIProvider, GeminiProvider
from .. import cdp

if TYPE_CHECKING:
    from ..core.tab import Tab

logger = logging.getLogger(__name__)

class AIPilot:
    def __init__(self, tab: "Tab", provider: Optional[AIProvider] = None):
        self.tab = tab
        self.provider = provider or GeminiProvider()
        self.history = []

    async def get_semantic_tree(self) -> List[Dict[str, Any]]:
        """Retrieves and simplifies the Accessibility Tree."""
        # Note: We need to ensure Accessibility is enabled
        try:
            nodes = await self.tab.send(cdp.accessibility.get_full_ax_tree())
        except Exception as e:
            logger.error(f"Failed to get AX tree: {e}")
            return []

        simplified = []
        for node in nodes:
            # We filter for nodes that are likely interactable or have useful text
            role = node.role.value if node.role else "unknown"
            name = node.name.value if node.name else ""
            
            # Roles we care about for interaction
            interactable_roles = [
                "button", "link", "textbox", "checkbox", "combobox", 
                "listbox", "menuitem", "searchbox", "tab"
            ]
            
            if role in interactable_roles or name:
                simplified.append({
                    "id": node.node_id,
                    "role": role,
                    "name": name,
                    "description": node.description.value if node.description else "",
                    "value": node.value.value if node.value else ""
                })
        
        return simplified

    async def run(self, goal: str, max_steps: int = 10) -> bool:
        """Main autonomous loop."""
        print(f"\n--- AI PILOT STARTING: {goal} ---")
        
        for step in range(max_steps):
            tree = await self.get_semantic_tree()
            current_url = await self.tab.evaluate("window.location.href")
            
            prompt = f"""
GOAL: {goal}
CURRENT URL: {current_url}
STEP: {step + 1}/{max_steps}

ACCESSIBILITY TREE (Simplified):
{json.dumps(tree, indent=2)}

HISTORY:
{json.dumps(self.history, indent=2)}

Decide the NEXT ACTION to reach the goal. 
Return ONLY JSON in this format:
{{
    "action": "CLICK" | "TYPE" | "SCROLL" | "WAIT" | "COMPLETE" | "FAIL",
    "element_id": "accessibility_node_id",
    "value": "text to type if applicable",
    "thought": "briefly explain your reasoning"
}}
"""
            response_text = await self.provider.generate_response(prompt, json_mode=True)
            try:
                decision = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: clean markdown
                if "```json" in response_text:
                    clean = response_text.split("```json")[1].split("```")[0].strip()
                    decision = json.loads(clean)
                else:
                    logger.error(f"AI returned invalid JSON: {response_text}")
                    break

            action = decision.get("action")
            thought = decision.get("thought", "")
            element_id = decision.get("element_id")
            value = decision.get("value")

            print(f"STEP {step+1}: {action} - {thought}")
            self.history.append({"step": step + 1, "action": action, "thought": thought})

            if action == "COMPLETE":
                print("--- GOAL REACHED! ---")
                return True
            if action == "FAIL":
                print("--- PILOT FAILED ---")
                return False

            # Execute action
            try:
                # Find element by name or ID
                found = None
                target_name = decision.get("name") or ""
                target_id = decision.get("element_id")
                
                # Try to resolve by name first (more robust if tree changes)
                if target_name:
                    found = await self.tab.find(target_name, timeout=3)
                
                # Fallback to precise backend node if ID provided
                if not found and target_id:
                     # This requires searching the full tree again to find backend_node_id
                     # Simplified for now: use find as primary.
                     pass

                if action == "CLICK":
                    if found:
                        await found.click()
                    else:
                        print(f"Could not find element to click: {target_name}")
                
                elif action == "TYPE" and value:
                    if found:
                        await found.type(value)
                    
                elif action == "SCROLL":
                    await self.tab.evaluate("window.scrollBy(0, 500)")
                
                elif action == "WAIT":
                    await asyncio.sleep(2)

                await asyncio.sleep(1) # Let page react
            except Exception as e:
                print(f"Action failed: {e}")

        return False
