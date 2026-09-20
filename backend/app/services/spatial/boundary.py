import os
import json
from typing import Dict, Any, Optional, Tuple
from shapely.geometry import shape, Point
from app.config import settings

class CampusBoundaryValidator:
    """
    Validates observation GPS latitude/longitude against configured GeoJSON campus boundary polygon.
    """

    def __init__(self, geojson_path: Optional[str] = None):
        path = geojson_path or settings.CAMPUS_BOUNDARY_FILE
        self.polygon = None
        self.load_boundary(path)

    def load_boundary(self, path: str):
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                features = data.get("features", [])
                if features:
                    geom = features[0].get("geometry", {})
                    self.polygon = shape(geom)
        except Exception as exc:
            print(f"Warning: Failed to load campus boundary GeoJSON: {exc}")
            self.polygon = None

    def is_inside_campus(self, latitude: float, longitude: float) -> Tuple[bool, Optional[str]]:
        """
        Checks if given (lat, lon) point falls inside campus polygon.
        Note: GeoJSON coordinates are [longitude, latitude].
        """
        if self.polygon is None:
            return True, "Boundary file not loaded"

        try:
            # Shapely Point(x, y) = Point(longitude, latitude)
            point = Point(longitude, latitude)
            is_inside = self.polygon.contains(point)
            message = "Inside campus boundary" if is_inside else "Location appears outside campus boundary"
            return is_inside, message
        except Exception as exc:
            return True, f"Boundary check error: {str(exc)}"

boundary_validator = CampusBoundaryValidator()
