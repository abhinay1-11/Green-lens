import io
import hashlib
from typing import Tuple
from PIL import Image, ImageOps
from fastapi import HTTPException, status

ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def validate_image_file(file_content: bytes, filename: str, mime_type: str) -> Tuple[int, int, str]:
    """
    Validates uploaded image file bytes against MIME type, size limit, and Pillow decoding.
    Returns: (width, height, sha256_checksum)
    Raises HTTPException(400) on invalid file.
    """
    # 1. Empty file check
    if not file_content or len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "Uploaded file is empty."}
        )

    # 2. File size check
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "FILE_TOO_LARGE", "message": "File exceeds maximum size limit of 10MB."}
        )

    # 3. Extension check
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_FILE", "message": f"Unsupported file extension '{ext}'."}
        )

    # 4. MIME type check
    if mime_type and mime_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_IMAGE", "message": f"Invalid MIME type '{mime_type}'."}
        )

    # 5. Pillow decode check & dimension check
    try:
        image = Image.open(io.BytesIO(file_content))
        image.verify()  # Verify header integrity
        
        # Re-open after verify() to read size dimensions
        image = Image.open(io.BytesIO(file_content))
        width, height = image.size
        
        if width == 0 or height == 0:
            raise ValueError("Zero dimension image")

        # Minimum dimension check for reliable identification
        if width < 100 or height < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "IMAGE_TOO_SMALL", "message": "Image dimensions are too small for reliable identification (minimum 100x100px required)."}
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_IMAGE", "message": "File appears corrupted or is not a valid image."}
        )

    # 6. Calculate checksum
    checksum = hashlib.sha256(file_content).hexdigest()

    return width, height, checksum


def preprocess_image_for_model(file_bytes: bytes, max_dimension: int = 1280) -> bytes:
    """
    Applies model-specific image preprocessing:
    - Auto-corrects EXIF rotation (camera orientation)
    - Converts RGBA/P/CMYK to RGB format
    - Resizes long side to max_dimension (e.g., 1280px) preserving aspect ratio
    - Re-encodes to high quality JPEG bytes
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        
        # 1. EXIF rotation transpose
        img = ImageOps.exif_transpose(img)

        # 2. RGB conversion
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 3. Resize if long edge > max_dimension
        w, h = img.size
        if max(w, h) > max_dimension:
            if w >= h:
                new_w = max_dimension
                new_h = int(h * (max_dimension / w))
            else:
                new_h = max_dimension
                new_w = int(w * (max_dimension / h))
            
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 4. Save to optimized JPEG buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    except Exception as exc:
        print(f"Warning: Image preprocessing error: {exc}")
        return file_bytes
