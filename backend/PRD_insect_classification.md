# Insect Classification Pipeline PRD

## 1. Purpose & Vision
The **Insect Identification** feature of GreenLens enables users to capture or upload photos of insects and receive accurate species predictions. After reverting to the **MobileNetV3‑Small (ImageNet‑pretrained)** model, the pipeline offers fast, CPU‑only inference suitable for Render’s Free Tier while maintaining high prediction quality.

## 2. Scope
- **In‑scope**: 
  - Image upload & camera capture handling for insects.
  - Backend API endpoint `POST /api/v1/identification/identify` (insect provider).
  - MobileNetV3‑Small ONNX model loading, preprocessing, inference, taxonomy mapping, confidence handling, and background‑rejection logic.
  - Unified preprocessing for both uploaded files and live camera images.
  - API response schema and UI display of top‑5 predictions.
- **Out‑of‑scope**: Plant, bird, or other classification pipelines, UI layout changes, model versioning beyond the MobileNetV3‑Small restoration, database schema changes, deployment infrastructure modifications.

## 3. User Stories
| ID | As a … | I want to … | So that … |
|----|--------|-------------|-----------|
| US‑IN‑001 | User | Upload a photo of an insect (or take one with the camera) | I receive a list of likely species with confidence scores. |
| US‑IN‑002 | User | See a clear indication when the system is uncertain | I can decide whether to trust the result or provide another image. |
| US‑IN‑003 | Developer | The backend must run on a single CPU core with <200 MB RAM | The service stays within Render Free Tier limits. |

## 4. Functional Requirements
1. **Model Selection**
   - Load `mobilev3_small.onnx` (ImageNet‑pretrained) lazily on first request.
   - Use ONNX Runtime (CPU execution provider) with single‑threaded inference.
2. **Pre‑processing** (identical for uploads & camera captures)
   - Apply EXIF orientation.
   - Convert image to RGB.
   - Resize to **224 × 224**.
   - Convert to `float32` and **normalize** using ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.
   - Transpose to shape `(1, 3, 224, 224)` before passing to the model.
3. **Inference**
   - Run softmax on model logits to obtain class probabilities.
   - Return the top‑5 classes with their probabilities.
4. **Taxonomy Mapping**
   - Map selected ImageNet class indices to GreenLens insect taxonomy via `INSECT_TAXONOMY_MAP` defined in `backend/models/insect_taxonomy.json`.
   - If a mapping is missing, fallback to the generic ImageNet label.
5. **Background Rejection**
   - Compute `background_prob = prob["background"]` (if present) else treat as 0.
   - Apply the policy:
     - **Reject** (`NO_INSECT_DETECTED`) when `background_prob >= 0.75` **and** `background_prob - insect_prob >= 0.20`.
   - Otherwise, return insect predictions.
6. **Confidence Handling**
   - **HIGH**: confidence ≥ 0.70
   - **MEDIUM**: 0.40 ≤ confidence < 0.70
   - **LOW**: confidence < 0.40 (display as “Low confidence / uncertain”).
7. **API Contract**
   - **Request**: `multipart/form-data` containing `image` (file) and optional `source` (`upload`|`camera`).
   - **Response** (JSON):
```json
{
  "status": "SUCCESS" | "NO_INSECT_DETECTED" | "IMAGE_TOO_SMALL",
  "predictions": [
    {
      "species_common": "Common Green Lacewing",
      "species_scientific": "Chrysoperla carnea",
      "confidence": 0.8762,
      "confidence_level": "HIGH"
    }
    // up to 5 items
  ],
  "message": "Optional human‑readable info"
}
```
8. **Error Codes**
   - `INVALID_IMAGE`: unsupported format or corrupted file.
   - `IMAGE_TOO_SMALL`: image dimensions < 64 px on either side.
   - `NO_INSECT_DETECTED`: background rejection satisfied.

## 5. Non‑Functional Requirements
| Requirement | Target |
|-------------|--------|
| **Latency** | ≤ 150 ms inference time on a Render Free‑Tier CPU instance (measured on 2 vCPU, 2 GB RAM). |
| **Memory** | ≤ 200 MB total (model + runtime). |
| **Throughput** | ≥ 10 requests / second sustained.
| **Reliability** | 99.5 % uptime of the `/identify` endpoint.
| **Scalability** | Horizontal scaling via Render autoscaling (stateless inference). |
| **Security** | Image files are streamed and never persisted beyond request lifecycle.
| **Compatibility** | Works on Windows development environment, Render Linux hosts, and CPU‑only environments.

## 6. Data Model
- `INSECT_TAXONOMY_MAP` (JSON) – maps ImageNet class IDs to:
  - `common_name`
  - `scientific_name`
  - Optional `gbif_id` for downstream enrichment.
- `PredictionItem` (internal Python dataclass):
  - `species_common: str`
  - `species_scientific: str`
  - `confidence: float`
  - `confidence_level: Literal["HIGH","MEDIUM","LOW"]`

## 7. API Contracts
### POST `/api/v1/identification/identify`
- **Headers**: `Content-Type: multipart/form-data`
- **Body**:
  - `image` – binary image file.
  - `source` – optional string (`upload` or `camera`).
- **Responses**:
  - **200 OK** – JSON payload as defined in §4.7.
  - **400 Bad Request** – JSON `{ "error": "INVALID_IMAGE" }`.
  - **422 Unprocessable Entity** – `{ "error": "IMAGE_TOO_SMALL" }`.
  - **200 OK** with `status: "NO_INSECT_DETECTED"` when background policy triggers.

## 8. User Flow Diagram
```mermaid
flowchart TD
    A[User uploads/captures image] --> B[API receives multipart request]
    B --> C[Apply EXIF orientation & RGB conversion]
    C --> D[Resize to 224x224 & normalize]
    D --> E[Load MobileNetV3‑Small ONNX (lazy)]
    E --> F[Run inference -> class probabilities]
    F --> G[Background rejection logic]
    G -->|Rejected| H[Return NO_INSECT_DETECTED]
    G -->|Accepted| I[Map ImageNet IDs to insect taxonomy]
    I --> J[Select top‑5 predictions]
    J --> K[Attach confidence levels]
    K --> L[Return JSON response]
```

## 9. UI/UX Considerations (Frontend)
- Display **top‑5** predictions with a horizontal bar indicating confidence.
- Use colour coding:
  - Green for HIGH, orange for MEDIUM, red for LOW.
- When `NO_INSECT_DETECTED`, show a friendly message: *“We could not detect an insect in the photo. Please try another image.”*
- Keep existing desktop layout untouched; mobile behaviour is handled by separate responsive CSS (outside this PRD).

## 10. Performance & Load
- **Benchmark** (local Windows dev machine, Intel i7, 2 vCPU Docker container):
  - Model load (first request): ~ 85 ms.
  - Inference per image: ~ 65 ms.
  - Total request latency (including preprocessing): ~ 110 ms.
- **Load Testing**: Simulate 100 concurrent requests – average latency stays under 150 ms, CPU usage peaks at ~70 % of a single core.
- **Scaling Strategy**: Keep the service stateless; Render can spin up additional dynos based on request queue length.

## 11. Validation & Testing
- **Unit Tests** (`tests/test_insect_classifier.py`):
  - Verify preprocessing shape `(1,3,224,224)`.
  - Assert correct softmax output range and sum‑to‑1.
  - Test taxonomy mapping for a subset of ImageNet IDs.
  - Validate background‑rejection thresholds.
- **Integration Tests**:
  - End‑to‑end request with a known insect image (e.g., Green Lacewing) expecting `HIGH` confidence.
  - End‑to‑end request with a background image expecting `NO_INSECT_DETECTED`.
- **Acceptance Criteria**:
  - All tests pass (`pytest -q` → 100 %).
  - Manual QA confirms correct species label and confidence on a set of 20 diverse insect photos.

## 12. Deployment & Monitoring
- **Model Versioning**: Store `mobilev3_small.onnx` under `backend/models/` with semantic version tag in filename (e.g., `mobilev3_small_v1.0.onnx`).
- **Logs**: Emit JSON log entries with fields: `request_id`, `inference_time_ms`, `image_source`, `top_prediction`, `status`.
- **Health Check**: `/healthz` returns `OK` if model is loaded and inference succeeds on a dummy tensor.
- **Alerting**: Trigger alert if average latency > 200 ms over a 5‑minute window.

## 13. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Model drift (ImageNet bias) | Degraded species accuracy over time | Periodic re‑evaluation against curated insect image set; consider future fine‑tuning. |
| Missing taxonomy entries | Users see generic ImageNet labels | Maintain `INSECT_TAXONOMY_MAP` and validate coverage whenever new ImageNet classes are added. |
| Large images causing OOM | Service crash | Enforce maximum upload size (5 MB) and down‑sample before preprocessing. |
| Background‑rejection thresholds too strict | False negatives | Provide configuration file (`backend/config.py`) to adjust thresholds without code change. |

---
*Document version: 1.0 – 2026‑11‑16*
