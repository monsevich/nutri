"""Torch-based inference utilities for meal classification."""

from __future__ import annotations

import io
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Tuple
from urllib.parse import urlparse

import torch
from PIL import Image
from torch import nn
from torchvision import models
from torchvision.models import EfficientNet_B0_Weights

logger = logging.getLogger(__name__)

_DEFAULT_LABEL = "гречка с курицей"

_LABEL_KEYWORDS: Dict[str, Iterable[str]] = {
    "салат огурцы-помидоры": ("salad", "lettuce", "cucumber", "tomato"),
    "гречка с курицей": ("chicken", "rice", "pilaf", "meat"),
    "паста болоньезе": ("pasta", "spaghetti", "noodle"),
    "бутерброд с сыром": ("sandwich", "cheeseburger", "cheese"),
    "овсянка с ягодами": ("oatmeal", "porridge", "berry"),
    "борщ": ("borsch", "soup", "broth"),
    "сырники": ("pancake", "fritter", "cheesecake"),
    "рыба с овощами": ("salmon", "fish", "vegetable"),
    "плов": ("pilaf", "paella", "rice"),
    "вареники с картошкой": ("dumpling", "pierogi", "gyoza"),
}


_TORCH_CACHE_DIR = Path("/root/.cache/torch/hub/checkpoints")


def _remove_cached_weights(weights: EfficientNet_B0_Weights) -> Path | None:
    """Delete a cached weights file if it exists."""

    try:
        weight_url = weights.url
        filename = Path(urlparse(weight_url).path).name if weight_url else ""
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Failed to resolve EfficientNet weight cache filename.")
        return None

    if not filename:
        return None

    cached_path = _TORCH_CACHE_DIR / filename
    if cached_path.exists():
        try:
            cached_path.unlink()
            logger.info("Removed cached EfficientNet weights: %s", cached_path)
            return cached_path
        except OSError:
            logger.exception(
                "Could not remove cached EfficientNet weights: %s", cached_path
            )
    return None


def _build_model(weights: EfficientNet_B0_Weights, *, check_hash: bool) -> nn.Module:
    state_dict = weights.get_state_dict(progress=True, check_hash=check_hash)
    model = models.efficientnet_b0(weights=None)
    model.load_state_dict(state_dict)
    return model


def _load_model() -> Tuple[nn.Module, nn.Module, Tuple[str, ...]]:
    weights = EfficientNet_B0_Weights.DEFAULT
    transforms = weights.transforms()
    categories = tuple(weights.meta["categories"])

    try:
        model = _build_model(weights, check_hash=True)
    except Exception as exc:
        logger.warning("Failed to load EfficientNet weights: %s", exc)
        _remove_cached_weights(weights)
        try:
            model = _build_model(weights, check_hash=True)
        except Exception as retry_exc:
            logger.error(
                "Retrying EfficientNet weight download failed: %s", retry_exc
            )
            try:
                model = _build_model(weights, check_hash=False)
                logger.warning(
                    "Loaded EfficientNet weights without hash verification."
                )
            except Exception as final_exc:
                logger.exception(
                    "Failed to load EfficientNet weights even without hash check."
                )
                model = models.efficientnet_b0(weights=None)
                logger.warning(
                    "Using randomly initialised EfficientNet weights as a fallback; "
                    "inference results may be unreliable."
                )

    model.eval()
    return model, transforms, categories


@lru_cache(maxsize=1)
def _get_inference_objects() -> Tuple[nn.Module, nn.Module, Tuple[str, ...]]:
    model, transforms, categories = _load_model()
    model.to(torch.device("cpu"))
    return model, transforms, categories


def _match_label(category_name: str) -> str | None:
    name = category_name.lower()
    for label, keywords in _LABEL_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return label
    return None


def classify(image_bytes: bytes) -> Tuple[str, float]:
    """Classify the meal on the image using a pretrained EfficientNet model."""

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return _DEFAULT_LABEL, 0.0

    model, transforms, categories = _get_inference_objects()
    input_tensor = transforms(image).unsqueeze(0)

    with torch.no_grad():
        logits = model(input_tensor)
        probabilities = torch.softmax(logits[0], dim=0)

    top_probs, top_indices = torch.topk(probabilities, k=5)

    best_label = _DEFAULT_LABEL
    best_prob = top_probs[0].item()

    for score, index in zip(top_probs.tolist(), top_indices.tolist()):
        label_candidate = _match_label(categories[index])
        if label_candidate:
            best_label = label_candidate
            best_prob = score
            break

    return best_label, float(best_prob)
