"""
Configuration module for target specifications and app settings.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Ring:
    """Represents a scoring ring on the target."""
    name: str
    score: float
    diameter_mm: float
    
    @property
    def radius_mm(self) -> float:
        return self.diameter_mm / 2


@dataclass
class TargetConfig:
    """Configuration for a shooting target type."""
    name: str
    bullet_diameter_mm: float
    rings: List[Ring]
    black_area_diameter_mm: float
    total_diameter_mm: float
    
    @property
    def bullet_radius_mm(self) -> float:
        return self.bullet_diameter_mm / 2
    
    @classmethod
    def from_json(cls, json_path: Path) -> "TargetConfig":
        """Load target configuration from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        rings = [
            Ring(name=r["ring"], score=r["score"], diameter_mm=r["diameter_mm"])
            for r in data["rings"]
        ]
        
        return cls(
            name=data["name"],
            bullet_diameter_mm=data["bullet_diameter_mm"],
            rings=rings,
            black_area_diameter_mm=data["black_area_diameter_mm"],
            total_diameter_mm=data["total_diameter_mm"]
        )

def get_targets_dir() -> Path:
    """Get the targets directory path."""
    return Path(__file__).parent.parent / "targets"


def list_available_targets() -> List[tuple[str, Path]]:
    """
    List all available target configurations.
    Returns list of (name, path) tuples.
    """
    targets_dir = get_targets_dir()
    targets = []
    
    for json_file in sorted(targets_dir.glob("*.json")):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            targets.append((data.get("name", json_file.stem), json_file))
        except:
            continue
    
    return targets


def load_target(path: Path) -> TargetConfig:
    """Load a target configuration from a JSON file."""
    return TargetConfig.from_json(path)


def get_default_target() -> TargetConfig:
    """Load the default Brazil RS 50m Air Rifle target configuration."""
    targets_dir = get_targets_dir()
    default_path = targets_dir / "brazil_rs_50m_air.json"
    
    # Fallback to ISSF 50m if Brazil RS doesn't exist
    if not default_path.exists():
        default_path = targets_dir / "issf_50m_rifle.json"
    
    return TargetConfig.from_json(default_path)


# Application settings
class AppSettings:
    """Global application settings."""
    # Detection parameters (can be tuned)
    HOUGH_DP = 1.2
    HOUGH_MIN_DIST_MM = 5.0  # Minimum distance between hole centers
    HOUGH_PARAM1 = 100       # Canny edge threshold
    HOUGH_PARAM2 = 30        # Accumulator threshold
    HOLE_MIN_RADIUS_MM = 2.0
    HOLE_MAX_RADIUS_MM = 4.0
    
    # Preprocessing
    GAUSSIAN_BLUR_SIZE = 5
    
    # Camera
    DEFAULT_CAMERA_INDEX = 0
    CAMERA_FRAME_WIDTH = 1280
    CAMERA_FRAME_HEIGHT = 720
