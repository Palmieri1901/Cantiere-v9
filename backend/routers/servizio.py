"""Documenti di servizio: coordinate bancarie (PDF) e modulo consenso privacy (PDF)."""
import io
import re
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import db
from helpers import _euro, _totale_extra
from pdf_builders import build_documento_servizio_pdf

router = APIRouter()

PRIVACY_DEFAULT = """INFORMATIVA SUL TRATTAMENTO DEI DATI PERSONALI
(art. 13 Regolamento UE 2016/679 - GDPR)

Titolare del trattamento: {cantiere}, {indirizzo} - Tel. {telefono} - Email {email}

1. FINALITÀ E BASE GIURIDICA
I dati personali forniti (dati anagrafici, recapiti, dati dell'imbarcazione e del motore, dati di pagamento) sono trattati per:
a) esecuzione del contratto di rimessaggio, alaggio, varo, manutenzione, riparazione e degli altri servizi richiesti (art. 6.1.b GDPR);
b) adempimenti amministrativi, contabili e fiscali previsti dalla legge (art. 6.1.c GDPR);
c) comunicazioni di servizio relative a scadenze, manutenzioni, movimentazioni dell'imbarcazione e pagamenti (art. 6.1.b GDPR);
d) previo consenso, invio di comunicazioni commerciali e promozionali su prodotti e servizi del cantiere (art. 6.1.a GDPR).

2. MODALITÀ DEL TRATTAMENTO
Il trattamento è effettuato con strumenti cartacei ed informatici, con misure di sicurezza adeguate a prevenire perdita, accessi non autorizzati e usi illeciti.

3. CONSERVAZIONE
I dati sono conservati per la durata del rapporto contrattuale e, successivamente, per il termine di 10 anni previsto dagli obblighi civilistici e fiscali. I dati trattati per finalità promozionali sono conservati fino alla revoca del consenso.

4. COMUNICAZIONE E DESTINATARI
I dati potranno essere comunicati a: consulenti fiscali e contabili, istituti bancari, compagnie assicurative, autorità marittime e portuali, fornitori di servizi informatici che agiscono come responsabili del trattamento. I dati non sono diffusi né trasferiti al di fuori dell'Unione Europea.

5. DIRITTI DELL'INTERESSATO
L'interessato può esercitare in ogni momento i diritti di accesso, rettifica, cancellazione, limitazione, portabilità e opposizione (artt. 15-22 GDPR), nonché revocare il consenso e proporre reclamo al Garante per la protezione dei dati personali, scrivendo ai recapiti del Titolare sopra indicati.

6. NATURA DEL CONFERIMENTO
Il conferimento dei dati per le finalità a), b), c) è necessario per l'erogazione dei servizi; il mancato conferimento comporta l'impossibilità di eseguire il contratto. Il conferimento per la finalità d) è facoltativo.
"""


class DatiServizio(BaseModel):
    banca: Optional[str] = ""
    intestatario: Optional[str] = ""
    iban: Optional[str] = ""
    bic: Optional[str] = ""
    note_pagamento: Optional[str] = ""
    privacy_testo: Optional[str] = None


class EstraiIn(BaseModel):
    file_base64: str


def split_iban(iban: str) -> dict:
    s = re.sub(r"\s+", "", iban or "").upper()
    out = {"iban": s, "iban_spaziato": " ".join(s[i:i + 4] for i in range(0, len(s), 4)), "paese": s[:2], "check": s[2:4]}
    if s.startswith("IT") and len(s) == 27:
        out.update({"cin": s[4], "abi": s[5:10], "cab": s[10:15], "conto": s[15:27]})
    else:
        out.update({"cin": "", "abi": "", "cab": "", "conto": ""})
    return out


async def _get() -> dict:
    d = await db.documenti_servizio.find_one({"id": "default"}, {"_id": 0}) or {"id": "default"}
    if not d.get("privacy_testo"):
        d["privacy_testo"] = PRIVACY_DEFAULT
    d["iban_split"] = split_iban(d.get("iban", ""))
    return d


@router.get("/servizio/dati")
async def get_dati():
    return await _get()


@router.put("/servizio/dati")
async def put_dati(payload: DatiServizio):
    upd = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "iban" in upd:
        upd["iban"] = re.sub(r"\s+", "", upd["iban"]).upper()
    await db.documenti_servizio.update_one({"id": "default"}, {"$set": upd}, upsert=True)
    return await _get()


@router.get("/servizio/privacy/default")
async def privacy_default():
    return {"testo": PRIVACY_DEFAULT}


@router.post("/servizio/privacy/estrai")
async def privacy_estrai(payload: EstraiIn):
    from ai_client import vision
    testo = await vision(
        "Sei un assistente che trascrive documenti legali in italiano. Restituisci solo il testo, senza commenti.",
        "Trascrivi integralmente il testo di questa informativa/consenso privacy, mantenendo titoli, numerazione e paragrafi. "
        "Non aggiungere nulla e non riassumere. Se il documento ha più pagine, trascrivile tutte.",
        [payload.file_base64],
    )
    testo = testo.strip()
    if not testo:
        raise HTTPException(422, "Nessun testo riconosciuto nel documento")
    return {"testo": testo}


async def _cliente(cid: Optional[str]) -> Optional[dict]:
    if not cid:
        return None
    c = await db.clienti.find_one({"id": cid}, {"_id": 0})
    if c:
        return c
    e = await db.clienti_esterni.find_one({"id": cid}, {"_id": 0})
    return {"cognome": e["nome"], "nome": "", **e} if e else None


COST_KEYS = ("costo_sosta", "costo_movimentazione", "costo_taccaggio", "costo_copertura", "costo_alaggio", "costo_varo",
             "costo_antivegetativa", "costo_scafo_sporco", "costo_lavaggio_inizio", "costo_lavaggio_fine", "costo_manutenzione_motore")


def _totale_cliente(c: dict) -> float:
    return round(sum(float(c.get(k) or 0) for k in COST_KEYS) + _totale_extra(c), 2)


@router.get("/servizio/coordinate.pdf")
async def coordinate_pdf(cliente_id: Optional[str] = None, importo: Optional[float] = None, causale: Optional[str] = None):
    d = await _get()
    if not d.get("iban"):
        raise HTTPException(400, "Inserisci prima l'IBAN nei dati bancari")
    cant = await db.cantiere.find_one({"id": "default"}, {"_id": 0}) or {}
    c = await _cliente(cliente_id)
    sp = d["iban_split"]
    righe = [("Intestatario", d.get("intestatario") or cant.get("nome", "")), ("Banca", d.get("banca", "")),
             ("IBAN", sp["iban_spaziato"])]
    if sp["abi"]:
        righe += [("Paese / Check", f"{sp['paese']} {sp['check']}"), ("CIN", sp["cin"]), ("ABI", sp["abi"]), ("CAB", sp["cab"]), ("Numero conto", sp["conto"])]
    if d.get("bic"):
        righe.append(("BIC / SWIFT", d["bic"]))
    blocchi = [("COORDINATE BANCARIE", righe)]
    sub = "Coordinate bancarie"
    if c:
        imp = importo if importo is not None else _totale_cliente(c)
        caus = causale or f"Rimessaggio {c.get('anno') or date.today().year} - {c.get('cognome', '')} {c.get('nome', '')}".strip()
        blocchi.insert(0, ("ISTRUZIONI DI PAGAMENTO", [("Cliente", f"{c.get('cognome', '')} {c.get('nome', '')}".strip()),
                                                        ("Imbarcazione", c.get("tipo_barca") or "—"), ("Importo", _euro(imp)), ("Causale", caus)]))
        sub = "Istruzioni di pagamento"
    note = d.get("note_pagamento") or "Si prega di indicare sempre la causale nel bonifico. Grazie."
    pdf = build_documento_servizio_pdf(cant, sub, blocchi, note=note)
    fname = f"Coordinate_bancarie{('_' + c['cognome'].replace(' ', '_')) if c else ''}.pdf"
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{fname}"'})


@router.get("/servizio/privacy.pdf")
async def privacy_pdf(cliente_id: Optional[str] = None, nome: Optional[str] = None):
    d = await _get()
    cant = await db.cantiere.find_one({"id": "default"}, {"_id": 0}) or {}
    c = await _cliente(cliente_id)
    indirizzo = ", ".join(x for x in [cant.get("indirizzo"), " ".join(filter(None, [cant.get("cap"), cant.get("citta")]))] if x)
    testo = d["privacy_testo"].replace("{cantiere}", cant.get("nome", "")).replace("{indirizzo}", indirizzo) \
        .replace("{telefono}", cant.get("telefono", "") or "").replace("{email}", cant.get("email", "") or "")
    nome_firma = (nome or "").strip() or (f"{c.get('cognome', '')} {c.get('nome', '')}".strip() if c else "")
    pdf = build_documento_servizio_pdf(cant, "Informativa e consenso privacy", [], testo=testo, firma_nome=nome_firma, consenso=True)
    fname = f"Consenso_privacy{('_' + nome_firma.replace(' ', '_')) if nome_firma else ''}.pdf"
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{fname}"'})
