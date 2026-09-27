"""Client AI vision indipendente dal provider.

Usa GEMINI_API_KEY (Google Gemini diretto, nessuna dipendenza esterna).
"""
import os
from typing import List
import httpx
from fastapi import HTTPException

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _clean(b64: str) -> str:
    return b64.split(",", 1)[-1] if "," in b64 else b64


def _mime(b64: str) -> str:
    head = b64[:12]
    if head.startswith("JVBER"):
        return "application/pdf"
    if head.startswith("iVBOR"):
        return "image/png"
    if head.startswith("UklGR"):
        return "image/webp"
    return "image/jpeg"


async def _gemini_direct(api_key: str, system: str, prompt: str, images: List[str]) -> str:
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    parts = [{"text": prompt}] + [{"inline_data": {"mime_type": _mime(i), "data": i}} for i in images]
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.1},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(GEMINI_URL.format(model=model), params={"key": api_key}, json=body)
    if r.status_code != 200:
        raise HTTPException(502, f"Errore Gemini ({r.status_code}): {r.text[:200]}")
    data = r.json()
    try:
        return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        return ""


async def vision(system: str, prompt: str, images_b64: List[str]) -> str:
    """Analizza una o più immagini/PDF (base64) e restituisce il testo prodotto dal modello."""
    images = [_clean(i) for i in images_b64 if i]
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        return await _gemini_direct(gemini_key, system, prompt, images)
    raise HTTPException(500, "Nessuna chiave AI configurata: imposta GEMINI_API_KEY nel file .env")
