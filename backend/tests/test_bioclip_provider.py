import pytest
from unittest.mock import patch, MagicMock
from app.services.identification.bioclip import BioCLIPBirdProvider, BioCLIPModelSingleton
from app.schemas.identification import PredictionResponse

# Sample dummy image payload
DUMMY_IMAGE = {
    "file_bytes": b"fake_image_bytes",
    "filename": "bird_test.jpg",
    "saved_path": "/uploads/test.jpg"
}

def test_bioclip_provider_invalid_image():
    provider = BioCLIPBirdProvider()
    response = provider.identify([], category="bird")
    assert response.success is False
    assert response.error.code == "INVALID_IMAGE"

@patch("app.services.identification.bioclip.BioCLIPModelSingleton.get_classifier")
def test_bioclip_provider_mocked_success(mock_get_classifier):
    mock_clf = MagicMock()
    mock_clf.predict.return_value = [
        {
            "species": "Centrocercus urophasianus",
            "common_name": "Greater Sage-Grouse",
            "score": 0.8407789468765259,
            "kingdom": "Animalia",
            "phylum": "Chordata",
            "class": "Aves",
            "order": "Galliformes",
            "family": "Phasianidae",
            "genus": "Centrocercus"
        },
        {
            "species": "Centrocercus minimus",
            "common_name": "Gunnison grouse",
            "score": 0.12547890841960907,
            "kingdom": "Animalia",
            "phylum": "Chordata",
            "class": "Aves",
            "order": "Galliformes",
            "family": "Phasianidae",
            "genus": "Centrocercus"
        }
    ]
    mock_get_classifier.return_value = mock_clf

    with patch("PIL.Image.open") as mock_pil_open:
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_pil_open.return_value = mock_img

        provider = BioCLIPBirdProvider()
        response = provider.identify([DUMMY_IMAGE], category="bird")

        assert response.success is True
        assert response.category == "bird"
        assert response.provider == "BioCLIP 2"
        assert response.identification_status == "HIGH_CONFIDENCE"
        assert len(response.predictions) == 2
        assert response.predictions[0].scientific_name == "Centrocercus urophasianus"
        assert response.predictions[0].common_names == ["Greater Sage-Grouse"]
        assert abs(response.predictions[0].confidence - 0.8408) < 0.001

@patch("app.services.identification.bioclip.BioCLIPModelSingleton.get_classifier")
def test_bioclip_provider_low_confidence(mock_get_classifier):
    mock_clf = MagicMock()
    mock_clf.predict.return_value = [
        {
            "species": "Unknown Bird",
            "common_name": "Mysterious Finch",
            "score": 0.15
        }
    ]
    mock_get_classifier.return_value = mock_clf

    with patch("PIL.Image.open") as mock_pil_open:
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_pil_open.return_value = mock_img

        provider = BioCLIPBirdProvider()
        response = provider.identify([DUMMY_IMAGE], category="bird")

        assert response.success is True
        assert response.identification_status == "LOW_CONFIDENCE"
        assert response.predictions[0].confidence == 0.15

@patch("app.services.identification.bioclip.BioCLIPModelSingleton.get_classifier")
def test_bioclip_provider_error_handling(mock_get_classifier):
    mock_get_classifier.side_effect = RuntimeError("BioCLIP model load failure")

    with patch("PIL.Image.open") as mock_pil_open:
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_pil_open.return_value = mock_img

        provider = BioCLIPBirdProvider()
        response = provider.identify([DUMMY_IMAGE], category="bird")

        assert response.success is False
        assert response.error.code == "BIRD_PROVIDER_UNAVAILABLE"
        assert "temporarily unavailable" in response.error.message

@pytest.mark.integration
def test_bioclip_real_sage_grouse_integration():
    """
    Real BioCLIP 2 integration test against Female_Greater_Sage-Grouse.webp.
    Run with: pytest -v -m integration
    """
    import os
    test_img_path = r"C:\Users\abhin\.gemini\antigravity\scratch\greenlens\data\test_images\birds\Female_Greater_Sage-Grouse.webp"
    assert os.path.exists(test_img_path), f"Test image not found at {test_img_path}"

    with open(test_img_path, "rb") as f:
        file_bytes = f.read()

    provider = BioCLIPBirdProvider()
    response = provider.identify([{"file_bytes": file_bytes, "filename": "Female_Greater_Sage-Grouse.webp"}], category="bird")

    assert response.success is True
    assert response.category == "bird"
    assert response.provider == "BioCLIP 2"
    assert len(response.predictions) > 0

    top_pred = response.predictions[0]
    assert top_pred.scientific_name == "Centrocercus urophasianus"
    assert "Greater Sage-Grouse" in top_pred.common_names
    assert top_pred.confidence > 0.80
