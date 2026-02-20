# Chuscraper Repo Analysis (Hindi)

## Project ka core kya hai
- `chuscraper` ek async CDP (Chrome DevTools Protocol) based scraping/automation framework hai, jiska focus stealth aur anti-detection par hai.
- Main API `chuscraper.start(...)` aur `Browser` object ke around centered hai.
- `core/` folder browser lifecycle, tabs, elements, network/wait/actions jaise primitives handle karta hai.
- `cdp/` folder generated/protocol bindings deta hai (domain-wise modules: page, runtime, network, input, etc.).
- `tests/` me core unit/integration tests aur docs tutorial smoke tests hain.
- `website/` folder Docusaurus docs site ke liye hai.

## High-priority observations
1. `pyproject.toml` me `emoji` dependency duplicate hai.
2. `README.md` me kai doc links `docs/...` path par point karte hain, lekin repo me top-level `docs/` folder present nahi hai (docs `website/docs/` me hain), isse broken links ka risk hai.
3. Clean environment me `pytest -q` test collection phase me hi fail ho raha hai because `pytest_mock` install nahi hai.
4. Pytest warning aa rahi hai for unknown options `asyncio_mode` and `asyncio_default_fixture_loop_scope`, jo tab aata hai jab `pytest-asyncio` plugin available na ho.

## Suggested fixes (quick wins)
- `pyproject.toml` dependencies se duplicate `emoji` entry hatao.
- README docs links ko `website/docs/...` ya published docs URLs par migrate karo.
- Contributor onboarding me clear test setup command add karo (example: `pip install -e . "pytest pytest-mock pytest-asyncio"` ya dev-group equivalent).
- CI me test job ke start me plugin presence validate karo, taaki collection-time failure jaldi dikhe.
