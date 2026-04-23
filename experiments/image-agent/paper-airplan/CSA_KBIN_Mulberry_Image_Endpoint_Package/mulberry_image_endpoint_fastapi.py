from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from pathlib import Path

app = FastAPI(title="Mulberry Image Endpoint Sample", version="0.1")

ROOT = Path(__file__).resolve().parent
BRAND_REGISTRY = json.loads((ROOT / "brand_registry.json").read_text(encoding="utf-8"))
INTENT_DICTIONARY = json.loads((ROOT / "intent_dictionary.json").read_text(encoding="utf-8"))

class OCRPayload(BaseModel):
    brand_id: str
    extracted_text: str
    text_confidence: Optional[float] = 1.0
    metadata: Optional[Dict[str, Any]] = None

def find_brand(brand_id: str):
    for brand in BRAND_REGISTRY["brands"]:
        if brand["brand_id"] == brand_id:
            return brand
    return None

def infer_intent(text: str):
    low = text.lower()
    scored = []
    for intent_name, intent_def in INTENT_DICTIONARY["intents"].items():
        matches = sum(1 for kw in intent_def["keywords"] if kw.lower() in low)
        if matches > 0:
            scored.append((matches, intent_name, intent_def))
    scored.sort(reverse=True, key=lambda x: x[0])
    if scored:
        return {
            "intent": scored[0][1],
            "agent": scored[0][2]["agent"],
            "functions": scored[0][2]["functions"],
            "score": scored[0][0]
        }
    return {"intent": "unknown", "agent": None, "functions": [], "score": 0}

@app.get("/")
def root():
    return {"service": "Mulberry Image Endpoint Sample", "status": "ok"}

@app.post("/v1/intent/resolve")
def resolve_intent(payload: OCRPayload):
    brand = find_brand(payload.brand_id)
    if not brand:
        return {"status": "error", "reason": "brand_not_registered"}

    if payload.text_confidence < brand["verification"]["text_confidence_min"]:
        return {"status": "error", "reason": "low_text_confidence"}

    inferred = infer_intent(payload.extracted_text)

    if inferred["intent"] == "unknown":
        return {
            "status": "ok",
            "brand_id": payload.brand_id,
            "resolved": False,
            "intent": "unknown",
            "agent": brand["default_agent"],
            "functions": brand["default_functions"],
            "note": "fallback to brand default"
        }

    if inferred["intent"] not in brand["allowed_intents"]:
        return {
            "status": "error",
            "reason": "intent_not_allowed_for_brand",
            "intent": inferred["intent"]
        }

    return {
        "status": "ok",
        "brand_id": payload.brand_id,
        "resolved": True,
        "intent": inferred["intent"],
        "agent": inferred["agent"],
        "functions": inferred["functions"],
        "brand_endpoint": brand["endpoint"]
    }

@app.post("/v1/intent/execute")
def execute_intent(payload: OCRPayload):
    resolved = resolve_intent(payload)
    if resolved.get("status") != "ok":
        return resolved
    return {
        **resolved,
        "execution": {
            "mode": "sample",
            "message": f"Agent {resolved['agent']} would execute {resolved['functions']}"
        }
    }