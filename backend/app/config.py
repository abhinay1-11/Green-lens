import os
from pydantic_settings import BaseSettings, SettingsConfigDict

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = os.path.dirname(backend_dir)

env_paths = [
    os.path.join(backend_dir, ".env"),
    os.path.join(root_dir, ".env")
]

class Settings(BaseSettings):
    APP_NAME: str = "GreenLens API"
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key"
    
    # Database URL
    DATABASE_URL: str = "sqlite:///./greenlens.db"
    
    # Global Identification Mode: 'real' (strict) or 'mock' (dev demo only)
    IDENTIFICATION_MODE: str = "real"
    
    # Identification Provider Selection
    PLANT_IDENTIFICATION_PROVIDER: str = "plantnet" # plantnet, mock
    PLANTNET_API_KEY: str = ""
    
    BIRD_IDENTIFICATION_PROVIDER: str = "local_onnx"   # local_onnx, bioclip, mock
    BIRD_MIN_CONFIDENCE: float = 0.30
    BIRD_PROVIDER_API_KEY: str = ""
    
    INSECT_IDENTIFICATION_PROVIDER: str = "local_ai"   # local_ai, bioclip, mock
    INSECT_PROVIDER_API_KEY: str = ""
    
    # Hugging Face Token (optional)
    HF_TOKEN: str = ""
    
    # Upload limits & directories
    MAX_UPLOAD_MB: int = 10
    UPLOAD_DIR: str = os.path.abspath(os.path.join(backend_dir, "uploads"))
    
    # Spatial boundary settings
    CAMPUS_NAME: str = "General Monitoring Area"
    CAMPUS_BOUNDARY_FILE: str = os.path.abspath(os.path.join(root_dir, "data", "campus", "campus_boundary.geojson"))

    model_config = SettingsConfigDict(env_file=env_paths, extra="ignore")

    @property
    def clean_plantnet_api_key(self) -> str:
        """Returns sanitized PLANTNET_API_KEY with whitespace and quotes stripped."""
        if not self.PLANTNET_API_KEY:
            return ""
        key = self.PLANTNET_API_KEY.strip().strip("'").strip('"')
        return key

settings = Settings()
