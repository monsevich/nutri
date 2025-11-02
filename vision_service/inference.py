import io
from functools import lru_cache
from typing import Tuple

import torch
from PIL import Image
from torchvision import models


_LABEL_MAPPING = {
    "plate": "гречка с курицей",
    "chicken": "гречка с курицей",
    "broccoli": "рыба с овощами",
    "spaghetti squash": "паста болоньезе",
    "cup": "овсянка с ягодами",
    "sandwich": "бутерброд с сыром",
    "borsch": "борщ",
    "ice lolly": "сырники",
    "rice": "плов",
    "dumpling": "вареники с картошкой",
    "salad": "салат огурцы-помидоры",
}


def _load_model():
    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)
    model.eval()
    return model, weights.transforms(), weights


@lru_cache
def _model_and_transform():
    return _load_model()


def classify(image_bytes: bytes) -> Tuple[str, float]:
    model, transform, weights = _model_and_transform()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model(tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probabilities, dim=1)
    categories = weights.meta.get("categories", [])
    raw_label = categories[predicted_idx.item()] if predicted_idx.item() < len(categories) else "plate"
    human_label = _LABEL_MAPPING.get(raw_label, "гречка с курицей")
    return human_label, confidence.item()
