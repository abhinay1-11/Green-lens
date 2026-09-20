# Model Providers & Configuration

GreenLens supports multiple AI model providers for species identification across plants, birds, and insects.

## Supported Providers

### 1. Plant Identification
- **Pl@ntNet (`PlantNetProvider`)**: Primary provider using Pl@ntNet API v2 (`POST /v2/identify/all`). Requires `PLANTNET_API_KEY` in backend `.env`. Supports up to 5 images per request with organ tags (`flower`, `leaf`, `fruit`, `bark`, `auto`).
- **Mock Engine (`MockProvider`)**: Default fallback provider for offline development.

### 2. Bird Identification
- **Bird Engine (`BirdProvider`)**: Configurable bird identification provider with mock fallback.

### 3. Insect Identification
- **Insect Engine (`InsectProvider`)**: Configurable insect identification provider with mock fallback.

## Configuring Pl@ntNet API Key
1. Sign up at [my.plantnet.org](https://my.plantnet.org/signup).
2. Retrieve your private API key.
3. Set `PLANTNET_API_KEY=your_key_here` and `PLANT_IDENTIFICATION_PROVIDER=plantnet` in `backend/.env`.
4. Restart the backend server.
