import pytest
from app.services.spatial.boundary import boundary_validator

def test_inside_campus_boundary():
    # 77.5900, 12.9750 is inside our test polygon bounds ([77.585, 12.97] to [77.595, 12.978])
    is_inside, msg = boundary_validator.is_inside_campus(12.9750, 77.5900)
    assert is_inside is True

def test_outside_campus_boundary():
    # 13.5000, 78.0000 is far outside
    is_inside, msg = boundary_validator.is_inside_campus(13.5000, 78.0000)
    assert is_inside is False
