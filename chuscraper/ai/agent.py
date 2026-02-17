import json
import logging
import asyncio
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from .providers import AIProvider, GeminiProvider
from .. import cdp

if TYPE_CHECKING:
    from ..core.tab import Tab

logger = logging.getLogger(__name__)

class AIPilot:
    def __init__(self, tab: "Tab", provider: Optional[AIProvider] = None, safe_mode: bool = True):
        self.tab = tab
        self.safe_mode = safe_mode
        if not provider:
            try:
                self.provider = GeminiProvider()
            except Exception as e:
                logger.warning(f"Default GeminiProvider failed to initialize: {e}")
                self.provider = None
        else:
            self.provider = provider

        self.history = []
        self.last_error = None

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Robustly extracts JSON from text (handles markdown blocks, etc)."""
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding first { and last } (Naive repair)
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        raise ValueError(f"Could not extract valid JSON from response. Raw: {text[:200]}...")

    async def get_semantic_tree(self) -> List[Dict[str, Any]]:
        """Retrieves and simplifies the Accessibility Tree."""
        try:
            # Enable accessibility if not already
            await self.tab.send(cdp.accessibility.enable())
            nodes = await self.tab.send(cdp.accessibility.get_full_ax_tree())
        except Exception as e:
            logger.error(f"Failed to get AX tree: {e}")
            return []

        simplified = []
        for node in nodes:
            role = node.role.value if node.role else "unknown"
            name = node.name.value if node.name else ""
            description = node.description.value if node.description else ""
            value = node.value.value if node.value else ""
            
            # Roles we care about for interaction
            interactable_roles = [
                "button", "link", "textbox", "checkbox", "combobox", 
                "listbox", "menuitem", "searchbox", "tab", "input", "textarea"
            ]
            
            # Include if interactable OR has significant content
            if role in interactable_roles or (name and len(name) < 200):
                item = {
                    "id": str(node.node_id), # AXNodeID
                    "backend_id": node.backend_node_id,
                    "role": role,
                    "name": name,
                }
                if description: item["description"] = description
                if value: item["value"] = value

                simplified.append(item)
        
        return simplified

    async def run(self, goal: str, max_steps: int = 15) -> bool:
        """Main autonomous loop."""
        if not self.provider:
            logger.error("❌ No AI Provider configured. Cannot run pilot.")
            return False

        print(f"\n--- 🤖 AI PILOT STARTING: {goal} ---")
        
        for step in range(max_steps):
            try:
                tree = await self.get_semantic_tree()
                current_url = await self.tab.evaluate("window.location.href")

                # Context Management
                history_context = json.dumps(self.history[-5:], indent=2) # Last 5 steps
                error_context = ""
                if self.last_error:
                    error_context = f"\n⚠️ PREVIOUS STEP FAILED: {self.last_error}\n(Adjust your strategy!)\n"

                # Truncate tree if too large (dumb heuristic)
                tree_str = json.dumps(tree[:150], indent=2)

                prompt = f"""
GOAL: {goal}
CURRENT URL: {current_url}
STEP: {step + 1}/{max_steps}
{error_context}

ACCESSIBILITY TREE (Simplified - First 150 nodes):
{tree_str}

HISTORY:
{history_context}

INSTRUCTIONS:
1. Analyze the tree to find the element that matches the goal.
2. If the element is not in the tree, scroll or try a different approach.
3. Return ONLY JSON.

FORMAT:
{{
    "action": "CLICK" | "TYPE" | "SCROLL" | "WAIT" | "COMPLETE" | "FAIL",
    "element_id": "node_id from tree (preferred)",
    "name": "element name or text (backup)",
    "value": "text to type (if TYPE action)",
    "thought": "Brief reasoning for this action"
}}
"""
                response_text = await self.provider.generate_response(prompt, json_mode=True)
                decision = self._extract_json(response_text)

                action = decision.get("action", "").upper()
                thought = decision.get("thought", "")
                target_id = decision.get("element_id") # AXNodeId (deprecated for internal use)
                backend_id = decision.get("backend_id") # THE GOLDEN ID
                target_name = decision.get("name")
                value = decision.get("value")

                # Safe Browsing Mode Checks
                if self.safe_mode:
                    dangerous_keywords = ["delete", "logout", "payment", "buy", "purchase", "confirm", "close account"]
                    content_to_check = (target_name or "").lower() + (value or "").lower()
                    if any(kw in content_to_check for kw in dangerous_keywords):
                        print(f"🛑 SAFE MODE: Blocking potentially destructive action: {target_name}")
                        self.last_error = "Action blocked by Safe Mode (Safety Violation)"
                        continue

                    # Action Allowlist
                    allowed_actions = ["CLICK", "TYPE", "SCROLL", "WAIT", "COMPLETE", "FAIL"]
                    if action not in allowed_actions:
                        print(f"🛑 SAFE MODE: Blocking unauthorized action type: {action}")
                        continue
                print(f"STEP {step+1}: {action} | {thought}")
                
                # Execute action
                self.last_error = None # Reset error
                
                if action == "COMPLETE":
                    print("✅ GOAL REACHED!")
                    return True
                
                elif action == "FAIL":
                    print("❌ PILOT GAVE UP.")
                    return False
                
                elif action == "WAIT":
                    await asyncio.sleep(2)
                    self.history.append({"step": step+1, "action": action, "thought": thought, "status": "success"})
                    continue

                elif action == "SCROLL":
                    await self.tab.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(1)
                    self.history.append({"step": step+1, "action": action, "thought": thought, "status": "success"})
                    continue

                # For interaction, we now prioritize backend_id
                from ..core import element
                found_element = None

                # 1. Direct Resolution (High Precision)
                if backend_id:
                    try:
                        # Get RemoteObject from backend_id
                        # Simplest way: use a new helper in Element or Tab to resolve and wrap
                        found_element = await self.tab.resolve_node(backend_id)
                    except Exception as e:
                        logger.debug(f"Direct node resolution failed: {e}")

                # 2. Fallback to Name/Text search if ID fails
                if not found_element and target_name:
                    try:
                        found_element = await self.tab.find(target_name, timeout=3)
                    except: pass

                # 3. If fail, log error
                if not found_element and action in ["CLICK", "TYPE"]:
                    raise ValueError(f"Could not find element '{target_name}' (Backend ID: {backend_id})")

                # Perform Interaction
                if action == "CLICK":
                    await found_element.click()
                elif action == "TYPE":
                    await found_element.fill(value or "")

                # Record Success
                self.history.append({"step": step+1, "action": action, "target": target_name, "status": "success"})
                await asyncio.sleep(1) # Let page settle

            except Exception as e:
                logger.warning(f"Step {step+1} failed: {e}")
                self.last_error = str(e)
                self.history.append({"step": step+1, "action": "ERROR", "error": str(e)})
                # Do NOT break, loop continues and feeds error back to AI

        print("⚠️ MAX STEPS REACHED")
        return False
