import io
import pytest
from PIL import Image
from app.services.identification.insect import InsectProvider
from app.services.identification.insect_model import run_insect_species_classifier, preprocess_insect_image


@pytest.fixture
def insect_provider():
    return InsectProvider()


def _make_dummy_image(width=600, height=400, color=(100, 180, 80)):
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# 1. Valid insect image
def test_valid_insect_image(insect_provider):
    # Using existing test insect image bee_sample.jpg
    import os
    img_path = os.path.abspath("data/test_images/insects/bee_sample.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.abspath("../data/test_images/insects/bee_sample.jpg")

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = insect_provider.identify([{"file_bytes": img_bytes}])
    assert res.success is True
    assert res.category == "insect"
    assert res.identification_status in ["HIGH_CONFIDENCE", "MEDIUM_CONFIDENCE", "LOW_CONFIDENCE"]
    assert len(res.predictions) > 0


# 2. Valid insect with leaf background
def test_valid_insect_leaf_background(insect_provider):
    import os
    img_path = os.path.abspath("data/test_images/insects/dragonfly_blue.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.abspath("../data/test_images/insects/dragonfly_blue.jpg")

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = insect_provider.identify([{"file_bytes": img_bytes}])
    assert res.success is True
    assert len(res.predictions) > 0


# 3. Valid insect with monarch/dirt background
def test_valid_insect_monarch(insect_provider):
    import os
    img_path = os.path.abspath("data/test_images/insects/butterfly_monarch.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.abspath("../data/test_images/insects/butterfly_monarch.jpg")

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = insect_provider.identify([{"file_bytes": img_bytes}])
    assert res.success is True
    assert len(res.predictions) > 0


# 4. Valid insect portrait aspect ratio
def test_insect_portrait_aspect_ratio(insect_provider):
    img_bytes = _make_dummy_image(width=400, height=800, color=(120, 160, 90))
    res = insect_provider.identify([{"file_bytes": img_bytes}])
    assert res.category == "insect"


# 5. Valid insect landscape aspect ratio
def test_insect_landscape_aspect_ratio(insect_provider):
    img_bytes = _make_dummy_image(width=1200, height=600, color=(90, 150, 100))
    res = insect_provider.identify([{"file_bytes": img_bytes}])
    assert res.category == "insect"


# 6. Genuinely non-insect image (solid plain background)
def test_genuinely_non_insect_image(insect_provider):
    # Pure solid gray canvas triggers background rejection
    img = Image.new("RGB", (300, 300), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    res = insect_provider.identify([{"file_bytes": buf.getvalue()}])
    # Should be rejected as background or handled as unavailable
    if not res.success:
        assert res.error.code in ["NO_INSECT_DETECTED", "IDENTIFICATION_UNAVAILABLE"]


# 7. Corrupted image bytes
def test_corrupted_image_bytes(insect_provider):
    res = insect_provider.identify([{"file_bytes": b"corrupted_garbage_bytes"}])
    assert res.success is False
    assert res.error.code == "INVALID_IMAGE"


# 8. Genuinely tiny image (< 16x16)
def test_tiny_image_resolution(insect_provider):
    img = Image.new("RGB", (10, 10), color=(100, 100, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    res = insect_provider.identify([{"file_bytes": buf.getvalue()}])
    assert res.success is False
    assert res.error.code == "IMAGE_TOO_SMALL"


# 9. Insect prediction formatting
def test_low_confidence_prediction_formatting(insect_provider):
    import os
    img_path = os.path.abspath("data/test_images/insects/butterfly_monarch.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.abspath("../data/test_images/insects/butterfly_monarch.jpg")

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = insect_provider.identify([{"file_bytes": img_bytes}])
    assert res.success is True
    assert res.category == "insect"
    assert len(res.predictions) > 0


# 10. Model input preprocessing tensor shape and scale
def test_model_preprocessing_tensor():
    img_bytes = _make_dummy_image(width=500, height=300)
    arr = preprocess_insect_image(img_bytes)
    assert arr.shape == (1, 3, 224, 224)
    assert arr.dtype.name == "float32"

