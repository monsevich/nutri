"""Torch-based inference utilities for meal classification."""

import os
import json
import hashlib
import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Dict

import torch
from torchvision import transforms, models
from PIL import Image, UnidentifiedImageError
from io import BytesIO

from torchvision.models import EfficientNet_B0_Weights

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vision_service")

# --- Пути и настройки модели ---
BASE_DIR = os.path.dirname(__file__)
LABELS_FILE = os.path.join(BASE_DIR, "nutrition_db.json")
MODEL_CACHE_DIR = os.path.expanduser("~/.cache/vision_service")
MODEL_FILE = os.path.join(MODEL_CACHE_DIR, "efficientnet_b0_rwightman-7f5810bc.pth")
MODEL_URL = "https://download.pytorch.org/models/efficientnet_b0_rwightman-7f5810bc.pth"
MODEL_HASH = "7f5810bc"

os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# --- Хеширование файла ---
def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# --- Проверка и скачивание весов ---
def _verify_or_download_weights():
    from torch.hub import download_url_to_file
    if os.path.exists(MODEL_FILE):
        digest = _sha256(MODEL_FILE)
        if MODEL_HASH in digest:
            return
        try:
            os.remove(MODEL_FILE)
        except OSError:
            logger.warning("Не удалось удалить повреждённый файл модели")
    tmp = MODEL_FILE + ".tmp"
    download_url_to_file(MODEL_URL, tmp, hash_prefix=MODEL_HASH)
    os.replace(tmp, MODEL_FILE)
    logger.info("Вес модели загружен и проверен")

# --- Загрузка модели и меток с кэшированием ---
@lru_cache(maxsize=1)
def _load_model():
    # --- Загрузка меток ---
    try:
        with open(LABELS_FILE, "r", encoding="utf-8") as f:
            label_map = json.load(f)
        if not isinstance(label_map, list):
            raise ValueError("nutrition_db.json должен быть списком блюд")
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        logger.error(f"Ошибка загрузки меток: {e}")
        label_map = []

    # --- Проверка весов ---
    _verify_or_download_weights()

    # --- Загрузка модели ---
    model = models.efficientnet_b0(weights=None)
    try:
        state = torch.load(MODEL_FILE, map_location="cpu")
        model.load_state_dict(state)
        model.eval()
    except Exception as e:
        logger.error(f"Ошибка загрузки весов модели: {e}")

    # --- Трансформации изображений ---
    tr = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])

    return model, tr, label_map

# --- Классификация изображения ---
def classify(image_bytes: bytes, topk: int = 3) -> List[dict]:
    model, tr, label_map = _load_model()
    results = []

    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError:
        logger.error("Невозможно открыть изображение")
        return results
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        return results

    x = tr(img).unsqueeze(0)  # (1, C, H, W)

    try:
        with torch.no_grad():
            logits = model(x)
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]
            top = torch.topk(probs, k=min(topk, probs.shape[0]))
    except Exception as e:
        logger.error(f"Ошибка при предсказании модели: {e}")
        return results

    for score, idx in zip(top.values.tolist(), top.indices.tolist()):
        meta = label_map[idx] if idx < len(label_map) else {"name": str(idx), "calories": None}
        results.append({
            "name": meta.get("name"),
            "confidence": float(score),
            "calories": meta.get("calories")
        })

    return results
