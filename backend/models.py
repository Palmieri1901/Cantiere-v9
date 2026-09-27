"""Pydantic models for the Cantiere Nautico API."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class Tariffe(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: "default")
    copertura_per_metro: float = 45.0
    alaggio_fino_5m: float = 90.0
    alaggio_oltre_5m_per_metro: float = 25.0
    varo_fino_5m: float = 90.0
    varo_oltre_5m_per_metro: float = 25.0
    antivegetativa_per_metro: float = 60.0
    sosta_temporanea_giornaliera: float = 25.0
    motore_labor_2_15hp: float = 90.0
    motore_labor_fino_40hp: float = 180.0
    motore_labor_40_150hp: float = 320.0
    motore_labor_oltre_150hp: float = 550.0
    # Manodopera unica valida per motori entrobordo (qualsiasi HP)
    motore_labor_entrobordo: float = 250.0
    costo_girante: float = 45.0
    costo_olio_motore: float = 12.0
    costo_filtro_olio: float = 18.0
    costo_candela: float = 12.0
    costo_termostato: float = 35.0
    costo_olio_piede: float = 25.0
    costo_anodi_interni: float = 40.0
    costo_anodi_esterni: float = 60.0
    costo_ingrassaggio: float = 30.0
    sosta_dentro_per_metro: float = 180.0
    sosta_fuori_per_metro: float = 120.0
    costo_movimentazione_per_metro: float = 25.0
    costo_taccaggio_per_metro: float = 20.0
    costo_lavaggio_inizio_stagione: float = 80.0
    costo_lavaggio_fine_stagione: float = 80.0
    maggiorazione_scafo_sporco_per_metro: float = 15.0
    costo_orario_manodopera: float = 45.0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TariffeUpdate(BaseModel):
    """Partial update per Tariffe: tutti i campi opzionali."""
    model_config = ConfigDict(extra="ignore")

    copertura_per_metro: Optional[float] = None
    alaggio_fino_5m: Optional[float] = None
    alaggio_oltre_5m_per_metro: Optional[float] = None
    varo_fino_5m: Optional[float] = None
    varo_oltre_5m_per_metro: Optional[float] = None
    antivegetativa_per_metro: Optional[float] = None
    sosta_temporanea_giornaliera: Optional[float] = None
    motore_labor_2_15hp: Optional[float] = None
    motore_labor_fino_40hp: Optional[float] = None
    motore_labor_40_150hp: Optional[float] = None
    motore_labor_oltre_150hp: Optional[float] = None
    motore_labor_entrobordo: Optional[float] = None
    costo_girante: Optional[float] = None
    costo_olio_motore: Optional[float] = None
    costo_filtro_olio: Optional[float] = None
    costo_candela: Optional[float] = None
    costo_termostato: Optional[float] = None
    costo_olio_piede: Optional[float] = None
    costo_anodi_interni: Optional[float] = None
    costo_anodi_esterni: Optional[float] = None
    costo_ingrassaggio: Optional[float] = None
    costo_orario_manodopera: Optional[float] = None
    sosta_dentro_per_metro: Optional[float] = None
    sosta_fuori_per_metro: Optional[float] = None
    costo_movimentazione_per_metro: Optional[float] = None
    costo_taccaggio_per_metro: Optional[float] = None
    costo_lavaggio_inizio_stagione: Optional[float] = None
    costo_lavaggio_fine_stagione: Optional[float] = None
    maggiorazione_scafo_sporco_per_metro: Optional[float] = None


class Cliente(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    cognome: str
    tipo_barca: str
    lunghezza: float
    tipo_sosta: str
    giorni_sosta_temporanea: int = 0
    anno: int = Field(default_factory=lambda: datetime.now().year)
    posto_barca: Optional[int] = None
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    codice_fiscale: Optional[str] = ""
    indirizzo: Optional[str] = ""
    cellulare: Optional[str] = ""
    pagato: bool = False
    data_pagamento: Optional[str] = None
    potenza_motore: float = 0.0
    litri_olio_motore: float = 3.0
    litri_olio_piede: float = 1.0
    numero_candele: int = 4
    numero_termostati: int = 1
    tipo_motore: str = "fuoribordo"  # "fuoribordo" | "entrobordo"
    filtro_olio_attivo: bool = True
    anodi_interni_attivo: bool = True
    anodi_esterni_attivo: bool = True
    olio_piede_attivo: bool = True
    ingrassaggio_attivo: bool = True
    primo_motore_attivo: bool = True
    secondo_motore: bool = False
    potenza_motore_2: float = 0.0
    litri_olio_motore_2: float = 3.0
    litri_olio_piede_2: float = 1.0
    numero_candele_2: int = 4
    numero_termostati_2: int = 1
    tipo_motore_2: str = "fuoribordo"
    filtro_olio_2_attivo: bool = True
    anodi_interni_2_attivo: bool = True
    anodi_esterni_2_attivo: bool = True
    olio_piede_2_attivo: bool = True
    ingrassaggio_2_attivo: bool = True
    girante_2_attivo: bool = True
    antivegetativa_attiva: bool = True
    scafo_sporco_attivo: bool = False
    copertura_attiva: bool = False
    girante_attivo: bool = True
    lavaggio_inizio_attivo: bool = True
    lavaggio_fine_attivo: bool = True
    alaggio_varo_attivo: bool = False
    numero_movimenti: int = 1
    destinazione_alaggio_varo: str = "marina_di_campo"
    destinazione_altra_nome: Optional[str] = ""
    larghezza_personalizzata: Optional[float] = None
    costo_sosta: float = 0.0
    costo_copertura: float = 0.0
    costo_alaggio: float = 0.0
    costo_varo: float = 0.0
    costo_antivegetativa: float = 0.0
    costo_manutenzione_motore: float = 0.0
    costo_lavaggio_inizio: float = 0.0
    costo_lavaggio_fine: float = 0.0
    costo_scafo_sporco: float = 0.0
    costo_movimentazione: float = 0.0
    costo_taccaggio: float = 0.0
    costo_ricambi_totale: float = 0.0
    costo_manodopera_motore: float = 0.0
    costo_ricambi_motore_2_totale: float = 0.0
    costo_manodopera_motore_2: float = 0.0
    lavorazioni_extra: List[dict] = Field(default_factory=list)
    costo_lavori: float = 0.0
    lavori_storico: List[dict] = Field(default_factory=list)
    override_costi: bool = False
    note_lavori: str = ""
    scadenza_antivegetativa: Optional[str] = None
    scadenza_manutenzione: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClienteCreate(BaseModel):
    nome: str
    cognome: str
    tipo_barca: str
    lunghezza: float
    tipo_sosta: str
    giorni_sosta_temporanea: Optional[int] = None
    anno: Optional[int] = None
    posto_barca: Optional[int] = None
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    codice_fiscale: Optional[str] = ""
    indirizzo: Optional[str] = ""
    cellulare: Optional[str] = ""
    pagato: Optional[bool] = None
    data_pagamento: Optional[str] = None
    potenza_motore: Optional[float] = 0.0
    litri_olio_motore: Optional[float] = 3.0
    litri_olio_piede: Optional[float] = None
    numero_candele: Optional[int] = 4
    numero_termostati: Optional[int] = 1
    tipo_motore: Optional[str] = None
    filtro_olio_attivo: Optional[bool] = None
    anodi_interni_attivo: Optional[bool] = None
    anodi_esterni_attivo: Optional[bool] = None
    olio_piede_attivo: Optional[bool] = None
    ingrassaggio_attivo: Optional[bool] = None
    secondo_motore: Optional[bool] = False
    primo_motore_attivo: Optional[bool] = None
    potenza_motore_2: Optional[float] = 0.0
    litri_olio_motore_2: Optional[float] = 3.0
    litri_olio_piede_2: Optional[float] = None
    numero_candele_2: Optional[int] = 4
    numero_termostati_2: Optional[int] = 1
    tipo_motore_2: Optional[str] = None
    filtro_olio_2_attivo: Optional[bool] = None
    anodi_interni_2_attivo: Optional[bool] = None
    anodi_esterni_2_attivo: Optional[bool] = None
    olio_piede_2_attivo: Optional[bool] = None
    ingrassaggio_2_attivo: Optional[bool] = None
    girante_2_attivo: Optional[bool] = None
    antivegetativa_attiva: Optional[bool] = True
    scafo_sporco_attivo: Optional[bool] = None
    copertura_attiva: Optional[bool] = None
    girante_attivo: Optional[bool] = True
    lavaggio_inizio_attivo: Optional[bool] = True
    lavaggio_fine_attivo: Optional[bool] = True
    costo_sosta: Optional[float] = None
    costo_copertura: Optional[float] = None
    costo_alaggio: Optional[float] = None
    costo_varo: Optional[float] = None
    alaggio_varo_attivo: Optional[bool] = None
    numero_movimenti: Optional[int] = None
    destinazione_alaggio_varo: Optional[str] = None
    destinazione_altra_nome: Optional[str] = None
    larghezza_personalizzata: Optional[float] = None
    costo_antivegetativa: Optional[float] = None
    costo_manutenzione_motore: Optional[float] = None
    costo_lavaggio_inizio: Optional[float] = None
    costo_lavaggio_fine: Optional[float] = None
    costo_scafo_sporco: Optional[float] = None
    costo_movimentazione: Optional[float] = None
    costo_taccaggio: Optional[float] = None
    lavorazioni_extra: Optional[List[dict]] = None
    override_costi: bool = False
    note_lavori: str = ""
    scadenza_antivegetativa: Optional[str] = None
    scadenza_manutenzione: Optional[str] = None


class Lavoro(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cliente_id: str
    data: str
    tipo: str
    descrizione: str = ""
    costo: float = 0.0
    materiali: str = ""
    stato: str = "completato"
    ore: float = 0.0
    dipendente: str = ""
    anno: int = Field(default_factory=lambda: datetime.now().year)
    articoli_magazzino: List[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LavoroCreate(BaseModel):
    cliente_id: str
    data: str
    tipo: str
    descrizione: Optional[str] = ""
    costo: Optional[float] = 0.0
    materiali: Optional[str] = ""
    stato: Optional[str] = "completato"
    ore: Optional[float] = 0.0
    dipendente: Optional[str] = ""
    anno: Optional[int] = None
    articoli_magazzino: Optional[List[dict]] = None


class Cantiere(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: "default")
    nome: str = "Portomare"
    slogan: str = "Cantiere nautico dal 1985"
    indirizzo: str = ""
    citta: str = ""
    cap: str = ""
    provincia: str = ""
    telefono: str = ""
    email: str = ""
    piva: str = ""
    sito_web: str = ""
    orari: str = ""
    logo_base64: str = ""
    iva_percentuale: float = 22.0  # aliquota IVA globale usata in tutti i calcoli (Suzuki, ecc.)
    # Blocchi testuali stampati in coda al preventivo PDF (editabili)
    preventivo_interno_titolo: str = "Interno cantiere:"
    preventivo_interno_testo: str = (
        "Previa disponibilità posti, il servizio prevede:\n"
        "Alaggio/varo con camion e gru se necessario · sosta in cantiere al coperto · "
        "assicurazione Incendio/furto · rimessaggio · tagliando al motore "
        "(ricambi e materiali di consumo INCLUSI: olio, filtri, anodi, ecc.) · 2 lavaggi."
    )
    preventivo_piazzale_titolo: str = "Con sosta su piazzale:"
    preventivo_piazzale_testo: str = (
        "Previa disponibilità posti, il servizio prevede:\n"
        "Alaggio/varo con camion e gru se necessario · sosta su piazzale · "
        "copertura con telo termorestringente · rimessaggio · tagliando al motore "
        "(ricambi e materiali di consumo INCLUSI: olio, filtri, anodi, ecc.) · 2 lavaggi.\n"
        "Nessuna forma di assicurazione."
    )
    preventivo_esclusi_titolo: str = "Esclusi dal servizio sono:"
    preventivo_esclusi_testo: str = ""
    preventivo_condizioni_titolo: str = "Condizioni:"
    preventivo_condizioni_testo: str = (
        "1) Qualora il natante non vada in mare per cause non dipendenti dal cantiere, "
        "verrà applicato solo uno sconto del 10% sull'importo totale.\n"
        "2) Le tariffe di cui sopra sono comprensive di IVA e delle quote di assicurazione dove specificato.\n"
        "3) Le tariffe relative alle voci 'sosta' sono relative ai metri quadrati di superficie occupata "
        "e valevoli dal 1 settembre al 31 agosto di ogni anno.\n"
        "4) Per la riconsegna del mezzo è richiesto un preavviso di 15 giorni.\n"
        "5) In caso di sosta su piazzale, per furti o danni dovuti alla maggiore usura causati da intemperie "
        "o condense (muffe, abrasioni, ecc.) il cantiere non si ritiene responsabile.\n"
        "6) Foro competente: Portoferraio.\n"
        "7) L'alaggio e il varo sono considerati dal porto di Marina di Campo.\n"
        "8) Il cantiere non si assume alcuna responsabilità per gli oggetti lasciati sulle barche."
    )
    # Testo di default della pagina Contratti
    contratto_template: str = (
        "Allegato al preventivo n. ______________ del ____/____/________ che ne è parte integrante\n\n"
        "**1. PARTI E DATI**\n"
        "Cliente: {{cognome}} {{nome}}\n"
        "Nato/a a: ____________________  Il: ____/____/________\n"
        "C.F.: {{codice_fiscale}}   P.IVA: ____________________\n"
        "Residente: {{indirizzo}}\n"
        "Tel. / Email: {{telefono}}  ·  {{email}}\n"
        "Imbarcazione: {{tipo_barca}}   Lunghezza: {{lunghezza}} m\n"
        "Matricola: ____________________   Motore: {{potenza_motore}}\n"
        "Posto barca: {{posto_barca}}   Valore dichiarato EUR: ______________\n"
        "Periodo: dal ____/____/________ al ____/____/________\n\n"
        "**2. OGGETTO E QUALIFICA GIURIDICA**\n"
        "Il presente contratto ha natura di **locazione del posto barca** indicato sopra e di "
        "**contratto d'opera** per i servizi di manutenzione descritti nel preventivo allegato. "
        "**Non si configura alcun rapporto di deposito, custodia o comodato** dell'imbarcazione. "
        "Il Cantiere garantisce esclusivamente la disponibilità del posto e l'esecuzione dei lavori concordati.\n\n"
        "**3. OGGETTI A BORDO E RESPONSABILITÀ**\n"
        "Il Cliente dichiara di aver rimosso dall'imbarcazione oggetti di valore, elettronica, attrezzi, "
        "documenti ed effetti personali prima della consegna. Il Cantiere **non risponde in alcun modo** "
        "della scomparsa, del danneggiamento o del deterioramento di qualsiasi oggetto lasciato a bordo, "
        "né di danni causati da essi a terzi o alle strutture del Cantiere.\n"
        "Il Cliente consegna l'imbarcazione nello stato in cui si trova e la ritira nello stesso stato, "
        "salvo i lavori di manutenzione concordati. Eventuali difetti o danni preesistenti sono a carico del Cliente.\n\n"
        "**4. ASSICURAZIONE**\n"
        "Il Cliente dichiara di mantenere attiva una polizza che copra furto, incendio, danni atmosferici e "
        "RC verso terzi, indicando il Cantiere come **contraente beneficiario** o comunicandone i dati. "
        "In caso di sinistro il Cliente si rivarrà esclusivamente sulla propria assicurazione.\n\n"
        "**5. LIMITAZIONE DI RESPONSABILITÀ**\n"
        "La responsabilità del Cantiere, ove accertata, è limitata ai soli danni diretti e prevedibili, "
        "al valore dichiarato e in ogni caso a un massimo di EUR ______________. Sono esclusi: eventi "
        "atmosferici eccezionali, terremoti, allagamenti, atti vandalici, **furti commessi da terzi**, "
        "incendi non imputabili, difetti preesistenti, danni causati da terzi durante movimentazione "
        "(salvo colpa grave del Cantiere). Non sono dovuti danni morali o mancato guadagno.\n\n"
        "**6. SICUREZZA**\n"
        "Il Cantiere mantiene l'area recintata con accesso controllato negli orari di apertura, "
        "**senza obblighi di vigilanza notturna o custodia specifica**. Il Cantiere non risponde di "
        "furti o danneggiamenti da terzi salvo negligenza specifica (es. mancata chiusura del cancello).\n\n"
        "**7. PAGAMENTO, RITENZIONE E RICONSEGNA**\n"
        "Pagamento secondo il preventivo allegato. Il Cantiere potrà esercitare il diritto di ritenzione "
        "sull'imbarcazione solo dopo **messa in mora di 15 giorni**. Riconsegna previo preavviso di 15 giorni, "
        "saldo dei corrispettivi e sottoscrizione del verbale di uscita.\n\n"
        "**8. CONTESTAZIONI E DECADENZA**\n"
        "Danni o mancanze devono essere contestati **per iscritto alla riconsegna, o entro 24 ore se occulti**. "
        "Decorso tale termine, ogni pretesa si intende decaduta. In caso di furto il Cliente deve sporgere "
        "denuncia entro 24 ore.\n\n"
        "**9. MANLEVA**\n"
        "Il Cliente manleva e tiene indenne il Cantiere da qualsiasi richiesta di terzi (assicurazioni, "
        "passeggeri, armatori parziali, enti pubblici) per danni a cose o persone verificatisi durante il "
        "rimessaggio, salvo dolo del Cantiere.\n\n"
        "**10. FORO COMPETENTE**\n"
        "Per qualsiasi controversia è competente il Foro di **Livorno**.\n\n"
        "**11. CLAUSOLE VESSATORIE - ART. 1341 C.C.**\n"
        "Il Cliente, con apposizione della firma qui sotto, dichiara di aver letto, compreso e "
        "**specificamente approvato** le seguenti clausole: **nn. 2, 3, 4, 5, 6, 7, 8, 9**."
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CantiereUpdate(BaseModel):
    nome: Optional[str] = None
    slogan: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    provincia: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    piva: Optional[str] = None
    sito_web: Optional[str] = None
    orari: Optional[str] = None
    logo_base64: Optional[str] = None
    iva_percentuale: Optional[float] = None
    preventivo_interno_titolo: Optional[str] = None
    preventivo_interno_testo: Optional[str] = None
    preventivo_piazzale_titolo: Optional[str] = None
    preventivo_piazzale_testo: Optional[str] = None
    preventivo_esclusi_titolo: Optional[str] = None
    preventivo_esclusi_testo: Optional[str] = None
    preventivo_condizioni_titolo: Optional[str] = None
    preventivo_condizioni_testo: Optional[str] = None
    contratto_template: Optional[str] = None


class PreventivoInline(ClienteCreate):
    """Payload preventivo veloce: solo nome e cognome sono obbligatori."""
    nome: str
    cognome: str
    tipo_barca: Optional[str] = "—"
    lunghezza: Optional[float] = 0.0
    tipo_sosta: Optional[str] = "dentro"


class RestoreRequest(BaseModel):
    version: Optional[int] = None
    cantiere: Optional[dict] = None
    tariffe: Optional[dict] = None
    clienti: Optional[List[dict]] = None
    lavori: Optional[List[dict]] = None
    articoli: Optional[List[dict]] = None
    fornitori: Optional[List[dict]] = None
    ricarichi_categoria: Optional[List[dict]] = None
    spese_accessorie: Optional[List[dict]] = None
    movimenti_magazzino: Optional[List[dict]] = None


class PagatoUpdate(BaseModel):
    pagato: bool


class ApriAnnoRequest(BaseModel):
    anno: int
    duplica_da: Optional[int] = None


class LoginRequest(BaseModel):
    # Email opzionale: l'app usa un utente unico condiviso, quindi in UI
    # viene chiesta solo la password. Se assente, viene usato ADMIN_EMAIL.
    email: Optional[str] = ""
    password: str


class PinResetRequest(BaseModel):
    pin: str
    new_password: str


class ChangePinRequest(BaseModel):
    current_pin: str
    new_pin: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    nome: Optional[str] = ""


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============================================================================
# MAGAZZINO - Articoli, Fornitori, Movimenti
# ============================================================================

class Fornitore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    abbreviazione: Optional[str] = ""
    user: Optional[str] = ""
    password: Optional[str] = ""
    note: Optional[str] = ""
    ricarico_default_percent: Optional[float] = None
    # Campi legacy mantenuti per compatibilità (non più mostrati in UI)
    referente: Optional[str] = ""
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    piva: Optional[str] = ""
    indirizzo: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FornitoreCreate(BaseModel):
    nome: str
    abbreviazione: Optional[str] = ""
    user: Optional[str] = ""
    password: Optional[str] = ""
    note: Optional[str] = ""
    ricarico_default_percent: Optional[float] = None
    referente: Optional[str] = ""
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    piva: Optional[str] = ""
    indirizzo: Optional[str] = ""


class Articolo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    codice: str = ""
    nome: str
    descrizione: Optional[str] = ""
    categoria: Optional[str] = ""
    fornitore_id: Optional[str] = None
    prezzo_acquisto: float = 0.0
    prezzo_listino: float = 0.0
    quantita: float = 0.0
    scorta_minima: float = 0.0
    unita_misura: Optional[str] = "pz"
    immagine_base64: Optional[str] = ""
    note: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArticoloCreate(BaseModel):
    codice: Optional[str] = ""
    nome: str
    descrizione: Optional[str] = ""
    categoria: Optional[str] = ""
    fornitore_id: Optional[str] = None
    prezzo_acquisto: Optional[float] = 0.0
    prezzo_listino: Optional[float] = 0.0
    quantita: Optional[float] = 0.0
    scorta_minima: Optional[float] = 0.0
    unita_misura: Optional[str] = "pz"
    immagine_base64: Optional[str] = ""
    note: Optional[str] = ""


class MovimentoMagazzino(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    articolo_id: str
    tipo: str  # "carico" | "scarico" | "rettifica"
    quantita: float  # positiva=carico, negativa=scarico, valore assoluto per rettifica
    quantita_dopo: float = 0.0
    motivo: Optional[str] = ""
    data: str  # ISO YYYY-MM-DD
    note: Optional[str] = ""
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = ""
    lavoro_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MovimentoCreate(BaseModel):
    articolo_id: str
    tipo: str
    quantita: float
    motivo: Optional[str] = ""
    data: Optional[str] = None
    note: Optional[str] = ""


class ScanArticoloRequest(BaseModel):
    image_base64: str


class ScanDDTRequest(BaseModel):
    image_base64: Optional[str] = None
    file_base64: Optional[str] = None
    mime_type: Optional[str] = None


class OrdineComposoItem(BaseModel):
    articolo_id: str
    quantita: float = 1
    nota: Optional[str] = ""


class OrdineComposto(BaseModel):
    items: List[OrdineComposoItem]
    fornitore_id: Optional[str] = None
    note: Optional[str] = ""


class RicaricoCategoria(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    categoria: str
    ricarico_percent: float = 30.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RicaricoCategoriaCreate(BaseModel):
    categoria: str
    ricarico_percent: float


class SpesaAccessoria(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: str  # bancarie | trasporto | imballo | spedizione | assicurazione | carburante | altro
    descrizione: str = ""
    importo: float = 0.0
    data: str  # ISO YYYY-MM-DD
    fornitore_id: Optional[str] = None
    fornitore_nome: Optional[str] = ""
    documento_ref: Optional[str] = ""  # numero DDT/fattura
    note: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SpesaCreate(BaseModel):
    tipo: str
    descrizione: Optional[str] = ""
    importo: float
    data: Optional[str] = None
    fornitore_id: Optional[str] = None
    fornitore_nome: Optional[str] = ""
    documento_ref: Optional[str] = ""
    note: Optional[str] = ""



# ============================================================================
# RIFACIMENTO TUBOLARI (sostituzione tubolari gommoni)
# ============================================================================


class TubolariConfig(BaseModel):
    """Configurazione prezzi del modulo Rifacimento Tubolari (singleton id=default)."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: "default")
    # Prezzo base al metro (Hypalon 1670 prima scelta)
    prezzo_al_metro: float = 1250.0
    # Supplemento se il cliente sceglie tessuto ORCA anziché Hypalon
    supplemento_orca: float = 357.0
    # Lavorazioni extra
    rifinitura_interna_strisciato: float = 382.50
    bottazzo_doppio_90mm: float = 357.0
    apposizione_pezze_velocita: float = 0.0  # 0 = "da valutare" nel PDF
    scritte_loghi_taglio_laser: float = 0.0  # 0 = "da valutare" nel PDF
    colori_tubo_differenti: float = 0.0      # 0 = "da valutare" nel PDF
    maniglione_aggiuntivo_cad: float = 50.0
    # Testi standard del preventivo (modificabili)
    validita_giorni: int = 90
    tempi_esecuzione_giorni: int = 90
    garanzia_mesi: int = 12
    note_standard: str = (
        "- I prezzi sono IVA esclusa\n"
        "- Franco cantiere chiavi in mano\n"
        "- 12 mesi garanzia sugli incollaggi\n"
        "- Validità preventivo 90 gg\n"
        "- Alaggi/vari/movimentazione del battello non sono inclusi nel preventivo"
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TubolariConfigUpdate(BaseModel):
    prezzo_al_metro: Optional[float] = None
    supplemento_orca: Optional[float] = None
    rifinitura_interna_strisciato: Optional[float] = None
    bottazzo_doppio_90mm: Optional[float] = None
    apposizione_pezze_velocita: Optional[float] = None
    scritte_loghi_taglio_laser: Optional[float] = None
    colori_tubo_differenti: Optional[float] = None
    maniglione_aggiuntivo_cad: Optional[float] = None
    validita_giorni: Optional[int] = None
    tempi_esecuzione_giorni: Optional[int] = None
    garanzia_mesi: Optional[int] = None
    note_standard: Optional[str] = None


class PreventivoTubolare(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero: Optional[str] = ""  # numero progressivo umano
    data: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    # Cliente (libero — non collegato a rubrica)
    cliente_nome: str = ""
    cliente_telefono: str = ""
    cliente_email: str = ""
    # Gommone
    marca_gommone: str = ""
    modello_gommone: str = ""
    metri: float = 0.0
    tessuto: str = "hypalon"  # hypalon | orca
    # Snapshot prezzi al momento della creazione (per non alterare i vecchi preventivi)
    prezzo_al_metro: float = 1250.0
    supplemento_orca: float = 357.0
    # Extra (checkbox on/off + quantità per maniglioni)
    include_rifinitura_strisciato: bool = False
    prezzo_rifinitura_strisciato: float = 382.50
    include_bottazzo_doppio: bool = False
    prezzo_bottazzo_doppio: float = 357.0
    include_pezze_velocita: bool = False
    prezzo_pezze_velocita: float = 0.0  # "da valutare" di default
    maniglioni_aggiuntivi: int = 0
    prezzo_maniglione: float = 50.0
    # Voci "da valutare" / variazioni
    scritte_loghi_laser: bool = False
    prezzo_scritte_loghi: float = 0.0
    colori_tubo_differenti: bool = False
    prezzo_colori_tubo_differenti: float = 0.0
    grafiche_particolari: bool = False
    prezzo_grafiche_particolari: float = 0.0
    rinforzi_diving: bool = False
    prezzo_rinforzi_diving: float = 0.0
    # Note e stato
    note: str = ""
    stato: str = "bozza"  # bozza | inviato | accettato | rifiutato
    totale: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PreventivoTubolareCreate(BaseModel):
    numero: Optional[str] = ""
    data: Optional[str] = None
    cliente_nome: Optional[str] = ""
    cliente_telefono: Optional[str] = ""
    cliente_email: Optional[str] = ""
    marca_gommone: Optional[str] = ""
    modello_gommone: Optional[str] = ""
    metri: Optional[float] = 0.0
    tessuto: Optional[str] = "hypalon"
    prezzo_al_metro: Optional[float] = None
    supplemento_orca: Optional[float] = None
    include_rifinitura_strisciato: Optional[bool] = False
    prezzo_rifinitura_strisciato: Optional[float] = None
    include_bottazzo_doppio: Optional[bool] = False
    prezzo_bottazzo_doppio: Optional[float] = None
    include_pezze_velocita: Optional[bool] = False
    prezzo_pezze_velocita: Optional[float] = 0.0
    maniglioni_aggiuntivi: Optional[int] = 0
    prezzo_maniglione: Optional[float] = None
    scritte_loghi_laser: Optional[bool] = False
    prezzo_scritte_loghi: Optional[float] = 0.0
    colori_tubo_differenti: Optional[bool] = False
    prezzo_colori_tubo_differenti: Optional[float] = 0.0
    grafiche_particolari: Optional[bool] = False
    prezzo_grafiche_particolari: Optional[float] = 0.0
    rinforzi_diving: Optional[bool] = False
    prezzo_rinforzi_diving: Optional[float] = 0.0
    note: Optional[str] = ""
    stato: Optional[str] = "bozza"


# =============================================================================
# MODULO FUORIBORDO SUZUKI
# =============================================================================

class SuzukiModello(BaseModel):
    """Modello di fuoribordo Suzuki con specifiche tecniche e prezzi/sconti."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    codice: Optional[str] = ""                   # es. "DF9.9BS", codice articolo Suzuki
    modello: str                                  # es. "DF150ATL"
    potenza_hp: float = 0                         # es. 150
    cilindrata_cc: Optional[float] = 0            # es. 2867
    cilindri: Optional[str] = ""                  # es. "4 in linea"
    alimentazione: Optional[str] = ""             # es. "EFI iniezione elettronica"
    peso_kg: Optional[float] = 0
    avviamento: Optional[str] = ""                # "elettrico" / "manuale" / "elettrico + manuale"
    gambo: Optional[str] = ""                     # "S" / "L" / "UL" / "XL"
    trim: Optional[str] = ""                      # "PT&T" / "idraulico" / "manuale"
    comandi: Optional[str] = ""                   # "a distanza" / "da barra"
    alternatore_A: Optional[float] = 0
    categoria: Optional[str] = ""                 # es. "Portable" / "Mid range" / "V6"
    prezzo_listino: float = 0                     # € IVA esclusa, prezzo concessionario
    prezzo_pubblico: Optional[float] = 0          # € IVA inclusa, prezzo di listino pubblico
    prezzo_offerta: Optional[float] = 0           # € IVA inclusa, prezzo promozionale (opzionale)
    contributo_offerta: Optional[float] = 0       # € IVA escl., contributo casa madre al concessionario
    carburante: Optional[str] = ""                # es. "91 (87 RON US)"
    sconto_perc_1: Optional[float] = 0            # primo sconto es. 10%
    sconto_perc_2: Optional[float] = 0            # secondo sconto es. 5%
    note: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SuzukiModelloCreate(BaseModel):
    codice: Optional[str] = ""
    modello: str
    potenza_hp: Optional[float] = 0
    cilindrata_cc: Optional[float] = 0
    cilindri: Optional[str] = ""
    alimentazione: Optional[str] = ""
    peso_kg: Optional[float] = 0
    avviamento: Optional[str] = ""
    gambo: Optional[str] = ""
    trim: Optional[str] = ""
    comandi: Optional[str] = ""
    alternatore_A: Optional[float] = 0
    categoria: Optional[str] = ""
    prezzo_listino: Optional[float] = 0
    prezzo_pubblico: Optional[float] = 0
    prezzo_offerta: Optional[float] = 0
    contributo_offerta: Optional[float] = 0
    carburante: Optional[str] = ""
    sconto_perc_1: Optional[float] = 0
    sconto_perc_2: Optional[float] = 0
    note: Optional[str] = ""


class SuzukiModelloUpdate(BaseModel):
    codice: Optional[str] = None
    modello: Optional[str] = None
    potenza_hp: Optional[float] = None
    cilindrata_cc: Optional[float] = None
    cilindri: Optional[str] = None
    alimentazione: Optional[str] = None
    peso_kg: Optional[float] = None
    avviamento: Optional[str] = None
    gambo: Optional[str] = None
    trim: Optional[str] = None
    comandi: Optional[str] = None
    alternatore_A: Optional[float] = None
    categoria: Optional[str] = None
    prezzo_listino: Optional[float] = None
    prezzo_pubblico: Optional[float] = None
    prezzo_offerta: Optional[float] = None
    contributo_offerta: Optional[float] = None
    carburante: Optional[str] = None
    sconto_perc_1: Optional[float] = None
    sconto_perc_2: Optional[float] = None
    note: Optional[str] = None


class SuzukiPreventivo(BaseModel):
    """Preventivo per un fuoribordo Suzuki con sconto composto (es. 10% + 5%)
    e voce montaggio opzionale."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero: Optional[str] = ""
    data: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    # cliente
    cliente_nome: str = ""
    cliente_telefono: Optional[str] = ""
    cliente_email: Optional[str] = ""
    # modello (snapshot al momento della creazione)
    modello_id: Optional[str] = ""
    codice: Optional[str] = ""
    modello: str = ""
    potenza_hp: Optional[float] = 0
    specifiche: Optional[str] = ""                # riepilogo tecnico legacy (compatibilità)
    # snapshot campi tecnici strutturati (per rendering PDF a colonne)
    cilindri: Optional[str] = ""
    cilindrata_cc: Optional[float] = 0
    alimentazione: Optional[str] = ""
    peso_kg: Optional[float] = 0
    avviamento: Optional[str] = ""
    gambo: Optional[str] = ""
    trim: Optional[str] = ""
    comandi: Optional[str] = ""
    alternatore_A: Optional[float] = 0
    carburante: Optional[str] = ""
    # prezzi
    prezzo_listino: float = 0
    prezzo_acquisto_concessionario: Optional[float] = 0   # € IVA esclusa, costo di acquisto dal concessionario (snapshot)
    sconto_perc_1: float = 0
    sconto_perc_2: float = 0
    montaggio: Optional[float] = 0
    cavetteria: Optional[float] = 0
    note: Optional[str] = ""
    stato: Optional[str] = "bozza"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SuzukiPreventivoCreate(BaseModel):
    numero: Optional[str] = ""
    data: Optional[str] = None
    cliente_nome: str
    cliente_telefono: Optional[str] = ""
    cliente_email: Optional[str] = ""
    modello_id: Optional[str] = ""
    codice: Optional[str] = ""
    modello: str
    potenza_hp: Optional[float] = 0
    specifiche: Optional[str] = ""
    cilindri: Optional[str] = ""
    cilindrata_cc: Optional[float] = 0
    alimentazione: Optional[str] = ""
    peso_kg: Optional[float] = 0
    avviamento: Optional[str] = ""
    gambo: Optional[str] = ""
    trim: Optional[str] = ""
    comandi: Optional[str] = ""
    alternatore_A: Optional[float] = 0
    carburante: Optional[str] = ""
    prezzo_listino: float
    prezzo_acquisto_concessionario: Optional[float] = 0
    sconto_perc_1: Optional[float] = 0
    sconto_perc_2: Optional[float] = 0
    montaggio: Optional[float] = 0
    cavetteria: Optional[float] = 0
    note: Optional[str] = ""
    stato: Optional[str] = "bozza"


class SuzukiImportRequest(BaseModel):
    """Payload per l'import via AI: PDF o immagine in base64.
    Il backend usa Gemini Vision per estrarre la lista dei modelli."""
    file_base64: str                              # dati base64 (data URL o raw)
    file_name: Optional[str] = ""


class SuzukiBulkCreate(BaseModel):
    modelli: List[SuzukiModelloCreate]


class SuzukiLegendaVoce(BaseModel):
    """Voce della legenda delle sigle motori Suzuki (editabile dall'utente)."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sigla: str
    significato: str
    gruppo: Optional[str] = ""
    ordine: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SuzukiLegendaVoceCreate(BaseModel):
    sigla: str
    significato: str
    gruppo: Optional[str] = ""
    ordine: Optional[int] = 0


class SuzukiLegendaVoceUpdate(BaseModel):
    sigla: Optional[str] = None
    significato: Optional[str] = None
    gruppo: Optional[str] = None
    ordine: Optional[int] = None



# ---------------------------------------------------------------------------
# GOMMONI GEB (marchio proprio)
# ---------------------------------------------------------------------------
class GommoneModello(BaseModel):
    """Gommone a marchio GEB con caratteristiche tecniche e prezzo pubblico."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    modello: str
    lunghezza_m: Optional[float] = 0
    larghezza_m: Optional[float] = 0
    diametro_tubolare_cm: Optional[float] = 0
    compartimenti: Optional[int] = 0
    portata_persone: Optional[int] = 0
    potenza_max_hp: Optional[float] = 0
    peso_kg: Optional[float] = 0
    carena: Optional[str] = ""
    tessuto: Optional[str] = ""
    lunghezza_interna_cm: Optional[float] = 0
    categoria_ce: Optional[str] = ""
    potenza_min_hp: Optional[float] = 0
    specchio: Optional[str] = ""
    accessori_serie: List[str] = []                # dotazioni di serie (lista propria, separata dagli optional)
    dotazioni: Optional[str] = ""
    note: Optional[str] = ""
    prezzo_pubblico: float = 0                    # € IVA inclusa
    ordine: Optional[int] = 0
    omologazione_file_id: Optional[str] = ""      # GridFS id del PDF di omologazione
    omologazione_nome: Optional[str] = ""
    presentazione_file_id: Optional[str] = ""     # GridFS id del PDF di presentazione
    presentazione_nome: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GommoneModelloCreate(BaseModel):
    modello: str
    lunghezza_m: Optional[float] = 0
    larghezza_m: Optional[float] = 0
    diametro_tubolare_cm: Optional[float] = 0
    compartimenti: Optional[int] = 0
    portata_persone: Optional[int] = 0
    potenza_max_hp: Optional[float] = 0
    peso_kg: Optional[float] = 0
    carena: Optional[str] = ""
    tessuto: Optional[str] = ""
    lunghezza_interna_cm: Optional[float] = 0
    categoria_ce: Optional[str] = ""
    potenza_min_hp: Optional[float] = 0
    specchio: Optional[str] = ""
    accessori_serie: List[str] = []                # dotazioni di serie (lista propria, separata dagli optional)
    dotazioni: Optional[str] = ""
    note: Optional[str] = ""
    prezzo_pubblico: Optional[float] = 0
    ordine: Optional[int] = 0


class GommoneBulkCreate(BaseModel):
    modelli: List[GommoneModelloCreate]


class GommoneAccessorio(BaseModel):
    """Accessorio optional per gommoni GEB. Prezzi IVA ESCLUSA (listino GEB), per taglia (es. "620": 1000)."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    descrizione: Optional[str] = ""
    categoria: Optional[str] = ""
    serie: Optional[str] = ""                     # Job / Sirio / Tsunami / "" (tutte)
    specifiche: Optional[str] = ""                # es. MONTATO
    prezzo: float = 0                             # prezzo base IVA esclusa (se non specificato per taglia)
    prezzi_per_modello: Dict[str, float] = {}     # taglia -> prezzo IVA esclusa
    di_serie: List[str] = []                      # taglie in cui l'accessorio è incluso di serie
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GommoneAccessorioCreate(BaseModel):
    nome: str
    descrizione: Optional[str] = ""
    categoria: Optional[str] = ""
    serie: Optional[str] = ""
    specifiche: Optional[str] = ""
    prezzo: Optional[float] = 0
    prezzi_per_modello: Dict[str, float] = {}
    di_serie: List[str] = []


class GommoneSconti(BaseModel):
    """Percentuali di sconto per tipologia cliente (listino cantiere)."""
    privati: float = 0
    lavoro: float = 10
    concessionari: float = 20


class GommonePreventivoAccessorio(BaseModel):
    accessorio_id: Optional[str] = ""
    nome: str
    prezzo: float = 0
    quantita: int = 1


class GommonePreventivo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero: Optional[str] = ""
    data: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    cliente_nome: str = ""
    cliente_telefono: Optional[str] = ""
    cliente_email: Optional[str] = ""
    tipo_cliente: Optional[str] = "privati"       # privati / lavoro / concessionari
    # snapshot gommone
    gommone_id: Optional[str] = ""
    modello: str = ""
    lunghezza_m: Optional[float] = 0
    larghezza_m: Optional[float] = 0
    diametro_tubolare_cm: Optional[float] = 0
    compartimenti: Optional[int] = 0
    portata_persone: Optional[int] = 0
    potenza_max_hp: Optional[float] = 0
    peso_kg: Optional[float] = 0
    carena: Optional[str] = ""
    tessuto: Optional[str] = ""
    lunghezza_interna_cm: Optional[float] = 0
    categoria_ce: Optional[str] = ""
    potenza_min_hp: Optional[float] = 0
    specchio: Optional[str] = ""
    accessori_serie: List[str] = []
    dotazioni: Optional[str] = ""
    prezzo_gommone: float = 0                     # € IVA incl. pubblico
    sconto_perc: float = 0
    accessori: List[GommonePreventivoAccessorio] = []
    # motore opzionale
    motore_modello: Optional[str] = ""
    motore_prezzo: Optional[float] = 0
    motore_sconto_perc: Optional[float] = 0
    montaggio: Optional[float] = 0
    cavetteria: Optional[float] = 0
    batteria: Optional[float] = 0
    note: Optional[str] = ""
    stato: Optional[str] = "bozza"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GommonePreventivoCreate(BaseModel):
    numero: Optional[str] = ""
    data: Optional[str] = None
    cliente_nome: str
    cliente_telefono: Optional[str] = ""
    cliente_email: Optional[str] = ""
    tipo_cliente: Optional[str] = "privati"
    gommone_id: Optional[str] = ""
    modello: str
    lunghezza_m: Optional[float] = 0
    larghezza_m: Optional[float] = 0
    diametro_tubolare_cm: Optional[float] = 0
    compartimenti: Optional[int] = 0
    portata_persone: Optional[int] = 0
    potenza_max_hp: Optional[float] = 0
    peso_kg: Optional[float] = 0
    carena: Optional[str] = ""
    tessuto: Optional[str] = ""
    lunghezza_interna_cm: Optional[float] = 0
    categoria_ce: Optional[str] = ""
    potenza_min_hp: Optional[float] = 0
    specchio: Optional[str] = ""
    accessori_serie: List[str] = []
    dotazioni: Optional[str] = ""
    prezzo_gommone: float = 0
    sconto_perc: Optional[float] = 0
    accessori: List[GommonePreventivoAccessorio] = []
    motore_modello: Optional[str] = ""
    motore_prezzo: Optional[float] = 0
    motore_sconto_perc: Optional[float] = 0
    montaggio: Optional[float] = 0
    cavetteria: Optional[float] = 0
    batteria: Optional[float] = 0
    note: Optional[str] = ""
    stato: Optional[str] = "bozza"


# ---------------------------------------------------------------------------
# DDT & FOGLIO DI DESTINAZIONE
# ---------------------------------------------------------------------------
class DdtIndirizzo(BaseModel):
    """Indirizzo in rubrica, richiamabile per cessionario / destinazione."""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    indirizzo: Optional[str] = ""
    cap: Optional[str] = ""
    citta: Optional[str] = ""
    provincia: Optional[str] = ""
    telefono: Optional[str] = ""
    codice_cliente: Optional[str] = ""
    note: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DdtIndirizzoCreate(BaseModel):
    nome: str
    indirizzo: Optional[str] = ""
    cap: Optional[str] = ""
    citta: Optional[str] = ""
    provincia: Optional[str] = ""
    telefono: Optional[str] = ""
    codice_cliente: Optional[str] = ""
    note: Optional[str] = ""


class DdtRiga(BaseModel):
    quantita: float = 1
    descrizione: str = ""
    prezzo_unitario: float = 0


class DdtDestinatario(BaseModel):
    nome: str = ""
    indirizzo: str = ""
    cap: str = ""
    citta: str = ""
    provincia: str = ""
    telefono: str = ""


class Ddt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero: int = 0
    anno: int = Field(default_factory=lambda: datetime.now().year)
    data: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    codice_cliente: Optional[str] = ""
    rif_ordine: Optional[str] = ""
    condizioni_pagamento: Optional[str] = ""
    cessionario: DdtDestinatario = DdtDestinatario()
    destinazione_idem: bool = True
    destinazione: DdtDestinatario = DdtDestinatario()
    righe: List[DdtRiga] = []
    causale: Optional[str] = "RIPARAZIONE"
    porto: Optional[str] = "franco"
    colli: Optional[int] = 1
    peso: Optional[str] = ""
    data_ora_trasporto: Optional[str] = ""
    vettore: Optional[str] = ""
    aspetto_beni: Optional[str] = "a vista"
    note: Optional[str] = ""
    note_destinazione: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DdtCreate(BaseModel):
    numero: Optional[int] = None
    anno: Optional[int] = None
    data: Optional[str] = None
    codice_cliente: Optional[str] = ""
    rif_ordine: Optional[str] = ""
    condizioni_pagamento: Optional[str] = ""
    cessionario: DdtDestinatario = DdtDestinatario()
    destinazione_idem: bool = True
    destinazione: DdtDestinatario = DdtDestinatario()
    righe: List[DdtRiga] = []
    causale: Optional[str] = "RIPARAZIONE"
    porto: Optional[str] = "franco"
    colli: Optional[int] = 1
    peso: Optional[str] = ""
    data_ora_trasporto: Optional[str] = ""
    vettore: Optional[str] = ""
    aspetto_beni: Optional[str] = "a vista"
    note: Optional[str] = ""
    note_destinazione: Optional[str] = ""
