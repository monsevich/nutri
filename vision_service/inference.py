"""Torch-based inference utilities for meal classification."""

from __future__ import annotations

import io
from functools import lru_cache
from typing import Dict, Iterable, Tuple

import torch
from PIL import Image
from torch import nn
from torchvision import models
from torchvision.models import EfficientNet_B0_Weights

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


def _load_model() -> Tuple[nn.Module, nn.Module, Tuple[str, ...]]:
    weights = EfficientNet_B0_Weights.DEFAULT
    model = models.efficientnet_b0(weights=weights)
    model.eval()
    transforms = weights.transforms()
    categories = tuple(weights.meta["categories"])
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
