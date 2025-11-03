"""Lightweight inference utilities for local development.

This module intentionally avoids heavy ML dependencies. Instead of loading a
neural network, we return a deterministic stub classification based on simple
image statistics. The goal is to keep the local Docker environment fast and
self-contained.
"""

from __future__ import annotations

import io
from typing import Tuple

import numpy as np
from PIL import Image


_DEFAULT_LABEL = "гречка с курицей"
_LABELS = {
    "light": ("салат огурцы-помидоры", 0.7),
    "medium": ("гречка с курицей", 0.8),
    "dark": ("плов", 0.75),
}


def _average_brightness(image: Image.Image) -> float:
    """Return the average brightness (0-255) of an RGB image."""

    # Convert to numpy array once — Pillow keeps it lazy otherwise.
    array = np.asarray(image, dtype=np.float32)
    # Average over RGB channels and all pixels.
    return float(array.mean())


def classify(image_bytes: bytes) -> Tuple[str, float]:
    """Return a stub classification for the provided image bytes.

    The function reads the image, estimates its brightness and returns a
    pre-defined food label with a pseudo confidence score. When the input is
    invalid, it falls back to a default label.
    """

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return _DEFAULT_LABEL, 0.5

    brightness = _average_brightness(image)
    if brightness < 85:
        label, confidence = _LABELS["dark"]
    elif brightness < 170:
        label, confidence = _LABELS["medium"]
    else:
        label, confidence = _LABELS["light"]
    return label, confidence
