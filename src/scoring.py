"""
Score calculation module.
Computes scores based on hole positions relative to target center.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple

from .config import TargetConfig
from .detection import DetectedCircle, TargetCalibration


@dataclass
class ScoredHole:
    """A detected hole with its calculated score."""
    hole: DetectedCircle
    score: float
    ring_name: str
    distance_from_center_mm: float
    
    @property
    def center(self) -> Tuple[float, float]:
        return self.hole.center


def calculate_distance_mm(
    hole: DetectedCircle,
    calibration: TargetCalibration
) -> float:
    """Calculate distance from hole center to target center in mm."""
    dx = hole.center_x - calibration.center_x
    dy = hole.center_y - calibration.center_y
    distance_px = math.sqrt(dx * dx + dy * dy)
    return calibration.px_to_mm(distance_px)


def calculate_score(
    hole: DetectedCircle,
    calibration: TargetCalibration,
    target_config: TargetConfig
) -> ScoredHole:
    """
    Calculate the score for a single hole.
    
    Uses ISSF scoring rules: the score is determined by where the 
    edge of the bullet hole touches the scoring rings.
    """
    distance_mm = calculate_distance_mm(hole, calibration)
    
    # ISSF scoring: subtract bullet radius (edge scoring)
    # The bullet only needs to touch the ring to score
    scoring_distance = distance_mm - target_config.bullet_radius_mm
    
    # Find which ring the bullet is in
    for ring in target_config.rings:
        ring_radius = ring.diameter_mm / 2
        if scoring_distance <= ring_radius:
            return ScoredHole(
                hole=hole,
                score=ring.score,
                ring_name=ring.name,
                distance_from_center_mm=distance_mm
            )
    
    # Miss - outside all rings
    return ScoredHole(
        hole=hole,
        score=0,
        ring_name="Miss",
        distance_from_center_mm=distance_mm
    )


def calculate_all_scores(
    holes: List[DetectedCircle],
    calibration: TargetCalibration,
    target_config: TargetConfig
) -> List[ScoredHole]:
    """Calculate scores for all detected holes."""
    return [
        calculate_score(hole, calibration, target_config)
        for hole in holes
    ]


def get_total_score(scored_holes: List[ScoredHole]) -> float:
    """Calculate total score from all holes."""
    return sum(h.score for h in scored_holes)


def get_score_summary(scored_holes: List[ScoredHole]) -> dict:
    """
    Generate a summary of scoring results.
    
    Returns:
        Dictionary with total score, shot count, average, and breakdown.
    """
    if not scored_holes:
        return {
            "total": 0,
            "shot_count": 0,
            "average": 0,
            "breakdown": []
        }
    
    total = get_total_score(scored_holes)
    count = len(scored_holes)
    
    breakdown = [
        {
            "shot": i + 1,
            "score": h.score,
            "ring": h.ring_name,
            "distance_mm": round(h.distance_from_center_mm, 2)
        }
        for i, h in enumerate(scored_holes)
    ]
    
    return {
        "total": total,
        "shot_count": count,
        "average": round(total / count, 2),
        "breakdown": breakdown
    }
