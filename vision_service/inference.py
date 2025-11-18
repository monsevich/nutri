"""Torch-based inference utilities for meal classification."""

import os
import json
import hashlib
from typing import Tuple, List
from functools import lru_cache

import torch
from torchvision import transforms, models
from PIL import Image
from io import BytesIO



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

BASE_DIR = os.path.dirname(__file__)
LABELS_FILE = os.path.join(BASE_DIR, "labels.json")
MODEL_CACHE_DIR = os.path.expanduser("~/.cache/vision_service")
MODEL_FILE = os.path.join(MODEL_CACHE_DIR, "efficientnet_b0_rwightman-7f5810bc.pth")
MODEL_URL = "https://download.pytorch.org/models/efficientnet_b0_rwightman-7f5810bc.pth"
MODEL_HASH = "7f5810bc"

os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _verify_or_download_weights():
    from torch.hub import download_url_to_file
    if os.path.exists(MODEL_FILE):
        digest = _sha256(MODEL_FILE)
        if MODEL_HASH in digest:
            return
        # corrupted -> remove
        try:
            os.remove(MODEL_FILE)
        except OSError:
            pass
    # download to temp and rename atomically
    tmp = MODEL_FILE + ".tmp"
    download_url_to_file(MODEL_URL, tmp, hash_prefix=MODEL_HASH)
    os.replace(tmp, MODEL_FILE)

@lru_cache(maxsize=1)
def _load_model():
    # load labels
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        label_map = json.load(f)  # expect list of dict { "name": "...", "keywords": [...], "calories": 400 }
    _verify_or_download_weights()
    # load model once
    model = models.efficientnet_b0(weights=None)
    state = torch.load(MODEL_FILE, map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    # transforms
    tr = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])
    return model, tr, label_map

def classify(image_bytes: bytes, topk: int = 3) -> List[dict]:
    model, tr, label_map = _load_model()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    x = tr(img).unsqueeze(0)  # (1, C, H, W)
    with torch.no_grad():
        logits = model(x)
        probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        top = torch.topk(probs, k=min(topk, probs.shape[0]))
    results = []
    # if label_map is a mapping from index->meta, adapt accordingly
    for score, idx in zip(top.values.tolist(), top.indices.tolist()):
        meta = label_map[idx] if isinstance(label_map, list) and idx < len(label_map) else {"name": str(idx)}
        results.append({
            "name": meta.get("name"),
            "confidence": float(score),
            "calories": meta.get("calories")
        })
    return results
