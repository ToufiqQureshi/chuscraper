import sys
import logging

_banner_printed = False

def print_banner():
    """
    Prints the Chuscraper startup banner once per process.
    """
    global _banner_printed
    if _banner_printed:
        return

    _banner_printed = True

    # ANSI Color Codes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Check if we are in a terminal that supports colors
    if not sys.stdout.isatty():
        CYAN = GREEN = RESET = BOLD = ""

    version = "0.19.3"

    banner = f"""{CYAN}
   ________  __  _______ __________  ___    ____  __________
  / ____/ / / / / / ___// ____/ __ \\/   |  / __ \\/ ____/ __ \\\\
 / /   / /_/ / / /\\__ \\/ /   / /_/ / /| | / /_/ / __/ / /_/ /
/ /___/ __  / /_/ /__/ / /___/ _, _/ ___ / ____/ /___/ _, _/
\\____/_/ /_/\\____/____/\\____/_/ |_/_/  |/_/   /_____/_/ |_|
{RESET}
{BOLD}Chuscraper v{version}{RESET} {GREEN}• Stealth Scraping Engine{RESET}
{CYAN}Running in Undetectable Mode{RESET}
"""
    # Print to stderr to avoid interfering with stdout pipe outputs
    print(banner, file=sys.stderr)
