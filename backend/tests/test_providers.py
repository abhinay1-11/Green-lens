import pytest
from app.config import settings
from app.services.identification.mock import MockProvider
from app.services.identification.factory import get_identification_provider

def test_mock_provider_plants():
    provider = MockProvider()
    response = provider.identify([], category="plant")
    assert response.provider == "mock"
    assert response.category == "plant"
    assert response.is_mock is True
    assert len(response.predictions) > 0
    assert response.predictions[0].scientific_name == "Azadirachta indica"
    assert response.predictions[0].confidence == 0.91

def test_provider_factory_real_mode_unconfigured():
    settings.IDENTIFICATION_MODE = "real"
    settings.PLANTNET_API_KEY = ""
    provider = get_identification_provider("plant")
    response = provider.identify([], category="plant")
    assert response.success is False
    assert response.error.code == "PLANT_PROVIDER_NOT_CONFIGURED"
    assert len(response.predictions) == 0

def test_provider_factory_mock_mode():
    settings.IDENTIFICATION_MODE = "mock"
    provider = get_identification_provider("plant")
    response = provider.identify([], category="plant")
    assert response.success is True
    assert response.is_mock is True
    assert len(response.predictions) > 0
    settings.IDENTIFICATION_MODE = "real"
