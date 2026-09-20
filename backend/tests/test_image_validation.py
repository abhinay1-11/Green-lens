import pytest
import io
from PIL import Image
from fastapi import HTTPException
from app.utils.image_validation import validate_image_file

def create_dummy_jpeg_bytes(width=100, height=100) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color="green")
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_valid_image_validation():
    file_bytes = create_dummy_jpeg_bytes()
    width, height, checksum = validate_image_file(file_bytes, "test.jpg", "image/jpeg")
    assert width == 100
    assert height == 100
    assert len(checksum) == 64  # SHA256 length

def test_empty_file_rejection():
    with pytest.raises(HTTPException) as exc_info:
        validate_image_file(b"", "empty.jpg", "image/jpeg")
    assert exc_info.value.status_code == 400

def test_corrupted_file_rejection():
    with pytest.raises(HTTPException) as exc_info:
        validate_image_file(b"NOT_AN_IMAGE_CONTENT", "fake.jpg", "image/jpeg")
    assert exc_info.value.status_code == 400
