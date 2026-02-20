import random
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class GpuProfile:
    vendor: str
    renderer: str

@dataclass
class BrowserProfile:
    os: str
    platform: str
    ua_platform: str
    cores: int
    memory: int
    gpu: GpuProfile
    screen_width: int
    screen_height: int
    fonts: List[str]

# Expanded list of common fonts per OS to mix and match
FONTS_WIN = ["Arial", "Calibri", "Cambria", "Consolas", "Courier New", "Georgia", "Impact", "Lucida Console", "MS Gothic", "MS Sans Serif", "MS Serif", "Palatino Linotype", "Segoe UI", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana"]
FONTS_MAC = ["Arial", "Arial Black", "Comic Sans MS", "Courier New", "Georgia", "Impact", "Times New Roman", "Trebuchet MS", "Verdana", "American Typewriter", "Andale Mono", "Apple Chancery", "Arial Narrow", "Baskerville", "Big Caslon", "Brush Script MT", "Chalkboard", "Copperplate", "Courier", "Didot", "Futura", "Geneva", "Gill Sans", "Helvetica", "Helvetica Neue", "Herculanum", "Hoefler Text", "Lucida Grande", "Marker Felt", "Menlo", "Monaco", "Optima", "Papyrus", "Skia", "Zapfino"]
FONTS_LINUX = ["Arial", "Courier New", "Georgia", "Impact", "Times New Roman", "Trebuchet MS", "Verdana", "DejaVu Sans", "DejaVu Serif", "Liberation Mono", "Liberation Sans", "Liberation Serif", "Ubuntu", "Ubuntu Mono"]

# Common screen resolutions (width, height)
RESOLUTIONS = [
    (1920, 1080), (1366, 768), (1440, 900), (1536, 864), (2560, 1440), (1280, 720), (1600, 900)
]

# Hardware Concurrency options (logical cores)
CORES = [2, 4, 6, 8, 12, 16, 24, 32]

# Device Memory options (GB)
MEMORY = [2, 4, 8, 16, 32]

def _get_gpu(os_type: str) -> GpuProfile:
    if os_type == "Windows":
        return random.choice([
            GpuProfile("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
            GpuProfile("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"),
            GpuProfile("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
            GpuProfile("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 5700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"),
        ])
    elif os_type == "macOS":
        return random.choice([
            GpuProfile("Apple Inc.", "Apple M1"),
            GpuProfile("Apple Inc.", "Apple M1 Pro"),
            GpuProfile("Apple Inc.", "Apple M2"),
            GpuProfile("Apple Inc.", "Apple M2 Pro"),
        ])
    else:  # Linux
        return random.choice([
            GpuProfile("Google Inc. (NVIDIA)", "NVIDIA GeForce GTX 1050 Ti"),
            GpuProfile("Google Inc. (Intel)", "Intel(R) UHD Graphics 620"),
            GpuProfile("Google Inc. (AMD)", "AMD Radeon RX 580"),
        ])

def get_random_profile(os_type: str = "auto") -> BrowserProfile:
    """
    Returns a generated coherent profile based on the desired OS type.
    """
    # Auto-detect host OS if not specified
    if os_type == "auto":
        if sys.platform == "win32":
            os_type = "Windows"
        elif sys.platform == "darwin":
            os_type = "macOS"
        else:
            os_type = "Linux"

    # Normalize OS type input
    if "win" in os_type.lower():
        target_os = "Windows"
        platform = "Win32"
        # Randomize Windows version in UA platform string
        ua_platform = random.choice(["Windows NT 10.0; Win64; x64", "Windows NT 10.0; WOW64", "Windows NT 11.0; Win64; x64"])
        fonts = random.sample(FONTS_WIN, k=min(len(FONTS_WIN), random.randint(5, 10)))
    elif "mac" in os_type.lower():
        target_os = "macOS"
        platform = "MacIntel"
        # Randomize macOS version
        mac_ver = random.choice(["10_15_7", "11_6", "12_3", "13_1", "14_0"])
        ua_platform = f"Macintosh; Intel Mac OS X {mac_ver}"
        fonts = random.sample(FONTS_MAC, k=min(len(FONTS_MAC), random.randint(5, 10)))
    else:
        target_os = "Linux"
        platform = "Linux x86_64"
        ua_platform = "X11; Linux x86_64"
        fonts = random.sample(FONTS_LINUX, k=min(len(FONTS_LINUX), random.randint(5, 10)))

    width, height = random.choice(RESOLUTIONS)
    
    return BrowserProfile(
        os=target_os,
        platform=platform,
        ua_platform=ua_platform,
        cores=random.choice(CORES),
        memory=random.choice(MEMORY),
        gpu=_get_gpu(target_os),
        screen_width=width,
        screen_height=height,
        fonts=fonts
    )
