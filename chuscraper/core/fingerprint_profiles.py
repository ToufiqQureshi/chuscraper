import random
from dataclasses import dataclass, field
from typing import List, Dict, Any

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
    fonts: List[str]

# Profiles for strictly coherent browser fingerprints
PROFILES: Dict[str, BrowserProfile] = {
    "win_nvidia": BrowserProfile(
        os="Windows",
        platform="Win32",
        ua_platform="Windows NT 10.0",
        cores=8,
        memory=16,
        gpu=GpuProfile(
            vendor="Google Inc. (NVIDIA)",
            renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        ),
        fonts=["Arial", "Cambria", "Consolas", "Courier New", "Georgia", "MS Gothic", "MS PGothic", "Segoe UI", "Tahoma", "Times New Roman", "Verdana"]
    ),
    "win_intel": BrowserProfile(
        os="Windows",
        platform="Win32",
        ua_platform="Windows NT 10.0",
        cores=4,
        memory=8,
        gpu=GpuProfile(
            vendor="Google Inc. (Intel)",
            renderer="ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        ),
        fonts=["Arial", "Segoe UI", "Verdana", "Times New Roman"]
    ),
    "mac_apple": BrowserProfile(
        os="macOS",
        platform="MacIntel",
        ua_platform="Macintosh; Intel Mac OS X 10_15_7",
        cores=8,
        memory=16,
        gpu=GpuProfile(
            vendor="Apple Inc.",
            renderer="Apple M2"
        ),
        fonts=["Avenir", "Avenir Next", "Courier", "Helvetica", "Helvetica Neue", "Menlo", "Monaco", "Palatino", "PingFang SC", "Times"]
    )
}

def get_random_profile(os_type: str = "auto") -> BrowserProfile:
    """
    Returns a coherent profile based on the desired OS type.
    """
    if os_type == "auto":
        name = random.choice(list(PROFILES.keys()))
    elif "win" in os_type.lower():
        name = random.choice(["win_nvidia", "win_intel"])
    elif "mac" in os_type.lower():
        name = "mac_apple"
    else:
        name = random.choice(list(PROFILES.keys()))
    
    return PROFILES[name]
