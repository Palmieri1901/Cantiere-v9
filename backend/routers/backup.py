"""Backup generale JSON + restore: include TUTTI i settori dell'app
(rimessaggio, tariffe, cantiere, magazzino, tubolari, Suzuki, gommoni GEB con PDF omologazione, DDT e rubrica).
Le credenziali (users, token) NON sono incluse.
"""
import base64
import json as _json
from datetime import datetime, timezone
from typing import Dict, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from pydantic import BaseModel, ConfigDict

from database import db

router = APIRouter()

BACKUP_VERSION = 3
EXCLUDED = {"users", "password_reset_tokens"}
GRIDFS_BUCKETS = {"gommoni_omologazioni": "PDF omologazione gommoni"}

SETTORI: Dict[str, List[str]] = {
    "Cantiere e tariffe": ["cantiere", "tariffe", "app_settings"],
    "Rimessaggio": ["clienti", "lavori"],
    "Magazzino": ["articoli", "fornitori", "ricarichi_categoria", "spese_accessorie", "movimenti_magazzino"],
    "Tubolari": ["tubolari_config", "preventivi_tubolari"],
    "Suzuki": ["suzuki_modelli", "suzuki_preventivi", "suzuki_legenda", "suzuki_settings"],
    "Gommoni GEB": ["gommoni_modelli", "gommoni_accessori", "gommoni_settings", "gommoni_preventivi"],
    "DDT": ["ddt", "ddt_indirizzi"],
    "Dipendenti e app": ["dipendenti", "lavori_pending", "clienti_esterni", "preventivi_esterni"],
    "Documenti di servizio": ["documenti_servizio"],
}

# collezioni "singleton" del vecchio formato v2 (dict invece di lista)
_LEGACY_SINGLE = {"cantiere", "tariffe"}


def _is_gridfs(name: str) -> bool:
    return any(name.startswith(b + ".") for b in GRIDFS_BUCKETS)


async def _dump_gridfs(bucket_name: str) -> List[dict]:
    bucket = AsyncIOMotorGridFSBucket(db, bucket_name=bucket_name)
    out = []
    async for f in bucket.find({}):
        stream = await bucket.open_download_stream(f._id)
        data = await stream.read()
        out.append({"_id": str(f._id), "filename": f.filename, "metadata": f.metadata or {}, "data_b64": base64.b64encode(data).decode("ascii")})
    return out


@router.get("/backup/ultimo")
async def ultimo_backup():
    """Data dell'ultimo backup scaricato e giorni trascorsi (None se mai eseguito)."""
    doc = await db.app_settings.find_one({"id": "backup_info"}, {"_id": 0}) or {}
    ts = doc.get("ultimo_backup")
    giorni = None
    if ts:
        try:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            giorni = (datetime.now(timezone.utc) - dt).days
        except ValueError:
            ts = None
    return {"ultimo_backup": ts, "giorni": giorni, "scaduto": ts is None or (giorni or 0) >= 7}


@router.get("/backup")
async def backup_data():
    """Esporta TUTTE le collezioni (tranne credenziali) + file GridFS in un unico JSON."""
    names = [n for n in await db.list_collection_names() if n not in EXCLUDED and not _is_gridfs(n)]
    collections: Dict[str, list] = {}
    for n in sorted(names):
        collections[n] = await db[n].find({}, {"_id": 0}).to_list(500000)
    files = {b: await _dump_gridfs(b) for b in GRIDFS_BUCKETS}
    payload = {
        "version": BACKUP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "app": "GEB Cantiere Nautico",
        "settori": SETTORI,
        "counts": {n: len(v) for n, v in collections.items()},
        "files_counts": {b: len(v) for b, v in files.items()},
        "collections": collections,
        "files": files,
    }
    body = _json.dumps(payload, ensure_ascii=False, default=str)
    await db.app_settings.update_one({"id": "backup_info"}, {"$set": {"ultimo_backup": payload["generated_at"]}}, upsert=True)
    filename = f"backup_geb_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(iter([body]), media_type="application/json",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


class RestorePayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    version: int | None = None
    collections: Dict[str, list] | None = None
    files: Dict[str, list] | None = None


def _legacy_collections(payload: RestorePayload) -> Dict[str, list]:
    """Converte un backup v1/v2 (chiavi top-level) nel formato collections."""
    extra = payload.model_extra or {}
    out: Dict[str, list] = {}
    for k, v in extra.items():
        if k in ("generated_at", "app", "counts", "settori", "files_counts"):
            continue
        if k in _LEGACY_SINGLE and isinstance(v, dict):
            out[k] = [v]
        elif isinstance(v, list):
            out[k] = v
    return out


@router.post("/restore")
async def restore_data(payload: RestorePayload):
    """Ripristina le collezioni presenti nel file (sovrascrivendole). Le collezioni assenti non vengono toccate."""
    collections = payload.collections if payload.collections is not None else _legacy_collections(payload)
    if not collections and not payload.files:
        raise HTTPException(400, "File di backup non valido: nessuna sezione riconosciuta")
    restored: Dict[str, int] = {}
    for name, docs in collections.items():
        if name in EXCLUDED or _is_gridfs(name) or not isinstance(docs, list):
            continue
        clean = [{k: v for k, v in d.items() if not k.startswith("_")} for d in docs if isinstance(d, dict)]
        await db[name].delete_many({})
        if clean:
            await db[name].insert_many(clean)
        restored[name] = len(clean)
    for bucket_name, files in (payload.files or {}).items():
        if bucket_name not in GRIDFS_BUCKETS or not isinstance(files, list):
            continue
        bucket = AsyncIOMotorGridFSBucket(db, bucket_name=bucket_name)
        await db[f"{bucket_name}.files"].delete_many({})
        await db[f"{bucket_name}.chunks"].delete_many({})
        n = 0
        for f in files:
            try:
                data = base64.b64decode(f.get("data_b64", ""))
                await bucket.upload_from_stream_with_id(ObjectId(f["_id"]), f.get("filename") or "file", data, metadata=f.get("metadata") or {})
                n += 1
            except Exception:
                continue
        restored[f"{bucket_name} (file)"] = n
    return {"ok": True, "restored": restored}
