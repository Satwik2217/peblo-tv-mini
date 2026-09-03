from typing import Dict, Any
from io import BytesIO
from PIL import Image


ARTWORK_SPECS = {
    "poster": {"aspect_ratio": 2 / 3, "target_width": 600, "target_height": 900, "max_kb": 200, "aspect_label": "2:3"},
    "banner": {"aspect_ratio": 16 / 9, "target_width": 1280, "target_height": 720, "max_kb": 200, "aspect_label": "16:9"},
    "thumbnail": {"aspect_ratio": 16 / 9, "target_width": 640, "target_height": 360, "max_kb": 200, "aspect_label": "16:9"},
}

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Tolerance for aspect ratio: 5%
ASPECT_TOLERANCE = 0.05


def validate_artwork(data: bytes, artwork_type: str, filename: str = "") -> Dict[str, Any]:
    errors = []
    warnings = []

    if artwork_type not in ARTWORK_SPECS:
        return {"valid": False, "errors": [f"Unknown artwork type: {artwork_type}"], "width": 0, "height": 0, "file_size": len(data)}

    spec = ARTWORK_SPECS[artwork_type]
    file_size_kb = len(data) / 1024

    # Check file size
    if file_size_kb > spec["max_kb"]:
        errors.append(
            f"File too large: {file_size_kb:.0f} KB. Maximum allowed is {spec['max_kb']} KB."
        )

    # Check image validity and dimensions
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        # Re-open after verify (verify closes the file)
        img = Image.open(BytesIO(data))
        width, height = img.size
    except Exception:
        return {
            "valid": False,
            "errors": ["Invalid image file. Please upload a valid JPEG or PNG image."],
            "width": 0,
            "height": 0,
            "file_size": len(data),
        }

    # Check aspect ratio
    actual_ratio = width / height if height > 0 else 0
    expected_ratio = spec["aspect_ratio"]
    ratio_diff = abs(actual_ratio - expected_ratio) / expected_ratio

    if ratio_diff > ASPECT_TOLERANCE:
        errors.append(
            f"Wrong aspect ratio: {width}×{height}px "
            f"(ratio {actual_ratio:.2f}, expected {spec['aspect_label']} ≈ {expected_ratio:.2f})."
        )

    # Check dimensions (within 50% of target)
    width_diff = abs(width - spec["target_width"]) / spec["target_width"]
    height_diff = abs(height - spec["target_height"]) / spec["target_height"]

    if width_diff > 0.5 or height_diff > 0.5:
        errors.append(
            f"Unexpected dimensions: {width}×{height}px. "
            f"Expected approximately {spec['target_width']}×{spec['target_height']}px."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "width": width,
        "height": height,
        "file_size": len(data),
        "file_size_kb": file_size_kb,
    }


def detect_mime_type(data: bytes, filename: str = "") -> str:
    if data[:3] == b'\xff\xd8\xff':
        return "image/jpeg"
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return "image/webp"
    ext_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, "application/octet-stream")
