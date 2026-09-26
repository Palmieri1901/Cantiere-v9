"""Lavorazioni esterne: clienti non in archivio (solo nominativo) con i relativi lavori."""
import io
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import db
from pdf_builders import build_conto_esterno_pdf, build_preventivo_esterno_pdf

router = APIRouter()


class EsternoIn(BaseModel):
    nome: str
    telefono: Optional[str] = ""
    note: Optional[str] = ""


async def crea_esterno(nome: str, telefono: str = "", note: str = "") -> dict:
    nome = (nome or "").strip()
    if not nome:
        raise HTTPException(400, "Nominativo obbligatorio")
    doc = {"id": str(uuid.uuid4()), "nome": nome, "telefono": telefono or "", "note": note or "",
           "created_at": datetime.now(timezone.utc).isoformat()}
    await db.clienti_esterni.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/esterni")
async def list_esterni():
    docs = await db.clienti_esterni.find({}, {"_id": 0}).sort("nome", 1).to_list(2000)
    ids = [d["id"] for d in docs]
    lavori = await db.lavori.find({"cliente_id": {"$in": ids}}, {"_id": 0, "cliente_id": 1, "costo": 1, "ore": 1, "data": 1}).to_list(10000)
    agg = {}
    for l in lavori:
        a = agg.setdefault(l["cliente_id"], {"n": 0, "totale": 0.0, "ore": 0.0, "ultimo": ""})
        a["n"] += 1
        a["totale"] += float(l.get("costo") or 0)
        a["ore"] += float(l.get("ore") or 0)
        a["ultimo"] = max(a["ultimo"], l.get("data") or "")
    for d in docs:
        d.update(agg.get(d["id"], {"n": 0, "totale": 0.0, "ore": 0.0, "ultimo": ""}))
        d["totale"] = round(d["totale"], 2)
    return docs


@router.post("/esterni")
async def create_esterno(payload: EsternoIn):
    return await crea_esterno(payload.nome, payload.telefono, payload.note)


@router.put("/esterni/{eid}")
async def update_esterno(eid: str, payload: EsternoIn):
    r = await db.clienti_esterni.update_one({"id": eid}, {"$set": {"nome": payload.nome.strip(), "telefono": payload.telefono or "", "note": payload.note or ""}})
    if not r.matched_count:
        raise HTTPException(404, "Cliente esterno non trovato")
    return await db.clienti_esterni.find_one({"id": eid}, {"_id": 0})


@router.delete("/esterni/{eid}")
async def delete_esterno(eid: str):
    """Elimina il cliente esterno e tutti i suoi lavori (ripristinando le giacenze di magazzino)."""
    from routers.lavori import delete_lavoro
    lavori = await db.lavori.find({"cliente_id": eid}, {"_id": 0, "id": 1}).to_list(5000)
    for l in lavori:
        await delete_lavoro(l["id"])
    r = await db.clienti_esterni.delete_one({"id": eid})
    if not r.deleted_count:
        raise HTTPException(404, "Cliente esterno non trovato")
    return {"ok": True, "lavori_eliminati": len(lavori)}


@router.get("/esterni/{eid}/conto.pdf")
async def conto_pdf(eid: str, anno: Optional[int] = None):
    """Conto lavori del cliente esterno (tutti i lavori o solo quelli dell'anno indicato)."""
    est = await db.clienti_esterni.find_one({"id": eid}, {"_id": 0})
    if not est:
        raise HTTPException(404, "Cliente esterno non trovato")
    q = {"cliente_id": eid}
    if anno:
        q["data"] = {"$regex": f"^{anno}"}
    lavori = await db.lavori.find(q, {"_id": 0}).sort("data", 1).to_list(2000)
    cantiere = await db.cantiere.find_one({"id": "default"}, {"_id": 0}) or {}
    pdf = build_conto_esterno_pdf(est, lavori, cantiere, anno)
    fname = f"Conto_{est['nome'].replace(' ', '_')}{f'_{anno}' if anno else ''}.pdf"
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{fname}"'})


# ---------- Preventivi per clienti esterni (con articoli dal magazzino) ----------

class RigaPrev(BaseModel):
    tipo: str = "voce"  # manodopera | articolo | voce
    descrizione: str = ""
    quantita: float = 1
    prezzo_unitario: float = 0
    articolo_id: Optional[str] = None
    codice: Optional[str] = ""


class PreventivoEsternoIn(BaseModel):
    data: Optional[str] = None
    oggetto: Optional[str] = ""
    righe: list[RigaPrev] = []
    sconto_pct: float = 0
    iva_pct: float = 22
    note: Optional[str] = ""
    validita_giorni: int = 30
    stato: Optional[str] = "bozza"


def _calc(p: dict) -> dict:
    imponibile = round(sum(float(r.get("quantita") or 0) * float(r.get("prezzo_unitario") or 0) for r in p.get("righe", [])), 2)
    sconto = round(imponibile * float(p.get("sconto_pct") or 0) / 100, 2)
    netto = round(imponibile - sconto, 2)
    iva = round(netto * float(p.get("iva_pct") or 0) / 100, 2)
    p.update({"imponibile": imponibile, "sconto": sconto, "netto": netto, "iva": iva, "totale": round(netto + iva, 2)})
    return p


@router.get("/esterni/{eid}/preventivi")
async def list_preventivi_esterno(eid: str):
    return await db.preventivi_esterni.find({"esterno_id": eid}, {"_id": 0}).sort("numero", -1).to_list(500)


@router.post("/esterni/{eid}/preventivi")
async def create_preventivo_esterno(eid: str, payload: PreventivoEsternoIn):
    est = await db.clienti_esterni.find_one({"id": eid}, {"_id": 0})
    if not est:
        raise HTTPException(404, "Cliente esterno non trovato")
    anno = datetime.now().year
    last = await db.preventivi_esterni.find_one({"anno": anno}, sort=[("numero", -1)])
    doc = _calc({**payload.model_dump(), "id": str(uuid.uuid4()), "esterno_id": eid, "esterno_nome": est["nome"],
                 "anno": anno, "numero": (last or {}).get("numero", 0) + 1,
                 "data": payload.data or datetime.now().strftime("%Y-%m-%d"),
                 "created_at": datetime.now(timezone.utc).isoformat()})
    await db.preventivi_esterni.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/esterni/preventivi/{pid}")
async def update_preventivo_esterno(pid: str, payload: PreventivoEsternoIn):
    old = await db.preventivi_esterni.find_one({"id": pid}, {"_id": 0})
    if not old:
        raise HTTPException(404, "Preventivo non trovato")
    upd = {k: v for k, v in payload.model_dump().items() if v is not None}
    doc = _calc({**old, **upd})
    await db.preventivi_esterni.update_one({"id": pid}, {"$set": doc})
    return doc


@router.delete("/esterni/preventivi/{pid}")
async def delete_preventivo_esterno(pid: str):
    await db.preventivi_esterni.delete_one({"id": pid})
    return {"ok": True}


@router.post("/esterni/preventivi/{pid}/converti")
async def converti_preventivo(pid: str):
    """Accetta il preventivo e crea il lavoro (scaricando gli articoli dal magazzino)."""
    from models import LavoroCreate
    from routers.lavori import create_lavoro
    p = await db.preventivi_esterni.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Preventivo non trovato")
    if p.get("lavoro_id"):
        raise HTTPException(400, "Preventivo già convertito in lavoro")
    righe = p.get("righe", [])
    articoli = [{"articolo_id": r["articolo_id"], "quantita": float(r.get("quantita") or 1), "prezzo_unitario": float(r.get("prezzo_unitario") or 0)}
                for r in righe if r.get("tipo") == "articolo" and r.get("articolo_id")]
    ore = sum(float(r.get("quantita") or 0) for r in righe if r.get("tipo") == "manodopera")
    manodopera_e_voci = round(sum(float(r.get("quantita") or 0) * float(r.get("prezzo_unitario") or 0) for r in righe
                                  if r.get("tipo") != "articolo" or not r.get("articolo_id")), 2)
    sconto_factor = 1 - float(p.get("sconto_pct") or 0) / 100
    descr = p.get("oggetto") or "; ".join(r.get("descrizione", "") for r in righe if r.get("tipo") != "articolo")[:200]
    lavoro = await create_lavoro(LavoroCreate(
        cliente_id=p["esterno_id"], data=datetime.now().strftime("%Y-%m-%d"), tipo="Riparazione",
        descrizione=f"Prev. {p['numero']}/{p['anno']} - {descr}".strip(" -"), costo=round(manodopera_e_voci * sconto_factor, 2),
        ore=ore, stato="completato", articoli_magazzino=articoli or None,
    ))
    await db.preventivi_esterni.update_one({"id": pid}, {"$set": {"stato": "accettato", "lavoro_id": lavoro.id}})
    return lavoro


@router.get("/esterni/preventivi/{pid}/pdf")
async def preventivo_esterno_pdf(pid: str):
    p = await db.preventivi_esterni.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Preventivo non trovato")
    est = await db.clienti_esterni.find_one({"id": p["esterno_id"]}, {"_id": 0}) or {"nome": p.get("esterno_nome", "")}
    cant = await db.cantiere.find_one({"id": "default"}, {"_id": 0}) or {}
    pdf = build_preventivo_esterno_pdf(p, est, cant)
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition": f'inline; filename="Preventivo_{p["numero"]}_{p["anno"]}_{est["nome"].replace(" ", "_")}.pdf"'})
