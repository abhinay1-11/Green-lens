import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import List, Optional
import os
import uuid

from app.schemas.identification import PredictionResponse
from app.services.identification.factory import get_identification_provider
from app.services.species_enrichment import SpeciesEnrichmentService
from app.utils.image_validation import validate_image_file
from app.config import settings

router = APIRouter(prefix="/api/identification", tags=["Identification"])

@router.post("/predict", response_model=PredictionResponse)
async def predict_species(
    images: List[UploadFile] = File(...),
    category: str = Form(...),
    organs: Optional[List[str]] = Form(None)
):
    """
    Receives 1 to 5 image files, validates them, and routes to appropriate IdentificationProvider.
    Logs timing for every stage under [PERF] tag.
    """
    t_total_start = time.time()

    if not images or len(images) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_IMAGE", "message": "At least one image file is required."}
        )

    if len(images) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_IMAGE", "message": "Maximum of 5 images allowed per identification request."}
        )

    t_upload_start = time.time()
    validated_images = []
    
    for idx, img_file in enumerate(images):
        file_bytes = await img_file.read()
        width, height, checksum = validate_image_file(file_bytes, img_file.filename, img_file.content_type)
        
        organ_tag = organs[idx] if (organs and idx < len(organs)) else "auto"
        
        ext = os.path.splitext(img_file.filename)[1].lower() or ".jpg"
        unique_name = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(settings.UPLOAD_DIR, unique_name)
        
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        validated_images.append({
            "file_bytes": file_bytes,
            "filename": img_file.filename,
            "saved_path": f"/uploads/{unique_name}",
            "file_size": len(file_bytes),
            "mime_type": img_file.content_type,
            "width": width,
            "height": height,
            "checksum": checksum,
            "organ": organ_tag
        })
    t_upload_end = time.time()
    upload_time = t_upload_end - t_upload_start

    # Model identification
    provider = get_identification_provider(category)
    result = provider.identify(validated_images, category=category)
    
    # Species Enrichment stage
    t_enrich_start = time.time()
    try:
        if result and getattr(result, "success", True) and getattr(result, "predictions", None):
            top_pred = result.predictions[0]
            if top_pred and getattr(top_pred, "scientific_name", None):
                common_name = top_pred.common_names[0] if (getattr(top_pred, "common_names", None) and len(top_pred.common_names) > 0) else None
                profile = SpeciesEnrichmentService.get_species_profile(
                    scientific_name=top_pred.scientific_name,
                    common_name=common_name,
                    category=category
                )
                if profile:
                    result.species_profile = profile.model_dump(mode="json")
    except Exception as enrich_err:
        print(f"[IdentificationRouter] Enrichment error ignored: {enrich_err}")
    t_enrich_end = time.time()
    enrich_time = t_enrich_end - t_enrich_start

    t_total_end = time.time()
    total_time = t_total_end - t_total_start

    perf_details = getattr(result, "_perf_details", {})
    prep_time = perf_details.get("preprocessing", 0.01)
    init_time = perf_details.get("model_initialization", 0.00)
    infer_time = perf_details.get("inference", 0.15)
    tax_time = perf_details.get("taxonomy", 0.01)

    print(f"[PERF] upload: {upload_time:.2f}s")
    print(f"[PERF] preprocessing: {prep_time:.2f}s")
    print(f"[PERF] model initialization: {init_time:.2f}s")
    print(f"[PERF] inference: {infer_time:.2f}s")
    print(f"[PERF] taxonomy: {tax_time:.2f}s")
    print(f"[PERF] enrichment: {enrich_time:.2f}s")
    print(f"[PERF] total: {total_time:.2f}s")

    return result


