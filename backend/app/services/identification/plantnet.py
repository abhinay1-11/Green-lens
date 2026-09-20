import time
import requests
from typing import List, Optional, Dict, Any

from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.services.identification.biodiversity_fallback import BiodiversityFallbackProvider
from app.schemas.identification import PredictionResponse, PredictionItem, ErrorDetail
from app.utils.confidence import normalize_confidence
from app.utils.image_validation import preprocess_image_for_model
from app.services.species_enrichment.session import get_http_session

PLANTNET_API_BASE = "https://my-api.plantnet.org/v2/identify"

class PlantNetProvider(IdentificationProvider):
    """
    Official Pl@ntNet API v2 Plant & Tree Identification Provider.
    Sends optimized plant/tree image bytes and organ tags to Pl@ntNet API server-side.
    Includes automated fallback to General Biodiversity Provider if primary is unconfigured or unavailable.
    """

    def __init__(self, api_key: Optional[str] = None):
        raw_key = api_key if api_key is not None else settings.clean_plantnet_api_key
        self.api_key = raw_key.strip().strip("'").strip('"') if raw_key else ""
        self.fallback_provider = BiodiversityFallbackProvider()

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str = "plant",
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        t_init_start = time.time()
        print("[IDENTIFY] Provider selected: plant (Pl@ntNet API v2)")
        print(f"[IDENTIFY] Provider initialization: {time.time() - t_init_start:.2f}s")

        # Check API Key availability
        if not self.api_key:
            print("[IDENTIFY] Pl@ntNet API key not set. Executing local biodiversity fallback...")
            fallback_res = self.fallback_provider.identify(images, category="plant", location=location)
            if fallback_res.success:
                return fallback_res

            return PredictionResponse(
                success=False,
                category="plant",
                provider="plantnet",
                model_name="Pl@ntNet API v2",
                model_version="v2",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                is_mock=False,
                error=ErrorDetail(
                    code="PLANT_PROVIDER_NOT_CONFIGURED",
                    message="Pl@ntNet API key is not configured in backend environment. Set PLANTNET_API_KEY in backend/.env."
                )
            )

        # Pl@ntNet POST /v2/identify/all?api-key={KEY}
        url = f"{PLANTNET_API_BASE}/all?api-key={self.api_key}"

        files = []
        data = []

        t_prep_start = time.time()
        # Up to 5 images per request supported by Pl@ntNet
        for idx, img in enumerate(images[:5]):
            raw_bytes = img.get("file_bytes")
            if not raw_bytes:
                continue

            # Model Preprocessing: EXIF transpose, RGB conversion, 1280px max dimension
            processed_bytes = preprocess_image_for_model(raw_bytes, max_dimension=1280)

            filename = img.get("filename", f"plant_image_{idx+1}.jpg")
            organ = img.get("organ", "auto")

            files.append(("images", (filename, processed_bytes, "image/jpeg")))
            data.append(("organs", organ))

        t_prep_end = time.time()
        print(f"[IDENTIFY] Image preprocessing: {t_prep_end - t_prep_start:.2f}s")

        if not files:
            return PredictionResponse(
                success=False,
                category="plant",
                provider="plantnet",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="INVALID_IMAGE", message="No valid plant images were provided for identification.")
            )

        try:
            session = get_http_session()
            t_api_start = time.time()
            print("[IDENTIFY] External API/model call started")
            response = session.post(url, files=files, data=data, timeout=10)
            t_api_end = time.time()
            print(f"[IDENTIFY] External API/model call completed: {t_api_end - t_api_start:.2f}s (Status: {response.status_code})")


            if response.status_code in (401, 403):
                fallback_res = self.fallback_provider.identify(images, category="plant", location=location)
                if fallback_res.success:
                    return fallback_res

                return PredictionResponse(
                    success=False,
                    category="plant",
                    provider="plantnet",
                    identification_status="IDENTIFICATION_UNAVAILABLE",
                    predictions=[],
                    error=ErrorDetail(code="PLANT_PROVIDER_AUTH_FAILED", message="Pl@ntNet API key authentication failed. Please verify PLANTNET_API_KEY in backend/.env.")
                )

            if response.status_code == 429:
                fallback_res = self.fallback_provider.identify(images, category="plant", location=location)
                if fallback_res.success:
                    return fallback_res

                return PredictionResponse(
                    success=False,
                    category="plant",
                    provider="plantnet",
                    identification_status="IDENTIFICATION_UNAVAILABLE",
                    predictions=[],
                    error=ErrorDetail(code="API_QUOTA_EXCEEDED", message="Pl@ntNet API request quota exceeded.")
                )

            response.raise_for_status()
            res_data = response.json()

            results = res_data.get("results", [])
            predictions = []

            for idx, res in enumerate(results[:5], start=1):
                score = float(res.get("score", 0.0))
                normalized_score = normalize_confidence(score)

                species_info = res.get("species", {})
                scientific_name = species_info.get("scientificNameWithoutAuthor") or species_info.get("scientificName", "Unknown plant species")

                c_names = species_info.get("commonNames", [])
                common_list = c_names if isinstance(c_names, list) else [c_names] if c_names else []

                predictions.append(
                    PredictionItem(
                        rank=idx,
                        scientific_name=scientific_name,
                        common_names=common_list,
                        confidence=normalized_score,
                        taxonomic_rank="species"
                    )
                )

            # Determine confidence status rating based on top candidate
            top_score = predictions[0].confidence if predictions else 0.0
            if top_score >= 0.80:
                ident_status = "HIGH_CONFIDENCE"
            elif top_score >= 0.50:
                ident_status = "MEDIUM_CONFIDENCE"
            else:
                ident_status = "LOW_CONFIDENCE"

            # If Pl@ntNet prediction score is low (< 0.50), attempt fallback provider
            if ident_status == "LOW_CONFIDENCE":
                fallback_res = self.fallback_provider.identify(images, category="plant", location=location)
                if fallback_res.success and fallback_res.predictions and fallback_res.predictions[0].confidence > top_score:
                    return fallback_res

            return PredictionResponse(
                success=True,
                category="plant",
                provider="plantnet",
                model_name="Pl@ntNet Floral AI Engine",
                model_version=res_data.get("version", "v2"),
                identification_status=ident_status,
                predictions=predictions,
                is_mock=False
            )

        except requests.exceptions.Timeout:
            fallback_res = self.fallback_provider.identify(images, category="plant", location=location)
            if fallback_res.success:
                return fallback_res

            return PredictionResponse(
                success=False,
                category="plant",
                provider="plantnet",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="PLANT_PROVIDER_UNAVAILABLE", message="Pl@ntNet API service timed out.")
            )
        except requests.exceptions.RequestException as exc:
            fallback_res = self.fallback_provider.identify(images, category="plant", location=location)
            if fallback_res.success:
                return fallback_res

            return PredictionResponse(
                success=False,
                category="plant",
                provider="plantnet",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="IDENTIFICATION_FAILED", message=f"Pl@ntNet API network error: {str(exc)}")
            )
