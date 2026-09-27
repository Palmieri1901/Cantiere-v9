"""Modulo Fuoribordo Suzuki: catalogo modelli, sconti, preventivi, PDF."""
import base64
import io
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from database import db
from helpers import serialize
from models import (
    SuzukiModello, SuzukiModelloCreate, SuzukiModelloUpdate,
    SuzukiPreventivo, SuzukiPreventivoCreate,
    SuzukiImportRequest, SuzukiBulkCreate,
    SuzukiLegendaVoce, SuzukiLegendaVoceCreate, SuzukiLegendaVoceUpdate,
)
from routers import suzuki_seed

router = APIRouter(prefix="/suzuki", tags=["Suzuki"])

# ---------------------------------------------------------------------------
# LOGO INTESTAZIONE PDF (personalizzabile dall'utente)
# ---------------------------------------------------------------------------
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
LOGO_PATH = STATIC_DIR / "suzuki_logo.png"
_ALLOWED_LOGO_MIME = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp"}


def _logo_flowable(max_w_mm: float, max_h_mm: float):
    """Restituisce un `Image` reportlab del logo mantenendo le proporzioni, oppure None."""
    if not LOGO_PATH.exists():
        return None
    try:
        from reportlab.lib.units import mm
        from reportlab.platypus import Image as RLImage
        from PIL import Image as PILImage
        with PILImage.open(LOGO_PATH) as im:
            w, h = im.size
        if not w or not h:
            return None
        ratio = w / h
        max_w = max_w_mm * mm
        max_h = max_h_mm * mm
        # scala prima sulla larghezza, poi vincola all'altezza
        target_w = max_w
        target_h = target_w / ratio
        if target_h > max_h:
            target_h = max_h
            target_w = target_h * ratio
        return RLImage(str(LOGO_PATH), width=target_w, height=target_h)
    except Exception:
        return None


@router.get("/logo")
async def get_logo():
    """Serve il logo corrente per il preview in UI (o 404 se non presente)."""
    if not LOGO_PATH.exists():
        raise HTTPException(404, "Logo non impostato")
    return FileResponse(str(LOGO_PATH), media_type="image/png")


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...)):
    """Sostituisce il logo di intestazione dei PDF Suzuki."""
    ctype = (file.content_type or "").lower()
    if ctype not in _ALLOWED_LOGO_MIME:
        raise HTTPException(400, f"Formato non supportato: {ctype}. Usa PNG, JPG o WebP.")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "File troppo grande (max 5 MB).")
    # normalizza sempre in PNG per uniformità
    try:
        from PIL import Image as PILImage
        with PILImage.open(io.BytesIO(data)) as im:
            im = im.convert("RGBA")
            w, h = im.size
            if w > 1600:
                im = im.resize((1600, int(h * 1600 / w)))
            im.save(LOGO_PATH, "PNG", optimize=True)
    except Exception as e:
        raise HTTPException(400, f"Immagine non valida: {e}")
    return {"ok": True, "size": LOGO_PATH.stat().st_size}


@router.delete("/logo")
async def reset_logo():
    """Rimuove il logo personalizzato (i PDF torneranno senza logo)."""
    if LOGO_PATH.exists():
        LOGO_PATH.unlink()
    return {"ok": True}


# ---------------------------------------------------------------------------
# LEGENDA SIGLE (editabile, integrata in ogni PDF)
# ---------------------------------------------------------------------------
GRUPPO_LUNGHEZZA = "Lunghezza piede e avviamento"
GRUPPO_COMANDO = "Comando, tilt e linea"
DEFAULT_LEGENDA = [
    {"sigla": "S", "significato": "corto (mm 381)", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 10},
    {"sigla": "L", "significato": "lungo (mm 508)", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 20},
    {"sigla": "X", "significato": "extra lungo (mm 635)", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 30},
    {"sigla": "XX", "significato": "ultra lungo (mm 762)", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 40},
    {"sigla": "E", "significato": "avviamento elettrico", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 50},
    {"sigla": "R", "significato": "scatola telecomando a paratia / avv. elettrico", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 60},
    {"sigla": "T", "significato": "power trim e tilt", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 70},
    {"sigla": "H", "significato": "barra di guida", "gruppo": GRUPPO_LUNGHEZZA, "ordine": 80},
    {"sigla": "Q", "significato": "tilt a gas", "gruppo": GRUPPO_COMANDO, "ordine": 110},
    {"sigla": "Z", "significato": "versione controrotante", "gruppo": GRUPPO_COMANDO, "ordine": 120},
    {"sigla": "TH", "significato": "tilt, guida a barra", "gruppo": GRUPPO_COMANDO, "ordine": 130},
    {"sigla": "G", "significato": "telecomando elettronico", "gruppo": GRUPPO_COMANDO, "ordine": 140},
    {"sigla": "AP", "significato": "telecomando elettronico, piede selettivo", "gruppo": GRUPPO_COMANDO, "ordine": 150},
    {"sigla": "BARRA", "significato": "barra di guida", "gruppo": GRUPPO_COMANDO, "ordine": 160},
    {"sigla": "SL", "significato": "Stealth Line, colorazione nero mat", "gruppo": GRUPPO_COMANDO, "ordine": 170},
]


async def _seed_legenda_if_empty():
    count = await db.suzuki_legenda.count_documents({})
    if count == 0:
        for v in DEFAULT_LEGENDA:
            voce = SuzukiLegendaVoce(**v)
            await db.suzuki_legenda.insert_one(serialize(voce))


@router.get("/legenda", response_model=List[SuzukiLegendaVoce])
async def list_legenda():
    await _seed_legenda_if_empty()
    docs = await db.suzuki_legenda.find({}, {"_id": 0}).sort([("ordine", 1), ("sigla", 1)]).to_list(500)
    return [SuzukiLegendaVoce(**d) for d in docs]


@router.post("/legenda", response_model=SuzukiLegendaVoce)
async def create_legenda(payload: SuzukiLegendaVoceCreate):
    voce = SuzukiLegendaVoce(**payload.model_dump())
    await db.suzuki_legenda.insert_one(serialize(voce))
    return voce


@router.put("/legenda/{vid}", response_model=SuzukiLegendaVoce)
async def update_legenda(vid: str, payload: SuzukiLegendaVoceUpdate):
    doc = await db.suzuki_legenda.find_one({"id": vid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Voce non trovata")
    upd = {k: v for k, v in payload.model_dump().items() if v is not None}
    upd["updated_at"] = datetime.now(timezone.utc)
    new_doc = {**doc, **upd}
    voce = SuzukiLegendaVoce(**new_doc)
    await db.suzuki_legenda.update_one({"id": vid}, {"$set": serialize(voce)})
    return voce


@router.delete("/legenda/{vid}")
async def delete_legenda(vid: str):
    res = await db.suzuki_legenda.delete_one({"id": vid})
    if res.deleted_count == 0:
        raise HTTPException(404, "Voce non trovata")
    return {"ok": True}


@router.post("/legenda/reset-defaults")
async def reset_legenda_defaults():
    """Ripristina la legenda ai valori originali (elimina tutte le voci correnti)."""
    await db.suzuki_legenda.delete_many({})
    for v in DEFAULT_LEGENDA:
        voce = SuzukiLegendaVoce(**v)
        await db.suzuki_legenda.insert_one(serialize(voce))
    return {"ok": True, "count": len(DEFAULT_LEGENDA)}


# ---------------------------------------------------------------------------
# CONDIZIONI PREVENTIVO (testo modificabile in fondo al PDF preventivo)
# ---------------------------------------------------------------------------
DEFAULT_CONDIZIONI_PREVENTIVO = [
    "Preventivo valido 30 giorni salvo esaurimento scorte.",
    "Consegna e montaggio da concordare. Garanzia ufficiale Suzuki secondo condizioni di casa madre.",
    "Il montaggio comprende collaudo in acqua e primo tagliando come da programma di manutenzione.",
    "Il pagamento avviene: 30% all'ordine, saldo alla consegna del motore.",
]


async def _get_condizioni_preventivo() -> List[str]:
    doc = await db.suzuki_settings.find_one({"id": "condizioni_preventivo"}, {"_id": 0})
    if not doc:
        await db.suzuki_settings.insert_one({
            "id": "condizioni_preventivo",
            "righe": DEFAULT_CONDIZIONI_PREVENTIVO,
            "updated_at": datetime.now(timezone.utc),
        })
        return list(DEFAULT_CONDIZIONI_PREVENTIVO)
    return list(doc.get("righe") or DEFAULT_CONDIZIONI_PREVENTIVO)


class _CondizioniPayload(BaseModel):
    righe: List[str]


@router.get("/condizioni-preventivo")
async def get_condizioni_preventivo():
    return {"righe": await _get_condizioni_preventivo()}


@router.put("/condizioni-preventivo")
async def set_condizioni_preventivo(payload: _CondizioniPayload):
    righe = [r.strip() for r in payload.righe if r and r.strip()]
    await db.suzuki_settings.update_one(
        {"id": "condizioni_preventivo"},
        {"$set": {"righe": righe, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return {"ok": True, "righe": righe}


@router.post("/condizioni-preventivo/reset")
async def reset_condizioni_preventivo():
    await db.suzuki_settings.update_one(
        {"id": "condizioni_preventivo"},
        {"$set": {"righe": list(DEFAULT_CONDIZIONI_PREVENTIVO), "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return {"ok": True, "righe": list(DEFAULT_CONDIZIONI_PREVENTIVO)}


@router.get("/listino-conc-sconti")
async def get_listino_conc_sconti():
    """Ritorna gli ultimi sconti sc1/sc2 usati per il PDF listino concessionario (default 10/5)."""
    doc = await db.suzuki_settings.find_one({"id": "listino_conc_sconti"}, {"_id": 0})
    if not doc:
        return {"sc1": 10.0, "sc2": 5.0}
    return {"sc1": float(doc.get("sc1", 10) or 10), "sc2": float(doc.get("sc2", 5) or 5)}


@router.put("/listino-conc-sconti")
async def save_listino_conc_sconti(payload: dict):
    """Salva gli sconti sc1/sc2 come default per i prossimi listini concessionario."""
    try:
        sc1 = float(payload.get("sc1") or 0)
        sc2 = float(payload.get("sc2") or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, "Sconti non validi")
    if sc1 < 0 or sc1 > 100 or sc2 < 0 or sc2 > 100:
        raise HTTPException(400, "Sconti fuori range (0-100)")
    await db.suzuki_settings.update_one(
        {"id": "listino_conc_sconti"},
        {"$set": {"sc1": sc1, "sc2": sc2, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return {"sc1": sc1, "sc2": sc2}


@router.put("/offerte")
async def save_offerte(payload: dict):
    """Imposta i motori in offerta casa madre. Body: {offerte: {<modello_id>: prezzo_imposto_iva_incl}}.
    I modelli non presenti vengono tolti dall'offerta (prezzo_offerta=0)."""
    offerte = payload.get("offerte") or {}
    if not isinstance(offerte, dict):
        raise HTTPException(400, "offerte deve essere un oggetto")
    clean: Dict[str, float] = {}
    for mid, val in offerte.items():
        try:
            p = float(val or 0)
        except (TypeError, ValueError):
            continue
        if p > 0:
            clean[str(mid)] = p
    contributi = payload.get("contributi") or {}
    now = datetime.now(timezone.utc)
    await db.suzuki_modelli.update_many(
        {"id": {"$nin": list(clean.keys())}, "prezzo_offerta": {"$gt": 0}},
        {"$set": {"prezzo_offerta": 0, "contributo_offerta": 0, "updated_at": now}},
    )
    for mid, p in clean.items():
        try:
            contributo = max(0.0, float(contributi.get(mid) or 0))
        except (TypeError, ValueError):
            contributo = 0.0
        await db.suzuki_modelli.update_one({"id": mid}, {"$set": {"prezzo_offerta": p, "contributo_offerta": contributo, "updated_at": now}})
    return {"count": len(clean), "offerte": clean}


@router.get("/listino-conc-overrides")
async def get_listino_conc_overrides():
    """Ritorna gli override sc1/sc2 salvati per singolo modello + defaults 10/5.
    Struttura: { default_sc1, default_sc2, overrides: { <modello_id>: {sc1, sc2} } }
    """
    defaults = await db.suzuki_settings.find_one({"id": "listino_conc_sconti"}, {"_id": 0}) or {}
    doc = await db.suzuki_settings.find_one({"id": "listino_conc_overrides"}, {"_id": 0}) or {}
    return {
        "default_sc1": float(defaults.get("sc1", 10) or 10),
        "default_sc2": float(defaults.get("sc2", 5) or 5),
        "overrides": doc.get("overrides", {}),
    }


@router.put("/listino-conc-overrides")
async def save_listino_conc_overrides(payload: dict):
    """Salva override sc1/sc2 per modello. Body: {default_sc1, default_sc2, overrides: {id: {sc1, sc2}}}."""
    try:
        default_sc1 = float(payload.get("default_sc1") or 10)
        default_sc2 = float(payload.get("default_sc2") or 5)
    except (TypeError, ValueError):
        raise HTTPException(400, "Sconti default non validi")
    if not (0 <= default_sc1 <= 100 and 0 <= default_sc2 <= 100):
        raise HTTPException(400, "Sconti default fuori range")
    overrides = payload.get("overrides") or {}
    if not isinstance(overrides, dict):
        raise HTTPException(400, "overrides deve essere un oggetto")
    clean: Dict[str, dict] = {}
    for mid, val in overrides.items():
        if not isinstance(val, dict):
            continue
        try:
            s1 = float(val.get("sc1") or 0)
            s2 = float(val.get("sc2") or 0)
        except (TypeError, ValueError):
            continue
        if not (0 <= s1 <= 100 and 0 <= s2 <= 100):
            continue
        clean[str(mid)] = {"sc1": s1, "sc2": s2}
    now = datetime.now(timezone.utc)
    await db.suzuki_settings.update_one(
        {"id": "listino_conc_sconti"},
        {"$set": {"sc1": default_sc1, "sc2": default_sc2, "updated_at": now}},
        upsert=True,
    )
    await db.suzuki_settings.update_one(
        {"id": "listino_conc_overrides"},
        {"$set": {"overrides": clean, "updated_at": now}},
        upsert=True,
    )
    return {"default_sc1": default_sc1, "default_sc2": default_sc2, "overrides": clean}


async def _legenda_flowables(avail_width_mm: float = 182, compact: bool = False):
    """Genera i flowables per stampare la legenda in fondo ai PDF."""
    await _seed_legenda_if_empty()
    voci = await db.suzuki_legenda.find({}, {"_id": 0}).sort([("ordine", 1), ("sigla", 1)]).to_list(500)
    if not voci:
        return []
    from collections import OrderedDict
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    NAVY = colors.HexColor("#0F2A47")
    LIGHT = colors.HexColor("#F2F4F7")
    BORDER = colors.HexColor("#D0D5DD")

    styles = getSampleStyleSheet()
    sz = 7 if compact else 8.5
    sz_h = 8 if compact else 9.5
    st_sig = ParagraphStyle("lg_sig", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=sz, leading=sz + 2)
    st_val = ParagraphStyle("lg_val", parent=styles["Normal"], fontSize=sz, leading=sz + 2)
    st_grp = ParagraphStyle("lg_grp", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=sz_h, leading=sz_h + 2, textColor=colors.white)

    gruppi = OrderedDict()
    for v in voci:
        gruppi.setdefault(v.get("gruppo") or "Legenda sigle", []).append(v)

    aw = avail_width_mm * mm
    sigw = (15 if compact else 18) * mm
    valw = (aw - 2 * sigw) / 2

    out = []
    for gruppo, items in gruppi.items():
        title = f"LEGENDA SIGLE — {gruppo.upper()}"
        header = Table([[Paragraph(title, st_grp)]], colWidths=[aw])
        header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY),
            ("TOPPADDING", (0, 0), (-1, -1), 2 if compact else 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 if compact else 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8 if compact else 10),
        ]))
        out.append(header)
        rows = []
        for i in range(0, len(items), 2):
            left = items[i]
            right = items[i + 1] if i + 1 < len(items) else None
            rows.append([
                Paragraph(left["sigla"], st_sig),
                Paragraph(left["significato"], st_val),
                Paragraph(right["sigla"] if right else "", st_sig),
                Paragraph(right["significato"] if right else "", st_val),
            ])
        t = Table(rows, colWidths=[sigw, valw, sigw, valw])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.3, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.2, BORDER),
            ("BACKGROUND", (0, 0), (0, -1), LIGHT),
            ("BACKGROUND", (2, 0), (2, -1), LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5 if compact else 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5 if compact else 6),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5 if compact else 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 if compact else 2.5),
        ]))
        out.append(t)
        out.append(Spacer(1, 3 if compact else 6))
    return out


# ---------------------------------------------------------------------------
# CRUD MODELLI
# ---------------------------------------------------------------------------
@router.get("/modelli", response_model=List[SuzukiModello])
async def list_modelli(categoria: Optional[str] = None, q: Optional[str] = None):
    query: dict = {}
    if categoria:
        query["categoria"] = categoria
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}
        query["$or"] = [{"modello": rx}, {"codice": rx}, {"note": rx}]
    docs = await db.suzuki_modelli.find(query, {"_id": 0}).sort([("potenza_hp", 1), ("modello", 1)]).to_list(5000)
    result = []
    for d in docs:
        try:
            result.append(SuzukiModello(**d))
        except Exception:
            pass
    return result


@router.get("/modelli/{mid}", response_model=SuzukiModello)
async def get_modello(mid: str):
    doc = await db.suzuki_modelli.find_one({"id": mid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Modello non trovato")
    return SuzukiModello(**doc)


@router.post("/modelli", response_model=SuzukiModello)
async def create_modello(payload: SuzukiModelloCreate):
    if not payload.modello or not payload.modello.strip():
        raise HTTPException(400, "Il nome del modello è obbligatorio")
    m = SuzukiModello(**payload.model_dump())
    await db.suzuki_modelli.insert_one(serialize(m))
    return m


@router.put("/modelli/{mid}", response_model=SuzukiModello)
async def update_modello(mid: str, payload: SuzukiModelloUpdate):
    doc = await db.suzuki_modelli.find_one({"id": mid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Modello non trovato")
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    new_data = {**doc, **updates, "updated_at": datetime.now(timezone.utc)}
    m = SuzukiModello(**new_data)
    await db.suzuki_modelli.update_one({"id": mid}, {"$set": serialize(m)})
    return m


@router.delete("/modelli/{mid}")
async def delete_modello(mid: str):
    res = await db.suzuki_modelli.delete_one({"id": mid})
    if res.deleted_count == 0:
        raise HTTPException(404, "Modello non trovato")
    return {"ok": True}


@router.post("/modelli/bulk", response_model=List[SuzukiModello])
async def bulk_create_modelli(payload: SuzukiBulkCreate):
    """Crea più modelli in una sola chiamata (usato dopo import AI/CSV)."""
    created: List[SuzukiModello] = []
    for row in payload.modelli:
        if not row.modello or not row.modello.strip():
            continue
        m = SuzukiModello(**row.model_dump())
        await db.suzuki_modelli.insert_one(serialize(m))
        created.append(m)
    return created


@router.post("/seed-listino-2025-2026")
async def seed_listino():
    """Popola il DB con i 61 modelli ufficiali del Listino Suzuki Marine 2025-2026
    (prezzo concessionario IVA escl., prezzo pubblico IVA incl., specifiche tecniche).
    Aggiorna quelli esistenti (match per `modello`) e crea i mancanti."""
    rows = suzuki_seed.build_seed_rows()
    created, updated = 0, 0
    for r in rows:
        existing = await db.suzuki_modelli.find_one({"modello": r["modello"]}, {"_id": 0})
        if existing:
            merged = {**existing, **r, "updated_at": datetime.now(timezone.utc)}
            m = SuzukiModello(**merged)
            await db.suzuki_modelli.update_one({"id": existing["id"]}, {"$set": serialize(m)})
            updated += 1
        else:
            m = SuzukiModello(**r)
            await db.suzuki_modelli.insert_one(serialize(m))
            created += 1
    return {"ok": True, "created": created, "updated": updated, "total": len(rows)}


@router.get("/listino.pdf")
async def listino_pdf():
    """PDF listino pubblico (per clienti finali)."""
    return await _build_listino_pdf(concessionario=False)


@router.get("/listino-concessionario.pdf")
async def listino_concessionario_pdf(sc1: float = 10.0, sc2: float = 5.0):
    """PDF listino concessionario. Se esistono override per modello nelle impostazioni li usa,
    altrimenti applica sc1/sc2 uniformi (query param, default 10/5)."""
    return await _build_listino_pdf(concessionario=True, sc1=sc1, sc2=sc2)


async def _build_listino_pdf(concessionario: bool = False, sc1: float = 10.0, sc2: float = 5.0):
    """PDF listino gamma Suzuki Marine, raggruppato per categoria HP.
    Se `concessionario=True` aggiunge colonne Sconto 1, Sconto 2, Netto concessionario,
    % sconto medio (calcolato da pubblico vs listino) e Guadagno stimato applicando sc1+sc2 sul pubblico."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    docs = await db.suzuki_modelli.find({}, {"_id": 0}).sort([("potenza_hp", 1), ("modello", 1)]).to_list(1000)
    if not docs:
        raise HTTPException(400, "Nessun modello in catalogo. Popola prima il listino.")

    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#0F2A47")
    ACCENT = colors.HexColor("#C62828")  # rosso per listino concessionario
    LIGHT = colors.HexColor("#F2F4F7")
    BORDER = colors.HexColor("#D0D5DD")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)

    story = []
    logo = _logo_flowable(max_w_mm=42, max_h_mm=22)
    variante = "Concessionario" if concessionario else "Pubblico"
    title_color = ACCENT if concessionario else NAVY
    header_title = Paragraph(f"<b>SUZUKI MARINE — Listino {variante} 2025-2026</b>",
                             ParagraphStyle("t", parent=styles["Heading1"], fontSize=14, textColor=title_color, spaceAfter=2))
    subtitle_text = ("GEB di Palmieri Sandro · <b>DOCUMENTO RISERVATO CONCESSIONARIO</b>"
                     if concessionario else "GEB di Palmieri Sandro · Concessionario Suzuki Marine")
    header_sub = Paragraph(subtitle_text,
                           ParagraphStyle("s", parent=styles["Normal"], fontSize=9, textColor=colors.grey))
    if logo:
        head = Table([[logo, [header_title, header_sub]]], colWidths=[46*mm, 140*mm])
        head.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        story.append(head)
    else:
        story.append(header_title)
        story.append(header_sub)
    story.append(Spacer(1, 8))

    # Raggruppa per categoria
    gruppi: Dict[str, List[dict]] = {}
    for d in docs:
        gruppi.setdefault(d.get("categoria") or "Altro", []).append(d)
    ordine_cat = ["Portatile", "In-linea 2", "In-linea 3", "In-linea 4", "V6", "V6 Flagship", "Altro"]

    if concessionario:
        head_row = ["Modello", "HP", "Gambo", "Peso",
                    "Listino IVA escl.", "Sc.1", "Sc.2", "Netto conc.",
                    "Pubblico IVA incl.", "% Sc. list.",
                    f"Guadagno ({sc1:g}%+{sc2:g}%)"]
        col_widths = [24*mm, 9*mm, 12*mm, 12*mm, 22*mm, 9*mm, 9*mm, 22*mm, 22*mm, 15*mm, 30*mm]
        font_size = 7.2
    else:
        head_row = ["Modello", "HP", "Cilindrata", "Gambo", "Peso", "Pubblico € (IVA incl.)", "In offerta"]
        col_widths = [40*mm, 14*mm, 22*mm, 22*mm, 18*mm, 40*mm, 30*mm]
        font_size = 8.5

    # aliquota IVA per calcoli (per il listino concessionario)
    iva_perc_pdf = await _get_iva_perc() if concessionario else 22.0
    IVA_M = 1 + (float(iva_perc_pdf) / 100.0)
    # override per-modello caricati dalle impostazioni (se presenti)
    overrides_doc = await db.suzuki_settings.find_one({"id": "listino_conc_overrides"}, {"_id": 0}) if concessionario else None
    overrides_map: Dict[str, dict] = (overrides_doc or {}).get("overrides", {}) if concessionario else {}
    OFFER_BG = colors.HexColor("#FFF3E0")
    OFFER_FG = colors.HexColor("#E65100")
    st_cell_c = ParagraphStyle("cc", parent=styles["Normal"], fontSize=font_size, leading=font_size + 1.5, alignment=TA_CENTER)
    st_cell_r = ParagraphStyle("cr", parent=styles["Normal"], fontSize=font_size, leading=font_size + 1.5, alignment=TA_RIGHT)

    for cat in [c for c in ordine_cat if c in gruppi]:
        rows = sorted(gruppi[cat], key=lambda x: (x.get("potenza_hp") or 0, x.get("modello") or ""))
        story.append(Paragraph(f"<b>{cat.upper()}</b>",
                               ParagraphStyle("cat", parent=styles["Heading3"], fontSize=11, textColor=NAVY, spaceBefore=6, spaceAfter=4)))
        st_head = ParagraphStyle("hd", parent=styles["Normal"], fontName="Helvetica-Bold",
                                 fontSize=font_size, leading=font_size + 1.5,
                                 textColor=colors.white, alignment=TA_CENTER)
        header_paras = [Paragraph(h, st_head) for h in head_row]
        data = [header_paras]
        neg_rows = []
        offer_rows = []
        for row_idx, r in enumerate(rows, start=1):
            offerta = float(r.get("prezzo_offerta") or 0)
            if offerta > 0:
                offer_rows.append(row_idx)
            if concessionario:
                base = [
                    r.get("modello", ""),
                    f"{r.get('potenza_hp',0):g}",
                    r.get("gambo", "") or "—",
                    f"{r.get('peso_kg',0):g} kg" if r.get("peso_kg") else "—",
                ]
            else:
                base = [
                    r.get("modello", ""),
                    f"{r.get('potenza_hp',0):g}",
                    f"{r.get('cilindrata_cc',0):g} cc" if r.get("cilindrata_cc") else "—",
                    r.get("gambo", "") or "—",
                    f"{r.get('peso_kg',0):g} kg" if r.get("peso_kg") else "—",
                ]
            if concessionario:
                pl = float(r.get("prezzo_listino") or 0)
                pub = float(r.get("prezzo_pubblico") or 0)
                # Netto conc. = costo REALE per il concessionario (listino IVA escl. dopo eventuali sconti Suzuki stored)
                s1_mod = float(r.get("sconto_perc_1") or 0)
                s2_mod = float(r.get("sconto_perc_2") or 0)
                netto_conc = pl * (1 - s1_mod/100) * (1 - s2_mod/100) if pl else 0
                if offerta > 0:
                    netto_conc = max(0.0, netto_conc - float(r.get("contributo_offerta") or 0))
                # % sconto listino: da pubblico IVA escl. al listino concessionario
                pub_escl = pub / IVA_M if pub else 0
                sconto_list_perc = ((pub_escl - pl) / pub_escl * 100) if pub_escl > 0 and pl > 0 else 0
                # sconti applicati riga (override per modello se presente, altrimenti uniform sc1/sc2)
                ov = overrides_map.get(str(r.get("id") or ""))
                row_sc1 = float((ov or {}).get("sc1", sc1))
                row_sc2 = float((ov or {}).get("sc2", sc2))
                if offerta > 0:
                    # motore in offerta casa madre: prezzo imposto, sconti bloccati a 0
                    pub = offerta
                    row_sc1 = row_sc2 = 0.0
                    pub_escl = pub / IVA_M
                    sconto_list_perc = ((pub_escl - pl) / pub_escl * 100) if pub_escl > 0 and pl > 0 else 0
                # Guadagno = netto vendita al cliente (row_sc1+row_sc2 sul pubblico) − costo reale (netto conc.)
                netto_vendita_incl = pub * (1 - row_sc1/100) * (1 - row_sc2/100) if pub else 0
                netto_vendita_escl = netto_vendita_incl / IVA_M if netto_vendita_incl else 0
                guadagno = netto_vendita_escl - netto_conc if pl and pub else 0
                if guadagno < 0:
                    neg_rows.append(row_idx)
                if offerta > 0:
                    base[0] = Paragraph(f"<b>{r.get('modello','')}</b><br/><font color='#E65100' size='{font_size-1.2}'>OFFERTA</font>",
                                        ParagraphStyle("mo", parent=styles["Normal"], fontSize=font_size, leading=font_size + 1.5))
                base += [
                    _fmt_eur(pl) if pl else "—",
                    f"{row_sc1:g}%",  # override per modello o default
                    f"{row_sc2:g}%",
                    _fmt_eur(netto_conc) if netto_conc else "—",
                    Paragraph(f"<b>{_fmt_eur(pub)}</b>", st_cell_r) if offerta > 0 else (_fmt_eur(pub) if pub else "—"),
                    f"{sconto_list_perc:.1f}%" if sconto_list_perc > 0 else "—",
                    _fmt_eur(guadagno) if guadagno else "—",
                ]
            else:
                pub = float(r.get("prezzo_pubblico") or 0)
                if offerta > 0:
                    base.append(Paragraph(
                        f"<strike><font color='grey'>{_fmt_eur(pub)}</font></strike>  <b>{_fmt_eur(offerta)}</b>" if pub else f"<b>{_fmt_eur(offerta)}</b>",
                        st_cell_r))
                    base.append(Paragraph("<b>OFFERTA</b>", st_cell_c))
                else:
                    base.append(_fmt_eur(pub) if pub else "—")
                    base.append("—")
            data.append(base)
        t = Table(data, colWidths=col_widths, repeatRows=1)
        style = [
            ("BACKGROUND", (0,0), (-1,0), title_color),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), font_size),
            ("ALIGN", (1,1), (-1,-1), "CENTER"),
            ("ALIGN", (5,1), (-1,-1), "RIGHT"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
            ("GRID", (0,0), (-1,-1), 0.25, BORDER),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 4 if concessionario else 5),
            ("RIGHTPADDING", (0,0), (-1,-1), 4 if concessionario else 5),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]
        if concessionario:
            # evidenzia colonne concessionario
            # colonne: 0 Modello, 1 HP, 2 Gambo, 3 Peso, 4 Listino IVA escl, 5 Sc.1, 6 Sc.2, 7 Netto conc, 8 Pubblico, 9 %Sc.list, 10 Guadagno
            style += [
                ("BACKGROUND", (5, 1), (7, -1), colors.HexColor("#FDECEC")),
                ("TEXTCOLOR", (7, 1), (7, -1), ACCENT),
                ("FONTNAME", (7, 1), (7, -1), "Helvetica-Bold"),
                ("ALIGN", (5, 1), (6, -1), "CENTER"),
                ("BACKGROUND", (9, 1), (10, -1), colors.HexColor("#E8F5E9")),
                ("TEXTCOLOR", (10, 1), (10, -1), colors.HexColor("#1B5E20")),
                ("FONTNAME", (10, 1), (10, -1), "Helvetica-Bold"),
                ("ALIGN", (9, 1), (9, -1), "CENTER"),
            ]
            # Evidenzia righe con guadagno negativo (fondo rosso chiaro, testo rosso su tutta la riga guadagno)
            for ridx in neg_rows:
                style += [
                    ("BACKGROUND", (10, ridx), (10, ridx), colors.HexColor("#FFEBEE")),
                    ("TEXTCOLOR", (10, ridx), (10, ridx), colors.HexColor("#B71C1C")),
                    ("FONTNAME", (10, ridx), (10, ridx), "Helvetica-Bold"),
                ]
            for ridx in offer_rows:
                style += [
                    ("BACKGROUND", (5, ridx), (6, ridx), OFFER_BG),
                    ("TEXTCOLOR", (5, ridx), (6, ridx), OFFER_FG),
                    ("FONTNAME", (5, ridx), (6, ridx), "Helvetica-Bold"),
                    ("BACKGROUND", (8, ridx), (8, ridx), OFFER_BG),
                ]
        else:
            for ridx in offer_rows:
                style += [
                    ("BACKGROUND", (5, ridx), (6, ridx), OFFER_BG),
                    ("TEXTCOLOR", (5, ridx), (6, ridx), OFFER_FG),
                ]
            # evidenzia colonna "In offerta" (rosso su sfondo chiaro)
            style += [
                ("BACKGROUND", (6, 1), (6, -1), colors.HexColor("#FDECEC")),
                ("TEXTCOLOR", (6, 1), (6, -1), ACCENT),
                ("FONTNAME", (6, 1), (6, -1), "Helvetica-Bold"),
            ]
        t.setStyle(TableStyle(style))
        story.append(t)

    story.append(Spacer(1, 8))
    if concessionario:
        disclaimer = (f"<i>Documento riservato al concessionario. Contiene prezzi netti al concessionario "
                      f"dopo applicazione degli sconti Suzuki (Sc.1 e Sc.2). La colonna <b>% Sc. list.</b> mostra "
                      f"lo sconto complessivo dal prezzo pubblico (IVA escl.) al listino concessionario. La colonna "
                      f"<b>Guadagno ({sc1:g}%+{sc2:g}%)</b> stima il margine (IVA escl.) applicando questi due sconti "
                      f"sul prezzo pubblico. I modelli contrassegnati <b>OFFERTA</b> hanno prezzo imposto dalla casa madre: "
                      f"sconti bloccati a 0% e guadagno calcolato sul prezzo imposto. Non consegnare al cliente finale.</i>")
    else:
        disclaimer = ("<i>Prezzi Suzuki Italia validi dal listino 2025-2026 salvo variazioni. "
                      "Il prezzo IVA inclusa è indicativo per il cliente finale; il concessionario applica le proprie condizioni. "
                      "I modelli contrassegnati <b>OFFERTA</b> sono in promozione casa madre al prezzo imposto indicato.</i>")
    story.append(Paragraph(disclaimer,
        ParagraphStyle("note", parent=styles["Normal"], fontSize=8, textColor=colors.grey)))

    # Legenda sigle
    story.append(Spacer(1, 8))
    for f in await _legenda_flowables(avail_width_mm=186, compact=False):
        story.append(f)

    doc.build(story)
    buf.seek(0)
    filename = f"listino_suzuki_{'concessionario' if concessionario else 'pubblico'}_2025-2026.pdf"
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": f'inline; filename="{filename}"'})


@router.get("/caratteristiche.pdf")
async def caratteristiche_pdf():
    """PDF caratteristiche tecniche della gamma Suzuki Marine, raggruppato per categoria."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    docs = await db.suzuki_modelli.find({}, {"_id": 0}).sort([("potenza_hp", 1), ("modello", 1)]).to_list(1000)
    if not docs:
        raise HTTPException(400, "Nessun modello in catalogo. Popola prima il listino.")

    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#0F2A47")
    LIGHT = colors.HexColor("#F2F4F7")
    BORDER = colors.HexColor("#D0D5DD")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=10*mm, rightMargin=10*mm, topMargin=12*mm, bottomMargin=12*mm)

    story = []
    logo = _logo_flowable(max_w_mm=42, max_h_mm=22)
    header_title = Paragraph("<b>SUZUKI MARINE — Caratteristiche Tecniche Gamma 2025-2026</b>",
                             ParagraphStyle("t", parent=styles["Heading1"], fontSize=13, textColor=NAVY, spaceAfter=2))
    header_sub = Paragraph("GEB di Palmieri Sandro · Concessionario Suzuki Marine",
                           ParagraphStyle("s", parent=styles["Normal"], fontSize=9, textColor=colors.grey))
    if logo:
        head = Table([[logo, [header_title, header_sub]]], colWidths=[46*mm, 144*mm])
        head.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        story.append(head)
    else:
        story.append(header_title)
        story.append(header_sub)
    story.append(Spacer(1, 8))

    gruppi: Dict[str, List[dict]] = {}
    for d in docs:
        gruppi.setdefault(d.get("categoria") or "Altro", []).append(d)
    ordine_cat = ["Portatile", "In-linea 2", "In-linea 3", "In-linea 4", "V6", "V6 Flagship", "Altro"]

    for cat in [c for c in ordine_cat if c in gruppi]:
        rows = sorted(gruppi[cat], key=lambda x: (x.get("potenza_hp") or 0, x.get("modello") or ""))
        story.append(Paragraph(f"<b>{cat.upper()}</b>",
                               ParagraphStyle("cat", parent=styles["Heading3"], fontSize=11, textColor=NAVY, spaceBefore=6, spaceAfter=4)))
        head = ["Modello", "HP", "Cilindrata", "Cilindri", "Alimentazione", "Peso", "Gambo", "Carburante"]
        data = [head]
        for r in rows:
            data.append([
                r.get("modello", ""),
                f"{r.get('potenza_hp',0):g}",
                f"{r.get('cilindrata_cc',0):g} cc" if r.get("cilindrata_cc") else "—",
                r.get("cilindri", "") or "—",
                r.get("alimentazione", "") or "—",
                f"{r.get('peso_kg',0):g} kg" if r.get("peso_kg") else "—",
                r.get("gambo", "") or "—",
                r.get("carburante", "") or "—",
            ])
        t = Table(data, colWidths=[30*mm, 11*mm, 21*mm, 40*mm, 32*mm, 15*mm, 20*mm, 21*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 7.8),
            ("ALIGN", (1,1), (2,-1), "CENTER"),
            ("ALIGN", (5,1), (7,-1), "CENTER"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
            ("GRID", (0,0), (-1,-1), 0.25, BORDER),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        story.append(t)

    # Legenda sigle
    story.append(Spacer(1, 8))
    for f in await _legenda_flowables(avail_width_mm=190, compact=False):
        story.append(f)

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": 'inline; filename="caratteristiche_suzuki_2025-2026.pdf"'})


# ---------------------------------------------------------------------------
# IMPORT AI (PDF/immagine listino Suzuki)
# ---------------------------------------------------------------------------
_IMPORT_PROMPT = (
    "Sei un assistente che analizza il listino ufficiale dei fuoribordo SUZUKI in italiano.\n"
    "Estrai la lista di TUTTI i modelli visibili nella pagina fornita.\n"
    "Rispondi SOLO con un array JSON, ogni elemento con le chiavi:\n"
    '  "codice": codice articolo Suzuki se presente (stringa, altrimenti "")\n'
    '  "modello": sigla del motore (es. "DF150ATL", "DF9.9BS")\n'
    '  "potenza_hp": potenza in HP (numero, es. 150)\n'
    '  "cilindrata_cc": cilindrata in cc (numero se presente, altrimenti 0)\n'
    '  "cilindri": es. "4 in linea", "V6" (stringa)\n'
    '  "alimentazione": es. "EFI", "carburatore" (stringa)\n'
    '  "peso_kg": peso in kg (numero se presente, altrimenti 0)\n'
    '  "avviamento": "elettrico", "manuale" oppure "elettrico + manuale"\n'
    '  "gambo": lunghezza gambo ("S", "L", "UL", "XL")\n'
    '  "trim": es. "PT&T", "idraulico", "manuale"\n'
    '  "comandi": "a distanza" o "da barra"\n'
    '  "alternatore_A": ampere alternatore (numero se presente)\n'
    '  "categoria": es. "Portable", "Mid range", "V6" se ricavabile\n'
    '  "prezzo_listino": prezzo in euro IVA esclusa (numero)\n'
    '  "note": eventuali note utili (stringa breve, altrimenti "")\n'
    "Se un dato non è presente nella pagina, usa stringa vuota o 0.\n"
    "NON aggiungere testo prima o dopo il JSON. NON usare fenced code block."
)


async def _run_vision_images(images_b64: List[str]) -> List[dict]:
    """Invia una o più pagine al modello AI e concatena i risultati JSON."""
    from ai_client import vision

    all_rows: List[dict] = []
    for b64 in images_b64:
        text = (await vision(
            "Sei un OCR avanzato specializzato nell'estrazione di dati tecnici "
            "dai listini ufficiali dei motori marini Suzuki. Sei preciso e sintetico.",
            _IMPORT_PROMPT, [b64],
        )).strip()
        parsed = _extract_json_array(text)
        if isinstance(parsed, list):
            all_rows.extend([r for r in parsed if isinstance(r, dict)])
    return all_rows


def _extract_json_array(text: str):
    if not text:
        return None
    m = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    candidate = m.group(1) if m else text
    i = candidate.find("[")
    if i == -1:
        return None
    depth = 0
    for j in range(i, len(candidate)):
        if candidate[j] == "[":
            depth += 1
        elif candidate[j] == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(candidate[i:j+1])
                except Exception:
                    return None
    return None


def _pdf_pages_to_images_b64(pdf_bytes: bytes, max_pages: int = 20) -> List[str]:
    """Renderizza le pagine PDF come PNG base64 usando pymupdf."""
    import pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    images: List[str] = []
    zoom = pymupdf.Matrix(2, 2)  # 2x per leggibilità OCR
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pix = page.get_pixmap(matrix=zoom)
        images.append(base64.b64encode(pix.tobytes("png")).decode("ascii"))
    doc.close()
    return images


@router.post("/import-ai")
async def import_ai(payload: SuzukiImportRequest):
    """Analizza un file (PDF/immagine) in base64 e restituisce la lista dei
    modelli riconosciuti (NON salva ancora nel DB — l'utente conferma prima)."""
    if not payload.file_base64:
        raise HTTPException(400, "File mancante")
    raw = payload.file_base64.split(",", 1)[-1] if "," in payload.file_base64 else payload.file_base64
    try:
        data = base64.b64decode(raw)
    except Exception:
        raise HTTPException(400, "Base64 non valido")

    name_lower = (payload.file_name or "").lower()
    if name_lower.endswith(".pdf") or data[:4] == b"%PDF":
        images = _pdf_pages_to_images_b64(data)
        if not images:
            raise HTTPException(400, "PDF vuoto o non leggibile")
    else:
        # immagine singola
        images = [raw]

    rows = await _run_vision_images(images)
    return {"count": len(rows), "modelli": rows}


# ---------------------------------------------------------------------------
# CRUD PREVENTIVI
# ---------------------------------------------------------------------------
def _calc_totale(p: SuzukiPreventivo, iva_perc: float = 22.0) -> dict:
    IVA = 1 + (float(iva_perc or 0) / 100.0)
    listino = float(p.prezzo_listino or 0)
    s1 = float(p.sconto_perc_1 or 0)
    s2 = float(p.sconto_perc_2 or 0)
    dopo_s1 = listino * (1 - s1 / 100)
    dopo_s2 = dopo_s1 * (1 - s2 / 100)
    netto = round(dopo_s2, 2)
    montaggio = float(p.montaggio or 0)
    cavetteria = float(p.cavetteria or 0)
    totale = round(netto + montaggio + cavetteria, 2)
    acquisto_iva_escl = float(p.prezzo_acquisto_concessionario or 0)
    acquisto_iva_incl = round(acquisto_iva_escl * IVA, 2)
    sotto_costo = acquisto_iva_incl > 0 and netto < acquisto_iva_incl
    margine = round(netto - acquisto_iva_incl, 2) if acquisto_iva_incl > 0 else 0.0
    return {
        "prezzo_listino": listino,
        "importo_sconto_1": round(listino - dopo_s1, 2),
        "importo_sconto_2": round(dopo_s1 - dopo_s2, 2),
        "netto_motore": netto,
        "montaggio": montaggio,
        "cavetteria": cavetteria,
        "totale_iva_esclusa": totale,
        "acquisto_iva_escl": acquisto_iva_escl,
        "acquisto_iva_incl": acquisto_iva_incl,
        "sotto_costo": sotto_costo,
        "margine": margine,
        "iva_perc": float(iva_perc or 0),
    }


async def _get_iva_perc() -> float:
    doc = await db.cantiere.find_one({"id": "default"}, {"iva_percentuale": 1})
    if doc and doc.get("iva_percentuale") is not None:
        try:
            return float(doc["iva_percentuale"])
        except (TypeError, ValueError):
            pass
    return 22.0


async def _next_numero() -> str:
    year = datetime.now().year
    n = await db.suzuki_preventivi.count_documents({"data": {"$regex": f"^{year}-"}})
    return f"S{year}-{n+1:03d}"


@router.get("/preventivi", response_model=List[SuzukiPreventivo])
async def list_preventivi(stato: Optional[str] = None):
    q: dict = {}
    if stato:
        q["stato"] = stato
    docs = await db.suzuki_preventivi.find(q, {"_id": 0}).sort("data", -1).to_list(2000)
    return [SuzukiPreventivo(**d) for d in docs]


@router.get("/preventivi/{pid}", response_model=SuzukiPreventivo)
async def get_preventivo(pid: str):
    doc = await db.suzuki_preventivi.find_one({"id": pid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Preventivo non trovato")
    return SuzukiPreventivo(**doc)


@router.post("/preventivi", response_model=SuzukiPreventivo)
async def create_preventivo(payload: SuzukiPreventivoCreate):
    data = payload.model_dump()
    if not data.get("data"):
        data["data"] = datetime.now(timezone.utc).date().isoformat()
    if not data.get("numero"):
        data["numero"] = await _next_numero()
    prev = SuzukiPreventivo(**data)
    await db.suzuki_preventivi.insert_one(serialize(prev))
    return prev


@router.put("/preventivi/{pid}", response_model=SuzukiPreventivo)
async def update_preventivo(pid: str, payload: SuzukiPreventivoCreate):
    doc = await db.suzuki_preventivi.find_one({"id": pid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Preventivo non trovato")
    data = payload.model_dump()
    new_data = {**doc, **data, "updated_at": datetime.now(timezone.utc)}
    prev = SuzukiPreventivo(**new_data)
    await db.suzuki_preventivi.update_one({"id": pid}, {"$set": serialize(prev)})
    return prev


@router.delete("/preventivi/{pid}")
async def delete_preventivo(pid: str):
    res = await db.suzuki_preventivi.delete_one({"id": pid})
    if res.deleted_count == 0:
        raise HTTPException(404, "Preventivo non trovato")
    return {"ok": True}


@router.post("/preventivi/preview-pdf")
async def preview_pdf(payload: SuzukiPreventivoCreate):
    """Genera un PDF senza salvare il preventivo."""
    data = payload.model_dump()
    if not data.get("data"):
        data["data"] = datetime.now(timezone.utc).date().isoformat()
    if not data.get("numero"):
        data["numero"] = "ANTEPRIMA"
    prev = SuzukiPreventivo(**data)
    pdf_bytes = await _build_pdf(prev)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="anteprima_preventivo.pdf"'},
    )


@router.get("/preventivi/{pid}/pdf")
async def get_preventivo_pdf(pid: str):
    doc = await db.suzuki_preventivi.find_one({"id": pid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Preventivo non trovato")
    prev = SuzukiPreventivo(**doc)
    pdf_bytes = await _build_pdf(prev)
    filename = f"preventivo_suzuki_{prev.numero or prev.id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# PDF BUILDER
# ---------------------------------------------------------------------------
def _fmt_eur(v: float) -> str:
    s = f"{float(v or 0):,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


async def _build_pdf(p: SuzukiPreventivo) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    NAVY = colors.HexColor("#0F2A47")
    NAVY_LIGHT = colors.HexColor("#26466B")
    LIGHT_GREY = colors.HexColor("#F2F4F7")
    BORDER = colors.HexColor("#D0D5DD")
    TEXT_MUTED = colors.HexColor("#667085")

    styles = getSampleStyleSheet()
    st_label = ParagraphStyle("lab", parent=styles["Normal"], fontSize=8, textColor=TEXT_MUTED, leading=10)
    st_val = ParagraphStyle("val", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13)
    st_title = ParagraphStyle("t", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=NAVY, alignment=TA_LEFT)
    st_sub = ParagraphStyle("s", parent=styles["Normal"], fontSize=9, leading=11, textColor=TEXT_MUTED)
    st_row = ParagraphStyle("row", parent=styles["Normal"], fontSize=9, leading=12)
    st_row_bold = ParagraphStyle("rb", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12)
    st_section = ParagraphStyle("sec", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, textColor=colors.white, leading=13)
    st_total_lab = ParagraphStyle("tl", parent=styles["Normal"], fontSize=11, textColor=colors.white, alignment=TA_RIGHT)
    st_total_val = ParagraphStyle("tv", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=15, textColor=colors.white, alignment=TA_RIGHT)
    st_footer = ParagraphStyle("f", parent=styles["Normal"], fontSize=8, textColor=TEXT_MUTED, leading=11)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14*mm, rightMargin=14*mm, topMargin=10*mm, bottomMargin=10*mm)

    def section_header(text: str, bg=NAVY):
        t = Table([[Paragraph(text, st_section)]], colWidths=[182*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ]))
        return t

    story = []

    # HEADER
    left_text = [
        Paragraph("VIA DEGLI ARTIGIANI, 1 · 57034 CAMPO NELL'ELBA (LI)", st_sub),
        Paragraph("Tel. 347 260 08 72 · info@genbnautica.it · www.genbnautica.it", st_sub),
    ]
    logo = _logo_flowable(max_w_mm=44, max_h_mm=22)
    if logo:
        left_block = Table([[logo], [left_text]], colWidths=[110*mm])
        left_block.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (0,0), 2),
            ("BOTTOMPADDING", (0,1), (-1,-1), 0),
        ]))
        left = left_block
    else:
        left = [
            Paragraph("<b>GEB di Palmieri Sandro</b>", st_val),
            *left_text,
        ]
    data_it = "—"
    try:
        d = datetime.fromisoformat((p.data or "")[:10])
        data_it = d.strftime("%d/%m/%Y")
    except Exception:
        pass
    right = Table(
        [[Paragraph("PREVENTIVO", st_title)],
         [Paragraph("Fuoribordo Suzuki", st_sub)],
         [Spacer(1, 4)],
         [Table([
             [Paragraph("N°", st_label), Paragraph(p.numero or "—", st_val)],
             [Paragraph("Data", st_label), Paragraph(data_it, st_val)],
         ], colWidths=[18*mm, 50*mm], style=TableStyle([
             ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
             ("LEFTPADDING", (0,0), (-1,-1), 0),
             ("RIGHTPADDING", (0,0), (-1,-1), 0),
             ("TOPPADDING", (0,0), (-1,-1), 1.5),
             ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
         ]))]],
        colWidths=[70*mm],
        style=TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]),
    )
    header = Table([[left, right]], colWidths=[112*mm, 70*mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(header)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceBefore=0, spaceAfter=6))

    # CLIENTE
    cliente_lines = [
        Paragraph("Spettabile", ParagraphStyle("sp", parent=styles["Normal"], fontSize=8.5, textColor=TEXT_MUTED, leading=10)),
        Paragraph(f"<b>{p.cliente_nome or '—'}</b>", st_val),
    ]
    if p.cliente_telefono:
        cliente_lines.append(Paragraph(f"Tel. {p.cliente_telefono}", st_row))
    if p.cliente_email:
        cliente_lines.append(Paragraph(f"Email: {p.cliente_email}", st_row))
    cliente_box = Table([[cliente_lines]], colWidths=[182*mm])
    cliente_box.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GREY),
        ("BOX", (0,0), (-1,-1), 0.6, BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(cliente_box)
    story.append(Spacer(1, 8))

    # MODELLO + SPECIFICHE
    story.append(section_header("MODELLO SUZUKI"))

    # Fallback: se lo snapshot tecnico è vuoto ma abbiamo modello_id, prendi dal catalogo
    def _has_snapshot(pv: SuzukiPreventivo) -> bool:
        return any([
            pv.cilindri, pv.cilindrata_cc, pv.alimentazione, pv.peso_kg,
            pv.avviamento, pv.gambo, pv.trim, pv.comandi, pv.alternatore_A, pv.carburante,
        ])

    tech = {
        "cilindri": p.cilindri or "",
        "cilindrata_cc": p.cilindrata_cc or 0,
        "alimentazione": p.alimentazione or "",
        "peso_kg": p.peso_kg or 0,
        "avviamento": p.avviamento or "",
        "gambo": p.gambo or "",
        "trim": p.trim or "",
        "comandi": p.comandi or "",
        "alternatore_A": p.alternatore_A or 0,
        "carburante": p.carburante or "",
    }
    if not _has_snapshot(p) and p.modello_id:
        m = await db.suzuki_modelli.find_one({"id": p.modello_id}, {"_id": 0})
        if m:
            for k in tech.keys():
                tech[k] = m.get(k, tech[k]) or tech[k]

    # Riga info principali (Codice · Modello · Potenza)
    st_cell_lab = ParagraphStyle("cl", parent=styles["Normal"], fontSize=7.5, textColor=TEXT_MUTED, leading=9)
    st_cell_val = ParagraphStyle("cv", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=12)

    def cell(label: str, value: str):
        return [Paragraph(label.upper(), st_cell_lab), Paragraph(value or "—", st_cell_val)]

    info_row = [[
        cell("Codice articolo", p.codice or "—"),
        cell("Modello", p.modello or "—"),
        cell("Potenza", f"{p.potenza_hp:g} HP" if p.potenza_hp else "—"),
    ]]
    tinfo = Table(info_row, colWidths=[60.66*mm, 60.66*mm, 60.66*mm])
    tinfo.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GREY),
        ("BOX", (0,0), (-1,-1), 0.4, BORDER),
        ("INNERGRID", (0,0), (-1,-1), 0.25, BORDER),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(tinfo)
    story.append(Spacer(1, 4))

    # Scheda tecnica 3×3
    def fmt_n(v, suffix):
        try:
            f = float(v)
            if f > 0:
                return f"{f:g} {suffix}"
        except Exception:
            pass
        return "—"

    grid_cells = [
        cell("Cilindri", tech["cilindri"] or "—"),
        cell("Cilindrata", fmt_n(tech["cilindrata_cc"], "cc")),
        cell("Alimentazione", tech["alimentazione"] or "—"),
        cell("Peso", fmt_n(tech["peso_kg"], "kg")),
        cell("Gambo", tech["gambo"] or "—"),
        cell("Trim", tech["trim"] or "—"),
        cell("Avviamento", tech["avviamento"] or "—"),
        cell("Comandi", tech["comandi"] or "—"),
        cell("Alternatore", fmt_n(tech["alternatore_A"], "A")),
        cell("Carburante", tech["carburante"] or "—"),
        "",
        "",
    ]
    grid_rows = [grid_cells[i:i+3] for i in range(0, 12, 3)]
    tgrid = Table(grid_rows, colWidths=[60.66*mm, 60.66*mm, 60.66*mm])
    tgrid.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.4, BORDER),
        ("INNERGRID", (0,0), (-1,-1), 0.25, BORDER),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, LIGHT_GREY]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(tgrid)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # COSTO MOTORE (evidenziato)
    # ------------------------------------------------------------------
    iva_perc = await _get_iva_perc()
    calc = _calc_totale(p, iva_perc=iva_perc)
    story.append(section_header("COSTO MOTORE"))

    motor_rows = [
        [Paragraph("Prezzo pubblico Suzuki (IVA inclusa)", st_row),
         Paragraph(_fmt_eur(calc["prezzo_listino"]), st_row_bold)],
    ]
    if p.sconto_perc_1:
        motor_rows.append([Paragraph(f"Sconto 1: <b>{p.sconto_perc_1:g}%</b>", st_row),
                           Paragraph("− " + _fmt_eur(calc["importo_sconto_1"]), st_row_bold)])
    if p.sconto_perc_2:
        motor_rows.append([Paragraph(f"Sconto 2: <b>{p.sconto_perc_2:g}%</b>", st_row),
                           Paragraph("− " + _fmt_eur(calc["importo_sconto_2"]), st_row_bold)])
    tmotor = Table(motor_rows, colWidths=[140*mm, 42*mm])
    tmotor.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.4, BORDER),
        ("INNERGRID", (0,0), (-1,-1), 0.25, BORDER),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, LIGHT_GREY]),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(tmotor)

    # Riga netto motore — evidenziata con fondo colorato e font più grande
    st_motor_lab = ParagraphStyle("motorlab", parent=styles["Normal"], fontName="Helvetica-Bold",
                                  fontSize=11, textColor=colors.white, leading=14)
    st_motor_val = ParagraphStyle("motorval", parent=styles["Normal"], fontName="Helvetica-Bold",
                                  fontSize=13, textColor=colors.white, leading=15, alignment=TA_RIGHT)
    tnetto = Table(
        [[Paragraph("NETTO MOTORE SCONTATO", st_motor_lab),
          Paragraph(_fmt_eur(calc["netto_motore"]), st_motor_val)]],
        colWidths=[140*mm, 42*mm],
    )
    tnetto.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY_LIGHT),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(tnetto)

    # ALLARME SOTTO-COSTO (se il netto motore < costo di acquisto IVA incl.)
    if calc.get("sotto_costo"):
        WARN_BG = colors.HexColor("#FEF3F2")
        WARN_BORDER = colors.HexColor("#B42318")
        st_warn_title = ParagraphStyle("wt", parent=styles["Normal"], fontName="Helvetica-Bold",
                                       fontSize=10, textColor=WARN_BORDER, leading=13)
        st_warn_body = ParagraphStyle("wb", parent=styles["Normal"], fontSize=8.5,
                                      textColor=colors.HexColor("#7A1913"), leading=11)
        warn_msg = (
            f"Il <b>NETTO MOTORE</b> ({_fmt_eur(calc['netto_motore'])}) è <b>inferiore</b> al prezzo del "
            f"listino concessionario di questo modello. Verificare gli sconti applicati prima di confermare."
        )
        twarn = Table(
            [[Paragraph("⚠  ATTENZIONE: PREZZO SOTTO COSTO", st_warn_title)],
             [Paragraph(warn_msg, st_warn_body)]],
            colWidths=[182*mm],
        )
        twarn.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), WARN_BG),
            ("BOX", (0,0), (-1,-1), 1.2, WARN_BORDER),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(Spacer(1, 4))
        story.append(twarn)

    story.append(Spacer(1, 8))

    # ------------------------------------------------------------------
    # INSTALLAZIONE E ACCESSORI (solo se presenti)
    # ------------------------------------------------------------------
    extra_rows = []
    if calc["montaggio"] > 0:
        extra_rows.append([Paragraph("Montaggio e collaudo", st_row),
                           Paragraph("+ " + _fmt_eur(calc["montaggio"]), st_row_bold)])
    if calc["cavetteria"] > 0:
        extra_rows.append([Paragraph("Cavetteria e accessori di installazione", st_row),
                           Paragraph("+ " + _fmt_eur(calc["cavetteria"]), st_row_bold)])
    if extra_rows:
        story.append(section_header("INSTALLAZIONE E ACCESSORI"))
        textra = Table(extra_rows, colWidths=[140*mm, 42*mm])
        textra.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 0.4, BORDER),
            ("INNERGRID", (0,0), (-1,-1), 0.25, BORDER),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, LIGHT_GREY]),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        story.append(textra)
        story.append(Spacer(1, 8))
    else:
        story.append(Spacer(1, 4))

    # TOTALE FINALE
    tot_tbl = Table(
        [[Paragraph("TOTALE PREVENTIVO", st_total_lab),
          Paragraph(_fmt_eur(calc["totale_iva_esclusa"]), st_total_val)],
         ["", Paragraph("IVA compresa", ParagraphStyle("iva", parent=styles["Normal"], fontSize=9, textColor=colors.white, alignment=TA_RIGHT))]],
        colWidths=[130*mm, 52*mm],
    )
    tot_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 14),
        ("RIGHTPADDING", (0,0), (-1,-1), 14),
    ]))
    story.append(tot_tbl)
    story.append(Spacer(1, 10))

    # NOTE
    if p.note:
        story.append(Paragraph(f"<b>Note:</b> {p.note}", st_row))
        story.append(Spacer(1, 6))

    # LEGENDA SIGLE (compatta)
    for f in await _legenda_flowables(avail_width_mm=182, compact=True):
        story.append(f)

    # FOOTER — condizioni + firma
    condizioni = await _get_condizioni_preventivo()
    cond_paras = [Paragraph(t, st_footer) for t in condizioni if t and t.strip()]
    firma_cell = [
        Paragraph("Il titolare", ParagraphStyle("fl", parent=styles["Normal"], fontSize=9, textColor=TEXT_MUTED, alignment=TA_CENTER)),
        Spacer(1, 22),
        Paragraph("<b>Sandro Palmieri</b>", ParagraphStyle("fn", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, textColor=NAVY, alignment=TA_CENTER)),
        HRFlowable(width="80%", thickness=0.5, color=BORDER, spaceBefore=2, spaceAfter=0, hAlign="CENTER"),
    ]
    footer = Table([[cond_paras, firma_cell]], colWidths=[120*mm, 62*mm])
    footer.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("LINEABOVE", (0,0), (-1,0), 0.6, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(footer)

    doc.build(story)
    return buf.getvalue()
