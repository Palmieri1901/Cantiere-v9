"""Costruttori PDF: preventivo singolo + storico multi-anno.

Contengono unicamente logica di rendering ReportLab. Nessun accesso a MongoDB.
"""
import io
import re
import base64 as _b64
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage

from helpers import _euro
from models import Tariffe


def _build_storico_pdf(docs: list, cantiere_doc: dict) -> bytes:
    """Genera PDF A4 con storico multi-anno di un cliente. `docs` ordinati dal più recente."""
    buf = io.BytesIO()
    primo = docs[0] if docs else {}
    pdf = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm,
        title=f"Storico {primo.get('cognome','')} {primo.get('nome','')}"
    )
    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#0F1B3D")
    TEAK = colors.HexColor("#B0562E")
    SAND = colors.HexColor("#F3EFE7")
    MUTED = colors.HexColor("#5B6478")

    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10, textColor=TEAK, leading=12, letterSpace=1.5, spaceBefore=8, spaceAfter=3)
    h3 = ParagraphStyle("h3", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, textColor=colors.white, leading=16)
    label = ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=MUTED, leading=9)
    val = ParagraphStyle("val", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=12)
    body = ParagraphStyle("body", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=NAVY, leading=11)

    elems = []

    nome_cantiere = (cantiere_doc.get("nome") or "PORTOMARE").upper()
    indirizzo_parts = [x for x in [cantiere_doc.get("indirizzo"), " ".join(filter(None, [cantiere_doc.get("cap"), cantiere_doc.get("citta"), (f"({cantiere_doc.get('provincia')})" if cantiere_doc.get("provincia") else "")])), cantiere_doc.get("telefono"), cantiere_doc.get("email"), cantiere_doc.get("piva") and f"P.IVA {cantiere_doc.get('piva')}"] if x]
    contatti_txt = " · ".join(indirizzo_parts) if indirizzo_parts else ""
    logo_b64 = cantiere_doc.get("logo_base64") or ""
    logo_cell = Paragraph(f"<b>{nome_cantiere}</b>", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY))
    if logo_b64 and "," in logo_b64:
        try:
            raw = _b64.b64decode(logo_b64.split(",", 1)[1])
            logo_cell = RLImage(io.BytesIO(raw), width=30*mm, height=18*mm, kind="proportional")
        except Exception:
            pass

    header_tbl = Table([
        [logo_cell,
         Paragraph(f"<para align=right><font color='#5B6478' size=8>STORICO CLIENTE</font><br/><font size=14 color='#B0562E'><b>{primo.get('cognome','')} {primo.get('nome','')}</b></font><br/><font color='#5B6478' size=8>Emesso il {date.today().strftime('%d/%m/%Y')}</font></para>", body)]
    ], colWidths=[85*mm, 95*mm])
    header_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    elems.append(header_tbl)
    if contatti_txt:
        elems.append(Spacer(1, 1*mm))
        elems.append(Paragraph(f"<font color='#5B6478' size=7>{contatti_txt}</font>", body))
    sep = Table([[""]], colWidths=[180*mm], rowHeights=[1.5])
    sep.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), TEAK)]))
    elems.append(Spacer(1, 2*mm))
    elems.append(sep)
    elems.append(Spacer(1, 3*mm))

    elems.append(Paragraph("ANAGRAFICA", h2))
    anagr_tbl = Table([
        [Paragraph("Cliente", label), Paragraph("Contatti", label)],
        [Paragraph(f"<b>{primo.get('cognome','')} {primo.get('nome','')}</b><br/><font size=8 color='#5B6478'>CF: {primo.get('codice_fiscale') or '—'}</font>", val),
         Paragraph(f"{primo.get('telefono') or '—'} · {primo.get('cellulare') or '—'}<br/><font size=8 color='#5B6478'>{primo.get('email') or '—'}</font>", body)],
        [Paragraph("Imbarcazione", label), Paragraph("Anni tracciati", label)],
        [Paragraph(f"<b>{primo.get('tipo_barca') or '—'}</b> · L. {primo.get('lunghezza') or '—'} m", body),
         Paragraph(f"<b>{len(docs)}</b> anno/i · da {min(d.get('anno') or 0 for d in docs)} a {max(d.get('anno') or 0 for d in docs)}", body)],
    ], colWidths=[90*mm, 90*mm])
    anagr_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("BOTTOMPADDING", (0,0), (-1,-1), 2)]))
    elems.append(anagr_tbl)

    COST_KEYS = [
        ("Sosta", "costo_sosta"),
        ("Movimentazione", "costo_movimentazione"),
        ("Taccaggio", "costo_taccaggio"),
        ("Copertura", "costo_copertura"),
        ("Alaggio", "costo_alaggio"),
        ("Varo", "costo_varo"),
        ("Antivegetativa", "costo_antivegetativa"),
        ("Magg. scafo sporco", "costo_scafo_sporco"),
        ("Lavaggio inizio stagione", "costo_lavaggio_inizio"),
        ("Lavaggio fine stagione", "costo_lavaggio_fine"),
        ("Manutenzione motore", "costo_manutenzione_motore"),
    ]
    totale_generale = 0.0

    for d in docs:
        anno = d.get("anno") or "—"
        sosta_label = {"dentro": "Al coperto", "fuori": "Su piazzale", "fuori_sede": "Fuori sede", "temporanea": "Temporanea"}.get(d.get("tipo_sosta"), "—")
        pagato_lbl = "PAGATO" if d.get("pagato") else "NON PAGATO"
        pagato_color = "#0F7B4E" if d.get("pagato") else "#B00020"

        anno_tbl = Table([[
            Paragraph(f"<font color='white'><b>ANNO {anno}</b></font>", h3),
            Paragraph(f"<para align=right><font color='white' size=8>{sosta_label} · Posto #{str(d.get('posto_barca') or '—').zfill(3) if d.get('posto_barca') else '—'}</font></para>", body),
        ]], colWidths=[90*mm, 90*mm])
        anno_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), NAVY),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ]))
        elems.append(Spacer(1, 4*mm))
        elems.append(anno_tbl)

        rows = [["VOCE", "IMPORTO"]]
        subtot = 0.0
        for lbl, k in COST_KEYS:
            v = float(d.get(k) or 0)
            if v > 0:
                lbl_out = lbl
                if k in ("costo_alaggio", "costo_varo"):
                    dest = d.get("destinazione_alaggio_varo") or "marina_di_campo"
                    dest_nome = (d.get("destinazione_altra_nome") or "").strip()
                    mov = int(d.get("numero_movimenti") or 1)
                    if dest == "altra" and dest_nome:
                        lbl_out = f"{lbl} ({dest_nome})"
                    if mov > 1:
                        lbl_out = f"{lbl_out} × {mov} mov."
                rows.append([lbl_out, _euro(v)])
                subtot += v
        for it in (d.get("lavorazioni_extra") or []):
            prezzo = float((it or {}).get("prezzo") or 0)
            if prezzo <= 0:
                continue
            descr = ((it or {}).get("descrizione") or "").strip() or "Lavorazione extra"
            rows.append([f"Extra · {descr}", _euro(prezzo)])
            subtot += prezzo
        for it in (d.get("lavori_storico") or []):
            costo_l = float((it or {}).get("costo") or 0)
            if costo_l <= 0:
                continue
            descr = ((it or {}).get("descrizione") or "").strip() or (it or {}).get("tipo") or "Lavoro"
            rows.append([f"Lavoro {(it or {}).get('data') or ''} · {descr}", _euro(costo_l)])
            subtot += costo_l

        if len(rows) == 1:
            rows.append([Paragraph("<i>Nessun costo registrato per quest'anno.</i>", body), ""])

        rows.append(["TOTALE ANNO", _euro(subtot)])
        cost_tbl = Table(rows, colWidths=[130*mm, 50*mm])
        cost_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), TEAK),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 8),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("FONTNAME", (0,1), (-1,-2), "Helvetica"),
            ("FONTSIZE", (0,1), (-1,-2), 9),
            ("TEXTCOLOR", (0,1), (-1,-2), NAVY),
            ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, SAND]),
            ("BACKGROUND", (0,-1), (-1,-1), NAVY),
            ("TEXTCOLOR", (0,-1), (-1,-1), colors.white),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,-1), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("LINEBELOW", (0,1), (-1,-2), 0.3, colors.HexColor("#D9D9D9")),
        ]))
        elems.append(cost_tbl)

        info_line = Paragraph(
            f"<font size=8 color='{pagato_color}'><b>{pagato_lbl}</b></font> "
            f"<font size=8 color='#5B6478'>· {d.get('data_pagamento') or 'data non registrata'}</font>"
            + (f" <font size=8 color='#5B6478'>· Note: {d.get('note_lavori')}</font>" if d.get("note_lavori") else ""),
            body,
        )
        elems.append(Spacer(1, 1*mm))
        elems.append(info_line)
        totale_generale += subtot

    elems.append(Spacer(1, 6*mm))
    tot_tbl = Table([[
        Paragraph("<font color='white' size=12><b>TOTALE GENERALE STORICO</b></font>", body),
        Paragraph(f"<para align=right><font color='white' size=14><b>{_euro(totale_generale)}</b></font></para>", body),
    ]], colWidths=[120*mm, 60*mm])
    tot_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), TEAK),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
    ]))
    elems.append(tot_tbl)

    elems.append(Spacer(1, 4*mm))
    elems.append(Paragraph(
        f"<font color='#5B6478' size=7>Report generato il {date.today().strftime('%d/%m/%Y')} · {nome_cantiere}</font>",
        body,
    ))

    pdf.build(elems)
    buf.seek(0)
    return buf.read()


def _build_preventivo_pdf(doc: dict, lavori_docs: list, cantiere_doc: dict, t_current: Tariffe) -> bytes:
    """Genera il PDF preventivo come bytes. Estratto per riuso in singolo + bulk export."""
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=12*mm, rightMargin=12*mm, topMargin=10*mm, bottomMargin=8*mm,
        title=f"Preventivo {doc.get('cognome','')} {doc.get('nome','')}"
    )
    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#0F1B3D")
    TEAK = colors.HexColor("#B0562E")
    SAND = colors.HexColor("#F3EFE7")
    MUTED = colors.HexColor("#5B6478")

    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=9, textColor=TEAK, spaceBefore=6, spaceAfter=2, leading=11, letterSpace=1.5)
    label = ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=MUTED, leading=9)
    val = ParagraphStyle("val", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=12)
    body = ParagraphStyle("body", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=NAVY, leading=11)
    tiny = ParagraphStyle("tiny", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=MUTED, leading=9)

    elems = []

    nome_cantiere = (cantiere_doc.get("nome") or "PORTOMARE").upper()
    indirizzo_parts = [x for x in [cantiere_doc.get("indirizzo"), " ".join(filter(None, [cantiere_doc.get("cap"), cantiere_doc.get("citta"), (f"({cantiere_doc.get('provincia')})" if cantiere_doc.get("provincia") else "")])), cantiere_doc.get("telefono"), cantiere_doc.get("email"), cantiere_doc.get("piva") and f"P.IVA {cantiere_doc.get('piva')}"] if x]
    contatti_txt = " · ".join(indirizzo_parts) if indirizzo_parts else ""

    logo_b64 = cantiere_doc.get("logo_base64") or ""
    logo_cell = Paragraph(f"<b>{nome_cantiere}</b>", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY))
    if logo_b64 and "," in logo_b64:
        try:
            raw = _b64.b64decode(logo_b64.split(",", 1)[1])
            logo_cell = RLImage(io.BytesIO(raw), width=30*mm, height=18*mm, kind="proportional")
        except Exception:
            pass

    header_tbl = Table([
        [logo_cell,
         Paragraph(f"<para align=right><font color='#5B6478' size=8>PREVENTIVO</font><br/><font size=14 color='#B0562E'><b>#{doc.get('posto_barca') or '—'}</b></font><br/><font color='#5B6478' size=8>{date.today().strftime('%d/%m/%Y')}</font></para>", body)]
    ], colWidths=[100*mm, 74*mm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    elems.append(header_tbl)
    if contatti_txt:
        elems.append(Spacer(1, 1*mm))
        elems.append(Paragraph(f"<font color='#5B6478' size=7>{contatti_txt}</font>", body))
    elems.append(Spacer(1, 2*mm))
    sep = Table([[""]], colWidths=[186*mm], rowHeights=[1.5])
    sep.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), TEAK)]))
    elems.append(sep)
    elems.append(Spacer(1, 2*mm))

    elems.append(Paragraph("CLIENTE E IMBARCAZIONE", h2))
    potenza = doc.get('potenza_motore') or 0
    litri_pdf = doc.get('litri_olio_motore') or 0
    sosta_label = ('Al coperto' if doc.get('tipo_sosta')=='dentro'
                   else 'Fuori sede' if doc.get('tipo_sosta')=='fuori_sede'
                   else f"Temporanea · {int(doc.get('giorni_sosta_temporanea') or 0)} giorni" if doc.get('tipo_sosta')=='temporanea'
                   else 'Su piazzale (fuori)')
    larg_pers = doc.get('larghezza_personalizzata')
    _lung_val = doc.get('lunghezza')
    if _lung_val:
        if larg_pers and float(larg_pers) > 0:
            _larg = float(larg_pers)
        elif float(_lung_val) <= 6.5:
            _larg = 2.5
        elif float(_lung_val) <= 9.0:
            _larg = 3.0
        else:
            _larg = 4.0
        _mq_str = f"{float(_lung_val) * _larg:g} mq"
        _lung_display = f"L. {_lung_val} m × {_larg:g} m ({_mq_str})"
    else:
        _lung_display = f"L. {_lung_val or '—'} m"
    info_tbl = Table([
        [Paragraph("Cliente", label), Paragraph("Contatti", label)],
        [Paragraph(f"<b>{doc.get('cognome','')} {doc.get('nome','')}</b>", val),
         Paragraph(f"{doc.get('telefono') or '—'} · {doc.get('email') or '—'}", body)],
        [Paragraph("Imbarcazione", label), Paragraph("Sosta", label)],
        [Paragraph(f"<b>{doc.get('tipo_barca','')}</b> · <font color='#5B6478' size=8>{_lung_display} · Motore: {int(potenza) if potenza else '—'} HP · Olio: {litri_pdf:g} L</font>", body),
         Paragraph(f"<b>{sosta_label}</b> · <font color='#5B6478' size=8>Posto: #{str(doc.get('posto_barca') or '—').zfill(3) if doc.get('posto_barca') else '—'}</font>", body)],
    ], colWidths=[93*mm, 93*mm])
    info_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
        ("TOPPADDING", (0,0), (-1,-1), 0),
    ]))
    elems.append(info_tbl)

    elems.append(Paragraph("DETTAGLIO COSTI ANNUALI", h2))
    voci = []
    def add(label_txt, key):
        v = float(doc.get(key) or 0)
        if v > 0:
            voci.append([label_txt, _euro(v)])
    add("Sosta", "costo_sosta")
    add("Movimentazione", "costo_movimentazione")
    add("Taccaggio", "costo_taccaggio")
    add("Copertura", "costo_copertura")
    dest = doc.get("destinazione_alaggio_varo") or "marina_di_campo"
    dest_nome = (doc.get("destinazione_altra_nome") or "").strip()
    mov = int(doc.get("numero_movimenti") or 1)
    suffix_mov = f" × {mov} mov." if mov > 1 else ""
    if dest == "altra" and dest_nome:
        add(f"Alaggio ({dest_nome}){suffix_mov}", "costo_alaggio")
        add(f"Varo ({dest_nome}){suffix_mov}", "costo_varo")
    else:
        add(f"Alaggio{suffix_mov}", "costo_alaggio")
        add(f"Varo{suffix_mov}", "costo_varo")
    add("Antivegetativa", "costo_antivegetativa")
    add("Magg. scafo sporco", "costo_scafo_sporco")
    add("Lavaggio inizio stagione", "costo_lavaggio_inizio")
    add("Lavaggio fine stagione", "costo_lavaggio_fine")
    add("Manutenzione motore", "costo_manutenzione_motore")
    lav_extra = doc.get("lavorazioni_extra") or []
    tot_extra = round(sum(float((it or {}).get("prezzo") or 0) for it in lav_extra), 2)
    if tot_extra > 0:
        voci.append(["Lavorazioni extra", _euro(tot_extra)])
    lav_storico = [l for l in (doc.get("lavori_storico") or []) if float((l or {}).get("costo") or 0) > 0]
    tot_lavori = round(sum(float(l.get("costo") or 0) for l in lav_storico), 2)
    for l in lav_storico:
        descr = (l.get("descrizione") or "").strip() or l.get("tipo") or "Lavoro"
        ore = f" · {l.get('ore'):g} h" if float(l.get("ore") or 0) > 0 else ""
        voci.append([f"Lavoro {l.get('data') or ''} · {descr}{ore}", _euro(float(l.get("costo") or 0))])
    totale = sum(float(doc.get(k) or 0) for k in ("costo_sosta","costo_movimentazione","costo_taccaggio","costo_copertura","costo_alaggio","costo_varo","costo_antivegetativa","costo_scafo_sporco","costo_lavaggio_inizio","costo_lavaggio_fine","costo_manutenzione_motore")) + tot_extra + tot_lavori

    if not voci:
        voci = [["Nessun costo configurato", "—"]]

    costi_data = [["VOCE", "IMPORTO"]] + voci + [["TOTALE", _euro(totale)]]
    costi_tbl = Table(costi_data, colWidths=[136*mm, 50*mm])
    n = len(voci)
    costi_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 7),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("FONTNAME", (0,1), (-1,n), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,n), 9),
        ("TEXTCOLOR", (0,1), (-1,n), NAVY),
        ("ROWBACKGROUNDS", (0,1), (-1,n), [colors.white, SAND]),
        ("LINEBELOW", (0,1), (-1,n), 0.3, colors.HexColor("#D9D9D9")),
        ("BACKGROUND", (0,-1), (-1,-1), TEAK),
        ("TEXTCOLOR", (0,-1), (-1,-1), colors.white),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,-1), (-1,-1), 11),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))
    elems.append(costi_tbl)

    manodopera = float(doc.get("costo_manodopera_motore") or 0)
    ricambi_tot = float(doc.get("costo_ricambi_totale") or 0)
    has_motore_2 = bool(doc.get("secondo_motore"))
    manodopera_2 = float(doc.get("costo_manodopera_motore_2") or 0)
    ricambi_2_tot = float(doc.get("costo_ricambi_motore_2_totale") or 0)

    def _build_motore_table(title_txt, potenza, litri, litri_piede, nc, nt, girante_on, manod, ric_tot):
        rows = [
            ["Manodopera motore", "", _euro(manod)],
        ]
        if girante_on:
            rows.append(["Girante", "1", _euro(t_current.costo_girante)])
        rows.extend([
            ["Olio motore", f"{litri:g} L", _euro(litri * t_current.costo_olio_motore)],
            ["Filtro olio", "1", _euro(t_current.costo_filtro_olio)],
            ["Candele", str(nc), _euro(nc * t_current.costo_candela)],
            ["Termostato", str(nt), _euro(nt * t_current.costo_termostato)],
            ["Olio piede", f"{litri_piede:g} L", _euro(litri_piede * t_current.costo_olio_piede)],
            ["Kit anodi interni", "1", _euro(t_current.costo_anodi_interni)],
            ["Kit anodi esterni", "1", _euro(t_current.costo_anodi_esterni)],
            ["Ingrassaggio", "1", _euro(t_current.costo_ingrassaggio)],
        ])
        subtotale = manod + ric_tot
        header_row = [f"{title_txt} — {int(potenza) if potenza else 0} HP", "", _euro(subtotale)]
        data = [header_row, ["VOCE", "Q.TÀ", "IMPORTO"]] + rows
        tbl = Table(data, colWidths=[116*mm, 20*mm, 50*mm])
        tbl.setStyle(TableStyle([
            ("SPAN", (0,0), (1,0)),
            ("BACKGROUND", (0,0), (-1,0), TEAK),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("ALIGN", (2,0), (2,0), "RIGHT"),
            ("BACKGROUND", (0,1), (-1,1), NAVY),
            ("TEXTCOLOR", (0,1), (-1,1), colors.white),
            ("FONTNAME", (0,1), (-1,1), "Helvetica-Bold"),
            ("FONTSIZE", (0,1), (-1,1), 7),
            ("ALIGN", (1,1), (2,-1), "RIGHT"),
            ("FONTNAME", (0,2), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,2), (-1,-1), 8),
            ("TEXTCOLOR", (0,2), (-1,-1), NAVY),
            ("ROWBACKGROUNDS", (0,2), (-1,-1), [colors.white, SAND]),
            ("LINEBELOW", (0,2), (-1,-1), 0.3, colors.HexColor("#D9D9D9")),
            ("TOPPADDING", (0,0), (-1,-1), 1),
            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ]))
        return tbl

    if manodopera > 0 or ricambi_tot > 0 or manodopera_2 > 0 or ricambi_2_tot > 0:
        elems.append(Paragraph("DETTAGLIO MANUTENZIONE MOTORE", h2))
        nc = int(doc.get("numero_candele") or 0)
        nt = int(doc.get("numero_termostati") or 0)
        girante_attivo = bool(doc.get("girante_attivo", True))
        litri = float(doc.get("litri_olio_motore") or 0)
        potenza_1 = float(doc.get("potenza_motore") or 0)
        motore_1_label = "1° Motore" if has_motore_2 else "Motore"
        litri_piede_1 = float(doc.get("litri_olio_piede") or 1.0)
        elems.append(_build_motore_table(motore_1_label, potenza_1, litri, litri_piede_1, nc, nt, girante_attivo, manodopera, ricambi_tot))

        if has_motore_2:
            elems.append(Spacer(1, 1*mm))
            nc2 = int(doc.get("numero_candele_2") or 0)
            nt2 = int(doc.get("numero_termostati_2") or 0)
            girante_2 = bool(doc.get("girante_2_attivo", True))
            litri2 = float(doc.get("litri_olio_motore_2") or 0)
            litri_piede_2 = float(doc.get("litri_olio_piede_2") or 1.0)
            potenza_2 = float(doc.get("potenza_motore_2") or 0)
            elems.append(_build_motore_table("2° Motore", potenza_2, litri2, litri_piede_2, nc2, nt2, girante_2, manodopera_2, ricambi_2_tot))

    if lav_extra and tot_extra > 0:
        elems.append(Paragraph("LAVORAZIONI EXTRA", h2))
        rows_extra = [["DESCRIZIONE", "IMPORTO"]]
        for it in lav_extra:
            desc = (it.get("descrizione") or "").strip() or "—"
            prezzo = float(it.get("prezzo") or 0)
            if prezzo > 0 or desc != "—":
                rows_extra.append([desc[:80], _euro(prezzo)])
        rows_extra.append(["TOTALE EXTRA", _euro(tot_extra)])
        ex_tbl = Table(rows_extra, colWidths=[136*mm, 50*mm])
        n_ex = len(rows_extra) - 2
        ex_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 7),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("FONTNAME", (0,1), (-1,n_ex), "Helvetica"),
            ("FONTSIZE", (0,1), (-1,n_ex), 9),
            ("TEXTCOLOR", (0,1), (-1,n_ex), NAVY),
            ("ROWBACKGROUNDS", (0,1), (-1,n_ex), [colors.white, SAND]),
            ("LINEBELOW", (0,1), (-1,n_ex), 0.3, colors.HexColor("#D9D9D9")),
            ("BACKGROUND", (0,-1), (-1,-1), TEAK),
            ("TEXTCOLOR", (0,-1), (-1,-1), colors.white),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,-1), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ]))
        elems.append(ex_tbl)

    if doc.get("scadenza_antivegetativa") or doc.get("scadenza_manutenzione"):
        elems.append(Paragraph("PROSSIME SCADENZE", h2))
        rows = []
        if doc.get("scadenza_antivegetativa"):
            rows.append(["Antivegetativa", doc["scadenza_antivegetativa"]])
        if doc.get("scadenza_manutenzione"):
            rows.append(["Manutenzione motore", doc["scadenza_manutenzione"]])
        sc_tbl = Table(rows, colWidths=[136*mm, 50*mm])
        sc_tbl.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("TEXTCOLOR", (0,0), (-1,-1), NAVY),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("LINEBELOW", (0,0), (-1,-1), 0.3, colors.HexColor("#D9D9D9")),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ]))
        elems.append(sc_tbl)

    if lavori_docs:
        elems.append(Paragraph("STORICO LAVORI ESEGUITI", h2))
        headers = ["Data", "Tipo", "Descrizione", "Costo"]
        rows = [headers]
        for l in lavori_docs[:5]:
            rows.append([
                l.get("data",""),
                l.get("tipo",""),
                (l.get("descrizione","") or "")[:60],
                _euro(float(l.get("costo") or 0)),
            ])
        lav_tbl = Table(rows, colWidths=[22*mm, 38*mm, 94*mm, 32*mm])
        lav_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 7),
            ("FONTSIZE", (0,1), (-1,-1), 8),
            ("TEXTCOLOR", (0,1), (-1,-1), NAVY),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, SAND]),
            ("ALIGN", (3,0), (3,-1), "RIGHT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
        ]))
        elems.append(lav_tbl)

    if doc.get("note_lavori"):
        elems.append(Paragraph("NOTE", h2))
        elems.append(Paragraph(doc["note_lavori"].replace("\n", "<br/>"), body))

    # Blocchi editabili (condizioni preventivo)
    def _block(titolo_key, testo_key):
        titolo = (cantiere_doc.get(titolo_key) or "").strip()
        testo = (cantiere_doc.get(testo_key) or "").strip()
        if not titolo and not testo:
            return
        if titolo:
            elems.append(Paragraph(titolo.upper(), h2))
        if testo:
            for para in testo.split("\n"):
                if para.strip():
                    elems.append(Paragraph(para.replace("<", "&lt;").replace(">", "&gt;"), body))
                else:
                    elems.append(Spacer(1, 1*mm))

    _block("preventivo_interno_titolo", "preventivo_interno_testo")
    _block("preventivo_piazzale_titolo", "preventivo_piazzale_testo")
    _block("preventivo_esclusi_titolo", "preventivo_esclusi_testo")
    _block("preventivo_condizioni_titolo", "preventivo_condizioni_testo")

    elems.append(Spacer(1, 3*mm))
    footer_name = cantiere_doc.get("nome") or "Portomare"
    elems.append(Paragraph(
        f"Documento generato automaticamente da {footer_name} — Gestione Cantiere Nautico. "
        f"Validità 30 giorni dalla data di emissione ({date.today().strftime('%d/%m/%Y')}).",
        tiny
    ))

    pdf.build(elems)
    buf.seek(0)
    return buf.getvalue()


def build_conto_esterno_pdf(est: dict, lavori: list, cantiere_doc: dict, anno=None) -> bytes:
    """Conto lavori per cliente esterno (solo nominativo): elenco interventi, articoli e totale."""
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4, leftMargin=12*mm, rightMargin=12*mm, topMargin=10*mm, bottomMargin=8*mm,
                            title=f"Conto lavori {est.get('nome', '')}")
    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#0F1B3D")
    TEAK = colors.HexColor("#B0562E")
    SAND = colors.HexColor("#F3EFE7")
    MUTED = colors.HexColor("#5B6478")
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=9, textColor=TEAK, spaceBefore=6, spaceAfter=2, leading=11)
    body = ParagraphStyle("body", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=NAVY, leading=11)
    small = ParagraphStyle("small", parent=body, fontSize=7.5, textColor=MUTED, leading=9)
    val = ParagraphStyle("val", parent=body, fontName="Helvetica-Bold", fontSize=11)

    nome_cantiere = (cantiere_doc.get("nome") or "PORTOMARE").upper()
    parts = [x for x in [cantiere_doc.get("indirizzo"), " ".join(filter(None, [cantiere_doc.get("cap"), cantiere_doc.get("citta")])), cantiere_doc.get("telefono"), cantiere_doc.get("email"), cantiere_doc.get("piva") and f"P.IVA {cantiere_doc.get('piva')}"] if x]
    logo_cell = Paragraph(f"<b>{nome_cantiere}</b>", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY))
    logo_b64 = cantiere_doc.get("logo_base64") or ""
    if logo_b64 and "," in logo_b64:
        try:
            logo_cell = RLImage(io.BytesIO(_b64.b64decode(logo_b64.split(",", 1)[1])), width=30*mm, height=18*mm, kind="proportional")
        except Exception:
            pass
    periodo = f"Anno {anno}" if anno else "Tutti i lavori"
    elems = [Table([[logo_cell, Paragraph(f"<para align=right><font color='#5B6478' size=8>CONTO LAVORI</font><br/><font size=13 color='#B0562E'><b>{periodo}</b></font><br/><font color='#5B6478' size=8>{date.today().strftime('%d/%m/%Y')}</font></para>", body)]], colWidths=[100*mm, 86*mm])]
    elems[0].setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    if parts:
        elems.append(Paragraph(" · ".join(parts), small))
    sep = Table([[""]], colWidths=[186*mm], rowHeights=[1.5])
    sep.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TEAK)]))
    elems += [Spacer(1, 2*mm), sep, Spacer(1, 3*mm), Paragraph("CLIENTE", h2), Paragraph(f"<b>{est.get('nome', '')}</b>", val)]
    contatti = " · ".join(x for x in [est.get("telefono"), est.get("note")] if x)
    if contatti:
        elems.append(Paragraph(contatti, small))

    elems.append(Paragraph("DETTAGLIO LAVORI", h2))
    rows = [["DATA", "LAVORO", "ORE", "IMPORTO"]]
    totale = 0.0
    ore_tot = 0.0
    for l in lavori:
        descr = (l.get("descrizione") or "").strip()
        testo = f"<b>{l.get('tipo', '')}</b>" + (f" — {descr}" if descr else "")
        if l.get("dipendente"):
            testo += f"<br/><font size=7 color='#5B6478'>eseguito da {l['dipendente']}</font>"
        if l.get("materiali"):
            testo += f"<br/><font size=7 color='#5B6478'>Materiali: {l['materiali']}</font>"
        for it in (l.get("articoli_magazzino") or []):
            testo += f"<br/><font size=7 color='#5B6478'>· {it.get('nome', '')} × {it.get('quantita'):g} — {_euro(float(it.get('totale') or 0))}</font>"
        ore = float(l.get("ore") or 0)
        costo = float(l.get("costo") or 0)
        totale += costo
        ore_tot += ore
        rows.append([l.get("data", ""), Paragraph(testo, body), f"{ore:g}" if ore else "—", _euro(costo)])
    if len(rows) == 1:
        rows.append(["—", Paragraph("Nessun lavoro registrato", body), "—", _euro(0)])
    rows.append(["", Paragraph("<b>TOTALE</b>", body), f"{ore_tot:g}" if ore_tot else "", _euro(totale)])
    tbl = Table(rows, colWidths=[22*mm, 112*mm, 14*mm, 38*mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, SAND]),
        ("BACKGROUND", (0, -1), (-1, -1), SAND), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, TEAK), ("GRID", (0, 0), (-1, -2), 0.25, colors.HexColor("#D9D4C7")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems += [tbl, Spacer(1, 6*mm), Paragraph("Importi IVA esclusa salvo diversa indicazione. Documento non valido ai fini fiscali.", small)]
    pdf.build(elems)
    return buf.getvalue()


def build_documento_servizio_pdf(cantiere_doc: dict, sottotitolo: str, blocchi: list, note: str = "", testo: str = "",
                                 firma_nome: str = "", consenso: bool = False) -> bytes:
    """Documento di servizio su carta intestata. Il modulo consenso viene compattato finché non sta in un unico foglio A4."""
    scale_steps = [1.0, 0.92, 0.85, 0.78, 0.72, 0.66] if consenso else [1.0]
    out = b""
    for sc in scale_steps:
        out, pages = _build_documento_servizio(cantiere_doc, sottotitolo, blocchi, note, testo, firma_nome, consenso, sc)
        if pages <= 1:
            break
    return out


def _build_documento_servizio(cantiere_doc, sottotitolo, blocchi, note, testo, firma_nome, consenso, sc):
    from xml.sax.saxutils import escape
    buf = io.BytesIO()
    m = 16*mm if sc == 1.0 else 11*mm
    pdf = SimpleDocTemplate(buf, pagesize=A4, leftMargin=m, rightMargin=m, topMargin=9*mm if sc < 1 else 12*mm, bottomMargin=9*mm if sc < 1 else 14*mm, title=sottotitolo)
    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#0F1B3D"); TEAK = colors.HexColor("#B0562E"); SAND = colors.HexColor("#F3EFE7"); MUTED = colors.HexColor("#5B6478")
    body = ParagraphStyle("body", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5*sc, textColor=NAVY, leading=13*sc)
    small = ParagraphStyle("small", parent=body, fontSize=7.5*sc, textColor=MUTED, leading=9*sc)
    h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=9*sc, textColor=TEAK, spaceBefore=8*sc, spaceAfter=3*sc)
    key = ParagraphStyle("key", parent=body, fontSize=8, textColor=MUTED)
    valb = ParagraphStyle("valb", parent=body, fontName="Helvetica-Bold", fontSize=10.5)
    mono = ParagraphStyle("mono", parent=valb, fontName="Courier-Bold", fontSize=12, leading=15)

    nome_cantiere = (cantiere_doc.get("nome") or "PORTOMARE").upper()
    parts = [x for x in [cantiere_doc.get("indirizzo"), " ".join(filter(None, [cantiere_doc.get("cap"), cantiere_doc.get("citta")])), cantiere_doc.get("telefono"), cantiere_doc.get("email"), cantiere_doc.get("piva") and f"P.IVA {cantiere_doc.get('piva')}"] if x]
    logo_cell = Paragraph(f"<b>{escape(nome_cantiere)}</b>", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=17, textColor=NAVY))
    logo_b64 = cantiere_doc.get("logo_base64") or ""
    if logo_b64 and "," in logo_b64:
        try:
            logo_cell = RLImage(io.BytesIO(_b64.b64decode(logo_b64.split(",", 1)[1])), width=30*mm, height=18*mm, kind="proportional")
        except Exception:
            pass
    head = Table([[logo_cell, Paragraph(f"<para align=right><font size=13 color='#B0562E'><b>{escape(sottotitolo)}</b></font><br/><font color='#5B6478' size=8>{date.today().strftime('%d/%m/%Y')}</font></para>", body)]], colWidths=[100*mm, 78*mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    sep = Table([[""]], colWidths=[178*mm], rowHeights=[1.5]); sep.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TEAK)]))
    elems = [head] + ([Paragraph(escape(" · ".join(parts)), small)] if parts else []) + [Spacer(1, 2*mm), sep, Spacer(1, 4*mm)]

    for titolo, righe in blocchi:
        elems.append(Paragraph(escape(titolo), h2))
        rows = [[Paragraph(escape(k), key), Paragraph(escape(str(v or "—")), mono if k in ("IBAN", "CIN", "ABI", "CAB", "Numero conto", "BIC / SWIFT") else valb)] for k, v in righe]
        t = Table(rows, colWidths=[40*mm, 138*mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SAND), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D4C7")),
                               ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
        elems += [t, Spacer(1, 3*mm)]

    if testo:
        for par in testo.split("\n"):
            par = par.strip()
            if not par:
                elems.append(Spacer(1, 2*mm*sc)); continue
            is_title = par.isupper() or re.match(r"^\d+\.\s+[A-ZÀ-Ü]", par)
            elems.append(Paragraph(escape(par), h2 if is_title else body))

    if consenso:
        elems += [Spacer(1, 6*mm*sc), Paragraph("CONSENSO", h2),
                  Paragraph("Il/La sottoscritto/a, letta l'informativa che precede:", body), Spacer(1, 2*mm),
                  Paragraph("☐ ACCONSENTE &nbsp;&nbsp; ☐ NON ACCONSENTE &nbsp;&nbsp; al trattamento dei dati per finalità di comunicazione commerciale e promozionale (punto 1.d).", body),
                  Spacer(1, 2*mm),
                  Paragraph("Dichiara inoltre di aver preso visione dell'informativa per le finalità contrattuali, amministrative e di servizio (punti 1.a, 1.b, 1.c).", body),
                  Spacer(1, 10*mm*sc)]
        firma = Table([[Paragraph(f"Nome e cognome<br/><b>{escape(firma_nome) if firma_nome else '&nbsp;'}</b>", key), Paragraph("Data<br/>&nbsp;", key), Paragraph("Firma<br/>&nbsp;", key)]],
                      colWidths=[70*mm, 40*mm, 68*mm], rowHeights=[16*mm*sc])
        firma.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.8, NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elems.append(firma)

    if note:
        elems += [Spacer(1, 6*mm), Paragraph(escape(note), small)]
    pdf.build(elems)
    return buf.getvalue(), pdf.page


def build_preventivo_esterno_pdf(p: dict, est: dict, cantiere_doc: dict) -> bytes:
    """Preventivo per cliente esterno: righe manodopera/articoli/voci, sconto, IVA, totale."""
    from xml.sax.saxutils import escape
    from datetime import datetime as _dt, timedelta as _td
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14*mm, rightMargin=14*mm, topMargin=10*mm, bottomMargin=10*mm, title=f"Preventivo {p['numero']}/{p['anno']}")
    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#0F1B3D"); TEAK = colors.HexColor("#B0562E"); SAND = colors.HexColor("#F3EFE7"); MUTED = colors.HexColor("#5B6478")
    body = ParagraphStyle("body", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=NAVY, leading=11.5)
    small = ParagraphStyle("small", parent=body, fontSize=7.5, textColor=MUTED, leading=9)
    h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=9, textColor=TEAK, spaceBefore=6, spaceAfter=2)
    nome_cantiere = (cantiere_doc.get("nome") or "PORTOMARE").upper()
    parts = [x for x in [cantiere_doc.get("indirizzo"), " ".join(filter(None, [cantiere_doc.get("cap"), cantiere_doc.get("citta")])), cantiere_doc.get("telefono"), cantiere_doc.get("email"), cantiere_doc.get("piva") and f"P.IVA {cantiere_doc.get('piva')}"] if x]
    logo_cell = Paragraph(f"<b>{escape(nome_cantiere)}</b>", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=17, textColor=NAVY))
    logo_b64 = cantiere_doc.get("logo_base64") or ""
    if logo_b64 and "," in logo_b64:
        try:
            logo_cell = RLImage(io.BytesIO(_b64.b64decode(logo_b64.split(",", 1)[1])), width=30*mm, height=18*mm, kind="proportional")
        except Exception:
            pass
    try:
        scad = (_dt.strptime(p.get("data", ""), "%Y-%m-%d") + _td(days=int(p.get("validita_giorni") or 30))).strftime("%d/%m/%Y")
    except Exception:
        scad = ""
    head = Table([[logo_cell, Paragraph(f"<para align=right><font color='#5B6478' size=8>PREVENTIVO</font><br/><font size=14 color='#B0562E'><b>N. {p['numero']}/{p['anno']}</b></font><br/><font color='#5B6478' size=8>del {escape(str(p.get('data', '')))}{(' · valido fino al ' + scad) if scad else ''}</font></para>", body)]], colWidths=[100*mm, 82*mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    sep = Table([[""]], colWidths=[182*mm], rowHeights=[1.5]); sep.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TEAK)]))
    elems = [head] + ([Paragraph(escape(" · ".join(parts)), small)] if parts else []) + [Spacer(1, 2*mm), sep, Spacer(1, 3*mm),
             Paragraph("SPETT.LE", h2), Paragraph(f"<b>{escape(est.get('nome', ''))}</b>", ParagraphStyle("v", parent=body, fontSize=11))]
    contatti = " · ".join(x for x in [est.get("telefono"), est.get("note")] if x)
    if contatti:
        elems.append(Paragraph(escape(contatti), small))
    if p.get("oggetto"):
        elems += [Paragraph("OGGETTO", h2), Paragraph(escape(p["oggetto"]), body)]
    elems.append(Paragraph("DETTAGLIO", h2))
    TIPO = {"manodopera": "Manodopera", "articolo": "Ricambio", "voce": "Voce"}
    rows = [["TIPO", "DESCRIZIONE", "Q.TÀ", "PREZZO", "IMPORTO"]]
    for r in p.get("righe", []):
        q = float(r.get("quantita") or 0); pu = float(r.get("prezzo_unitario") or 0)
        descr = escape(r.get("descrizione", "")) + (f" <font size=7 color='#5B6478'>[{escape(r['codice'])}]</font>" if r.get("codice") else "")
        rows.append([TIPO.get(r.get("tipo"), "Voce"), Paragraph(descr, body), f"{q:g}" + (" h" if r.get("tipo") == "manodopera" else ""), _euro(pu), _euro(q * pu)])
    tbl = Table(rows, colWidths=[24*mm, 86*mm, 18*mm, 26*mm, 28*mm], repeatRows=1)
    tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                             ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (2, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SAND]), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D4C7")),
                             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    elems += [tbl, Spacer(1, 3*mm)]
    tot_rows = [["Imponibile", _euro(p.get("imponibile", 0))]]
    if float(p.get("sconto_pct") or 0) > 0:
        tot_rows += [[f"Sconto {p['sconto_pct']:g}%", "- " + _euro(p.get("sconto", 0))], ["Netto", _euro(p.get("netto", 0))]]
    tot_rows += [[f"IVA {float(p.get('iva_pct') or 0):g}%", _euro(p.get("iva", 0))], ["TOTALE", _euro(p.get("totale", 0))]]
    tt = Table(tot_rows, colWidths=[40*mm, 34*mm], hAlign="RIGHT")
    tt.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                            ("BACKGROUND", (0, -1), (-1, -1), SAND), ("LINEABOVE", (0, -1), (-1, -1), 1, TEAK), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    elems.append(tt)
    if p.get("note"):
        elems += [Paragraph("NOTE", h2), Paragraph(escape(p["note"]), body)]
    elems += [Spacer(1, 8*mm), Paragraph("Per accettazione (data e firma): ____________________________________", body),
              Spacer(1, 3*mm), Paragraph("Prezzi validi per il periodo indicato. I ricambi sono soggetti a disponibilità di magazzino.", small)]
    pdf.build(elems)
    return buf.getvalue()
