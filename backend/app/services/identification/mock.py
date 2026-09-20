from typing import List, Optional, Dict, Any
from app.services.identification.base import IdentificationProvider
from app.schemas.identification import PredictionResponse, PredictionItem
from app.utils.confidence import normalize_confidence

class MockProvider(IdentificationProvider):
    """
    Development Mock Identification Provider.
    Returns deterministic species predictions labeled explicitly as mock/demo.
    Used ONLY when IDENTIFICATION_MODE=mock or in offline development fallback.
    """

    MOCK_PLANTS = [
        {"scientific": "Azadirachta indica", "common": ["Neem", "Indian Lilac"], "confidence": 0.91},
        {"scientific": "Mangifera indica", "common": ["Mango Tree", "Aam"], "confidence": 0.05},
        {"scientific": "Ficus religiosa", "common": ["Sacred Fig", "Peepal"], "confidence": 0.02},
        {"scientific": "Pongamia pinnata", "common": ["Indian Beech", "Karanj"], "confidence": 0.01}
    ]

    MOCK_BIRDS = [
        {"scientific": "Passer domesticus", "common": ["House Sparrow"], "confidence": 0.88},
        {"scientific": "Acridotheres tristis", "common": ["Common Myna"], "confidence": 0.07},
        {"scientific": "Pycnonotus cafer", "common": ["Red-vented Bulbul"], "confidence": 0.03},
        {"scientific": "Corvus splendens", "common": ["House Crow"], "confidence": 0.01}
    ]

    MOCK_INSECTS = [
        {"scientific": "Apis cerana", "common": ["Asian Honey Bee"], "confidence": 0.85},
        {"scientific": "Danaus chrysippus", "common": ["Plain Tiger Butterfly"], "confidence": 0.09},
        {"scientific": "Coccinella septempunctata", "common": ["Seven-spot Ladybird"], "confidence": 0.04},
        {"scientific": "Pantala flavescens", "common": ["Wandering Glider Dragonfly"], "confidence": 0.01}
    ]

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str,
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        cat = category.lower()
        if cat == "bird":
            pool = self.MOCK_BIRDS
        elif cat == "insect":
            pool = self.MOCK_INSECTS
        else:
            pool = self.MOCK_PLANTS

        predictions = []
        for idx, item in enumerate(pool, start=1):
            predictions.append(
                PredictionItem(
                    rank=idx,
                    scientific_name=item["scientific"],
                    common_names=item["common"],
                    confidence=normalize_confidence(item["confidence"]),
                    taxonomic_rank="species"
                )
            )

        return PredictionResponse(
            success=True,
            category=cat,
            provider="mock",
            model_name="Demo Mock Identification Engine",
            model_version="mock-v1.0.0",
            identification_status="HIGH_CONFIDENCE",
            predictions=predictions,
            is_mock=True
        )
