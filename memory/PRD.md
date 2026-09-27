# PRD — Portomare: Gestione Cantiere Nautico

## Changelog
- **2026-06** — **Magazzino: carico rapido**: accanto alla freccia rossa ↓ (scarico) aggiunta freccia verde ↑ (`btn-carico-{id}`, movimento `tipo:"carico"`, motivo "Carico rapido"); colonna rinominata "Carica / Scarica"; `doMovimento(art, tipo)` unifica la logica.
- **2026-06** — **Lista di scelta accessori di serie**: `GET/PUT /api/gommoni/dotazioni-serie` (`gommoni_settings{id:"dotazioni_serie"}.voci`, ordinata, dedup). Nel dialog gommone: select "Scegli dalla lista…" + campo nuova voce (che si aggiunge anche alla lista) + "Gestisci lista di scelta" per eliminare voci solo dalla lista (non dai modelli). Precaricate 13 voci tipiche.
- **2026-06** — **Accessori di serie = lista propria per modello**: `GommoneModello.accessori_serie: List[str]` (testo libero, aggiungi/rimuovi a chip, suggerimenti da altri modelli via datalist), del tutto separata dagli accessori optional; rimosso `accessori_serie_ids` (dati migrati). Preventivo copia i nomi; PDF scheda e preventivo li stampano.
- **2026-06** — **Accessori di serie per modello**: `GommoneModello.accessori_serie_ids` (checklist nel dialog modello, filtrata per serie con prezzo per taglia); snapshot `GommonePreventivo.accessori_serie` (nomi) compilato alla scelta del gommone, mostrato nel form (riquadro verde), escluso dal menu optional, stampato nel PDF preventivo e nella scheda caratteristiche.
- **2026-06** — **Preventivo gommone – voci motore**: aggiunti campi `cavetteria` e `batteria` (oltre a `montaggio`) su `GommonePreventivo(Create)`; form con 3 voci separate "Montaggio e collaudo", "Cavetterie e comandi", "Batteria"; riepilogo UI, PDF (sezione MOTORIZZAZIONE con "Totale motorizzazione") e totale lista includono le nuove voci.
- **2026-06** — **Scheda tecnica singolo gommone**: `GET /api/gommoni/caratteristiche.pdf?modello_id=` genera il PDF del solo modello (titolo "GOMMONE GEB — <modello> · Scheda tecnica"); icona PDF per riga nel catalogo (`btn-scheda-gommone-{id}`).
- **2026-06** — **PDF accessori per serie**: `GET /api/gommoni/accessori.pdf?serie=Job|Sirio|Tsunami&iva=escl|incl` (layout come i listini GEB originali, nota IVA e piè di pagina). Tab Accessori: selettore IVA + pulsanti PDF Job/Sirio/Tsunami. Tabella accessori estratta in `_accessori_tables()` condivisa col listino pubblico.
- **2026-06** — **Fix tasto Elimina**: `window.confirm` è bloccato nella preview in iframe (ritorna false). Creato `components/ConfirmDialog.jsx` (`confirmDialog()` promise + `ConfirmHost` montato in App.js) e sostituite tutte le 15 chiamate `window.confirm` (gommoni, DDT, Suzuki, magazzino, lavori) con `await confirmDialog(...)`.
- **2026-06** — **Accessori GEB per taglia + PDF presentazione**: `GommoneAccessorio` ora ha `serie`, `specifiche`, `prezzi_per_modello` (taglia→prezzo IVA ESCLUSA), `di_serie`; seed `scripts/seed_accessori_geb.py` (45 accessori Sirio/Tsunami). Tab Accessori raggruppato per serie con colonne taglia e IVA incl. tra parentesi; preventivo filtra per serie/taglia del gommone e inserisce prezzo IVA inclusa (o "di serie" a 0); listino PDF accessori per serie/taglia. Documenti per modello generici: `POST/GET(.pdf)/DELETE /api/gommoni/modelli/{id}/doc/{omologazione|presentazione}` (`DocumentoButton.jsx`). Prezzi pubblici importati dall'utente uniti nei modelli seed (610→620).
- **2026-06** — **Catalogo Gommoni GEB reale**: importati i 14 modelli da "CARATTERISTICHE GOMMONI G.E.B." (`backend/scripts/seed_gommoni_geb.py`, upsert per modello). Nuovi campi `lunghezza_interna_cm`, `categoria_ce`, `potenza_min_hp`, `specchio` su modelli/preventivi, form, PDF caratteristiche (griglia 3×4) e PDF preventivo, prompt AI.
- **2026-06** — **Promemoria backup**: `GET /api/backup` registra `ultimo_backup` in `app_settings{id:"backup_info"}`; `GET /api/backup/ultimo` ritorna data, giorni trascorsi e `scaduto` (≥7 giorni o mai). Home mostra banner ambra con pulsante "Salva backup ora" quando scaduto, altrimenti riga verde "Ultimo backup: …".
- **2026-06** — **Backup in cartella scelta con rotazione 3 copie**: `lib/backupFolder.js` usa `showDirectoryPicker` (Chrome/Edge) per chiedere la cartella, scrive `backup_geb_completo_<ts>.json` e cancella le copie più vecchie oltre 3; fallback a `showSaveFilePicker` o download classico su browser non supportati (Firefox/Safari).
- **2026-06** — **Backup generale v3**: `GET /api/backup` esporta TUTTE le collezioni (escluse `users`/`password_reset_tokens`) + file GridFS (PDF omologazione) in un JSON con `collections`, `files`, `settori`, `counts`; `POST /api/restore` generico (sovrascrive solo le collezioni presenti, ripristina GridFS) e retro-compatibile con i vecchi backup v2 a chiavi top-level. Dialog ripristino Home mostra riepilogo per settore.
- **2026-06** — **Nuovo modulo DDT & Foglio di destinazione** (`/ddt`, `backend/routers/ddt.py`, `pages/ddt/*`): DDT editabile (numero auto N/anno, data, cessionario, destinazione idem/diversa, righe merce, causale/porto/colli/peso/vettore/aspetto, note), catalogati per anno con filtro e ricerca; PDF DDT fedele al modello ODS; Foglio di destinazione PDF (mittente GEB + destinatario grande + note aggiuntive `note_destinazione`); rubrica indirizzi (`ddt_indirizzi`) richiamabile dal DDT e salvabile al volo. Collezioni: `ddt`, `ddt_indirizzi`. Testing agent iteration_16: 12/12 backend + frontend OK.
- **2026-06** — **Inventario PDF magazzino**: la data non è più automatica; il pulsante apre un dialog "Data inventario" (default oggi, modificabile) e il PDF riporta "Inventario al gg/mm/aaaa" (`GET /api/magazzino/inventario.pdf?data=YYYY-MM-DD`, 400 se non valida).
- **2026-06** — **Gommoni: omologazione PDF + AI caratteristiche**: per ogni modello pulsante "Carica omologazione" (PDF in GridFS `gommoni_omologazioni`, endpoint `POST/GET(.pdf)/DELETE /api/gommoni/modelli/{id}/omologazione`), badge verde "Omologazione" per aprirlo, sostituire o rimuovere. Nel dialog modello pulsante "Rileva caratteristiche con AI" (`POST /api/gommoni/import-ai-scheda`) che compila i campi da scheda tecnica PDF/foto. Prompt import AI esteso (carena/CE, tessuto grammatura, dotazioni complete, note) e tabella anteprima import con tutte le colonne.
- **2026-06** — **Nuovo modulo Gommoni GEB** (`/gommoni`, `backend/routers/gommoni.py`, `pages/gommoni/*`): catalogo gommoni editabile (modello, dimensioni, Ø tubolare, compartimenti, persone, HP max, peso, carena, tessuto, dotazioni, prezzo pubblico); accessori optional CRUD; sconti globali per tipologia (privati/lavoro/concessionari) in `gommoni_settings.sconti`; PDF listino pubblico, listino cantiere per categoria (`?categoria=`), caratteristiche; import AI (Gemini) listini/schede; preventivi gommone (G2026-NNN) con accessori, motore Suzuki opzionale, montaggio, anteprima e PDF. Collezioni: `gommoni_modelli`, `gommoni_accessori`, `gommoni_settings`, `gommoni_preventivi`. Testato con testing agent (iteration_15, 29/29 backend + frontend OK).
- **2026-06** — **Specifiche motore nel preventivo Suzuki**: il seed (`suzuki_seed.derive_specs`) deriva trim / avviamento / comandi dalla sigla Suzuki (E=elettrico, R=a distanza, T/Z/P/G o ≥40HP=Power Trim & Tilt, H/barra=da barra). Catalogo ripopolato (62 modelli). Aggiunto campo "Comandi" nel form preventivo e nella scheda tecnica del PDF (griglia 3×4).
- **2026-06** — **Motori in offerta casa madre**: pulsante "Motori in offerta" in tab Modelli → `pages/suzuki/OfferteDialog.jsx` (checkbox + prezzo imposto IVA incl.). Nuovo endpoint `PUT /api/suzuki/offerte` `{offerte:{id:prezzo}}` (azzera i non selezionati). Modelli con `prezzo_offerta>0`: Sc.1/Sc.2 bloccati a 0% e badge OFFERTA nell'editor listino concessionario e nel PDF (guadagno calcolato sul prezzo imposto); listino pubblico PDF mostra vecchio prezzo barrato + prezzo imposto + "OFFERTA". Preventivi già usano `prezzo_offerta` come base.
- **2026-02-19** — **Refactor Suzuki.jsx** (1059 → 33 righe, –97%) spezzato in `pages/suzuki/` con 10 file: `common.jsx` (helpers), `LogoPdfButton.jsx`, `ModelloDialog.jsx`, `ImportAIDialog.jsx`, `ModelliTab.jsx`, `CondizioniPreventivoButton.jsx`, `PreventivoDialog.jsx`, `PreventiviTab.jsx`, `LegendaDialog.jsx`, `LegendaTab.jsx`. Tutti i data-testid preservati.
- **2026-02-19** — **Refactor ClienteForm.jsx** (1220 → 652 righe, –47%) spezzato in `pages/cliente-form/` con 4 sotto-componenti.
- **2026-02-19** — **Aliquota IVA globale** configurabile in Impostazione dati cantiere (`Cantiere.iva_percentuale`, default 22%). Usata dinamicamente da Suzuki `_calc_totale` (form live + PDF) per costo acquisto IVA incl. e allarme sotto-costo.
- **2026-02-19** — **Allarme sotto-costo Suzuki**: nuovo campo `prezzo_acquisto_concessionario` (IVA escl.) nel preventivo. Backend/frontend mostrano margine (verde/rosso) e riquadro rosso "⚠ ATTENZIONE: PREZZO SOTTO COSTO" se il netto motore è inferiore all'acquisto IVA incl.
- **2026-02-19** — **Layout PDF Suzuki riorganizzato**: sezioni "COSTO MOTORE" → barra "NETTO MOTORE SCONTATO" evidenziata → "INSTALLAZIONE E ACCESSORI" → "TOTALE PREVENTIVO".
- **2026-02-19** — **Anteprima PDF unificata** in tutta l'app (Suzuki, Tubolari, Contratti, Clienti, ClienteForm) con nuovo componente `components/PdfPreviewOverlay.jsx` basato su react-pdf. Include paginazione + zoom, no download automatico.
- **2026-02-19** — Lunghezza minima password uniformata a **5 caratteri** ovunque.
- **2026-02-16** — Preventivo Suzuki: base prezzo cambiata da "listino IVA escl." a **"pubblico IVA incl."**.
- **2026-02-16** — Refactoring **Magazzino.jsx** (2411 righe) spezzato in cartella `pages/magazzino/` con 12 file.



## Problem Statement (Original, IT)
"Una app di gestione clienti per un cantiere nautico
Nome, cognome, tipo di barca e lunghezza,
Tipo di sosta dentro/fuori,
Se fuori calcolo dei costi della copertura, alaggio e varo, note dei lavori eseguiti, costo antivegetativa, costo manutenzione motore.
Sono circa 200 posti barca"

## User Choices
- Autenticazione: **Password unica condivisa** (utente singolo, nessuna email richiesta in UI). Backend usa `ADMIN_EMAIL` internamente.
- Recupero password: **PIN di recupero master** (default `347260`, cambiabile da Impostazioni). Reset diretto senza email.
- Costi: **Tariffe base configurabili + override manuale per cliente**
- Extra: **Export Excel/CSV** + integrazioni future
- Lingua: **Italiano**
- Design: nessuna preferenza → tema Premium Maritime (Deep Ocean navy + Teak orange, Fraunces + Chivo)

## Personas
- **Titolare cantiere / segreteria**: gestisce l'anagrafica dei 200 posti barca, monitora entrate stimate e scadenze
- **Meccanico / responsabile lavori**: aggiorna note lavori eseguiti e scadenze manutenzione

## Architecture (2026-02)
Backend spezzato in moduli (`server.py` ora 112 righe, prima 2761):
- `database.py` — Mongo client, logger, TOTAL_POSTI
- `models.py` — Pydantic (Cliente, Tariffe, Lavoro, Cantiere, ecc.)
- `helpers.py` — serialize, calcola_costi, _euro
- `auth.py` — JWT + endpoints + seed_admin
- `pdf_builders.py` — PDF preventivo + storico multi-anno
- `routers/*.py` — un file per dominio: tariffe, clienti, lavori, stats, export, cantiere, backup, preventivo, report, anni


## Iter30 (2026-02-XX) — Autenticazione con recupero password
- ✅ Backend `auth.py`: JWT session estesa a **30 giorni**, endpoint `POST /forgot-password`, `POST /reset-password`, `POST /change-password`. Token di reset 32-byte urlsafe, TTL 1h, single-use, TTL index MongoDB.
- ✅ Backend `email_service.py`: integrazione Resend gestita Emergent (EMERGENT_EMAIL_KEY). Template HTML italiano per password reset.
- ✅ Backend `server.py`: `api_router` ora ha `dependencies=[Depends(get_current_user)]` — tutte le rotte `/api/*` (tranne `/api/auth/*`) richiedono cookie di sessione valido. 401 senza auth.
- ✅ Admin seed cambiato a `sanpalmie@gmail.com` / `Portomare2026!`. Email di recupero **fissa** `info@gebnautica.it` (env `OWNER_EMAIL`).
- ✅ Frontend `App.js`: nuovo `AuthProvider`, rotte pubbliche `/login`, `/forgot-password`, `/reset-password`, tutto il resto dentro `ProtectedRoute`.
- ✅ Frontend nuove pagine `ForgotPassword.jsx` e `ResetPassword.jsx`, link "Password dimenticata?" in `Login.jsx`.
- ✅ Frontend `Layout.jsx`: mostra utente loggato in sidebar + bottone **Esci**.
- ✅ Frontend `Impostazioni.jsx`: sezione "Sicurezza account" con cambio password (verifica password attuale).

## Iter41 (2026-02-14) — Applica ricarico fornitore a tutti gli articoli
- ✅ Backend `POST /api/magazzino/fornitori/{fid}/applica-ricarico`: ricalcola `prezzo_listino = prezzo_acquisto × (1 + ricarico%)` per TUTTI gli articoli del fornitore, saltando quelli senza prezzo di acquisto. Ritorna `{articoli_aggiornati, articoli_saltati, totale, ricarico_percent}`.
- ✅ Frontend `Magazzino.jsx` tab Fornitori: nuovo bottone icona **%** in ogni riga (disabled se ricarico non impostato) che apre AlertDialog di conferma prima del ricalcolo.
- ✅ Frontend `FornitoreForm`: quando si modifica il ricarico % predefinito e si salva, viene aperto automaticamente l'AlertDialog "Vuoi applicare il nuovo ricarico X% a tutti gli articoli?".
- ✅ Test manuale curl: Gibellato (6 articoli, ricarico 55%): tutti aggiornati con prezzo listino esatto (pa × 1.55, arrotondato 2 dec). Errori 404/400 gestiti.

- ✅ E2E test manuale: login → hit `/api/clienti` con cookie 200, senza cookie 401. Forgot → email 202 Accepted a info@gebnautica.it → token DB → reset → login con nuova password → change-password → login con originale ✅.

## Iter31 (2026-02-XX) — Magazzino accessori nautici + AI vision + Password toggle
- ✅ **Password toggle** su Login/Reset/Cambio password: nuovo componente `PasswordInput.jsx` con icona occhio, `type=text/password` togglabile.
- ✅ **Backend router** `routers/magazzino.py` (~450 righe) con endpoint per Fornitori, Articoli, Movimenti, scan AI e export:
  - CRUD Fornitori (`/magazzino/fornitori`): elimina distacca articoli collegati.
  - CRUD Articoli (`/magazzino/articoli`): filtri per q/fornitore/categoria/sotto_scorta, endpoint categorie distinct, count sotto scorta.
  - Movimenti (`/magazzino/movimenti`): tipi `carico`/`scarico`/`rettifica`, aggiornamento automatico giacenza, storico.
  - **AI scan** (`/magazzino/scan-articolo`, `/magazzino/scan-ddt`) via **Gemini 3 Flash** (emergentintegrations + `EMERGENT_LLM_KEY`): estrae codice/nome/descrizione/prezzo da foto singolo articolo, oppure lista articoli da foto DDT italiano.
  - **Bulk import** (`/magazzino/importa-articoli`): dopo scan DDT crea articoli nuovi o incrementa giacenza degli esistenti (match per codice), registra movimenti "Carico da DDT".
  - **Export PDF** listino (`/magazzino/listino.pdf`) filtrabile per fornitore/categoria, formato tabellare Reportlab.
  - **Export Excel** inventario (`/magazzino/inventario.xlsx`): colonne complete + calcolo valore giacenza + totale.
- ✅ **Modelli**: `Fornitore`, `Articolo`, `MovimentoMagazzino` + Create variants + `ScanArticoloRequest/ScanDDTRequest`.
- ✅ **Frontend page** `Magazzino.jsx` con 3 tab (Articoli / Fornitori / Movimenti):
  - Tab Articoli: KPI (totali, sotto scorta, categorie, valore), search + filtri fornitore/categoria/sotto-scorta, riga rossa se sotto scorta, immagine miniatura, edit/delete, 3 modalità inserimento (manuale / Scan foto AI / Scan DDT AI), export PDF listino filtrato + Excel inventario.
  - Tab Fornitori: CRUD completo.
  - Tab Movimenti: carico/scarico/rettifica con dialog dedicato, tabella storico con badge tipo.
- ✅ **Nav**: nuova voce "Magazzino" (icona Package) nel sidebar tra Posti Barca e Report.
- ✅ **Indici MongoDB**: `articoli.codice`, `articoli.nome`, `movimenti_magazzino.articolo_id`, `movimenti_magazzino.created_at`.
- ✅ E2E test manuale: CRUD fornitore/articolo (200), PUT articolo (200), movimenti carico→15 rettifica→8, listino PDF 200 2.3KB, inventario XLSX 200 5.5KB, AI vision Gemini scan-articolo su immagine dummy HTTP 200 con JSON valido.



## Iter32 (2026-02-XX) — Magazzino ↔ Clienti + Ordine Fornitore PDF + upload DDT
- ✅ **Backend `models.py`**: `Lavoro` esteso con `articoli_magazzino: List[dict]`; `MovimentoMagazzino` esteso con `cliente_id`, `cliente_nome`, `lavoro_id`; `ScanDDTRequest` accetta anche `file_base64` + `mime_type` (per PDF).
- ✅ **Backend `routers/lavori.py`**: nuovo helper `_scarica_articoli_magazzino` che, alla creazione di un lavoro, valida stock, decrementa la giacenza di ogni articolo indicato e genera un movimento **scarico** collegato a cliente+lavoro. Il costo del lavoro è auto-incrementato del valore degli articoli (Σ qt × prezzo_unitario). In PUT gli articoli sono ignorati per evitare doppi scarichi.
- ✅ **Backend `routers/magazzino.py`**: nuovo endpoint `GET /magazzino/ordine-fornitore.pdf?fornitore_id=` che genera un PDF ordine per il fornitore (o globale) con TUTTI gli articoli sotto scorta, intestazione cantiere, tabella evidenziata, colonna "Q.tà da ordinare" suggerita. Endpoint `POST /magazzino/scan-ddt` ora accetta anche PDF (converte prima pagina a PNG via PyMuPDF a 200 DPI).
- ✅ **Frontend `LavoriSection.jsx`**: nel dialog "Nuovo lavoro" nuova sezione "Articoli dal magazzino" con select per aggiungere articolo, quantità/prezzo editabili, alert giacenza insufficiente, totale live "manodopera + articoli". Le righe lavoro mostrano ora i badge degli articoli usati.
- ✅ **Frontend `Magazzino.jsx`**: nuovo bottone globale **"Ordine PDF"** (icona ShoppingCart) accanto a Listino/Inventario. Nella tab Fornitori ogni riga ha una icona ShoppingCart che scarica l'ordine PDF filtrato per quel fornitore. Nel tab Movimenti la colonna motivo mostra ora `Cliente: Cognome Nome` in blu se il movimento è collegato a un cliente/lavoro. Il dialog Scan DDT ora accetta **JPG/PNG/PDF** (max 8MB) con card dedicata per PDF.
- ✅ E2E test: POST lavoro con 2 articoli (FLT × 2 + AN × 1) → costo 211€, giacenze 10→8 e 2→1 ✅, movimenti con `cliente_nome="Rossi Mario"` e `lavoro_id` ✅. Ordine PDF `fornitore_id=X` HTTP 200 ✅. Scan DDT PDF → prima pagina convertita e AI legge fornitore/righe.

## Preventivo + Contratto in un unico PDF (2026-02)
- Nuovo endpoint `GET /api/clienti/{id}/preventivo-contratto.pdf` che genera preventivo, poi contratto (usando `cantiere.contratto_template`) e li unisce con `pymupdf.insert_pdf`

## Iter33 (2026-02-XX) — Ripristino giacenza automatico su DELETE lavoro
- ✅ **Backend `routers/lavori.py`**: `DELETE /lavori/{id}` ora legge `articoli_magazzino` del lavoro, ripristina la giacenza di ogni articolo (idempotente rispetto ad articoli eliminati dal magazzino) e genera per ciascuno un movimento **carico** con motivo `"Storno lavoro eliminato · Cliente X"`, mantenendo il collegamento `cliente_id`/`lavoro_id`. Risposta: `{ok, giacenze_ripristinate, articoli_saltati}`.
- ✅ **Frontend `LavoriSection.jsx`**: la conferma di eliminazione ora avvisa esplicitamente ("Verranno ripristinate le giacenze di N articoli"). Toast di successo mostra il numero di giacenze ripristinate.
- ✅ E2E: creato lavoro con 3pz su articolo giacenza 20 → 17. DELETE → 20 ✓. Movimenti: scarico -3 + carico +3 di storno ✓. Edge case articolo eliminato dal magazzino → `articoli_saltati:1`, nessun errore ✓.

- Refactor: builder contratto estratto in `build_contratto_pdf_bytes(cliente, cantiere, testo, titolo)` in `routers/contratti.py`, riusato dal nuovo endpoint

## Iter34 (2026-02-XX) — Hotfix pagina bloccata
- 🐛 **Fix `TypeError: nav.map is not a function`** in `Layout.jsx`: la costante `nav` (array del menu) veniva sovrascritta dalla local `const nav = useNavigate()` introdotta con la feature Logout. Ora `useNavigate()` è assegnato a `navigate` per evitare shadow.
- ✅ **`lib/api.js`**: aggiunto timeout 30s e interceptor axios su risposta 401 che reindirizza automaticamente a `/login?redirect=<path>` — evita spinner infiniti quando la sessione scade a metà navigazione.
- ✅ **`Clienti.jsx`**: `.then` sostituito con `try/catch` + `.finally` per rimuovere lo spinner e mostrare un toast in caso di errore di rete.
- ✅ **`server.py` CORS**: `allow_origins` esplicito su `FRONTEND_URL` (anziché `*`) per essere compatibile con `allow_credentials=True` nei browser moderni.


## Iter35 (2026-02-XX) — Articoli magazzino in Lavorazioni extra del preventivo cliente
- ✅ **`ClienteForm.jsx`**: nella sezione "Lavorazioni extra" affianco al bottone "Aggiungi voce" ora c'è un select "+ Da magazzino" (icona Package) che elenca tutti gli articoli. Selezionando un articolo viene aggiunta automaticamente una lavorazione_extra con descrizione `[CODICE] Nome` e prezzo = `prezzo_listino`. Gli articoli sono caricati all'apertura del form.
- ℹ️ **Nota di design**: in fase di preventivo/inserimento cliente lo stock NON viene decrementato (nessun lavoro effettivo eseguito). Il decremento continua ad avvenire solo quando si crea un `Lavoro` reale dalla sezione "Storico lavori" del cliente.

- Nuovo bottone icona (FileSignature) sulla riga cliente in `Clienti.jsx` accanto al PDF preventivo
- Verificato: 3 pagine totali con "PREVENTIVO", "CONTRATTO" e "CLAUSOLE VESSATORIE" presenti nel PDF unificato

## Iter36 (2026-02-XX) — Quantità articolo su preventivo cliente
- ✅ **`ClienteForm.jsx`**: bottone "Da magazzino" ora apre un **Dialog** (invece di select singolo) con:
  - selettore articolo (mostra codice + prezzo unitario + U.M.)
  - input **quantità** (default 1, step 0.01, auto-focus)
  - anteprima live: `[COD] Nome × Q  ·  Q × prezzo = TOTALE`
  - indicatore giacenza corrente accanto al campo quantità
- ✅ La lavorazione_extra viene aggiunta come `descrizione = "[COD] Nome × Q pz"` con `prezzo = Q × prezzo_listino` calcolato lato client. Il totale del preventivo si aggiorna automaticamente.



## Iter37 (2026-02-XX) — Ricerca live articolo magazzino nel dialog preventivo
- ✅ **`ClienteForm.jsx`** — Dialog "Da magazzino" rifatto con combobox custom:
  - Input di ricerca con auto-focus che filtra in tempo reale su **codice + nome + descrizione + categoria** (case-insensitive)
  - Lista scrollabile (max 56 righe visibili) con icona, codice, nome, descrizione, prezzo/UM, giacenza, categoria
  - Selezionato l'articolo, viene mostrata una card di conferma con bottone "X" per cambiare selezione
  - Fallback: lista vuota → messaggio "Nessun risultato per '...'", magazzino vuoto → messaggio dedicato
  - Se articoli > 30 senza query, mostra hint "Digita per cercare tra N articoli…"
- ✅ Build frontend pulita (nessun warning nuovo).

## MQ nel PDF + Larghezza personalizzata (2026-02)

## Iter38 (2026-02-XX) — Magazzino orientato al Listino prezzi (non tracking giacenza)
- ✅ **`Magazzino.jsx` — nuova impostazione**: la sezione è pensata come **listino aggiornabile a ogni acquisto**, non come tracking di giacenza in tempo reale.
- ✅ **KPI ripensati**: `Articoli in listino` · `Categorie` · `Fornitori attivi` · **`Ricarico medio %`** (calcolato automaticamente su `(prezzo_vendita - prezzo_acquisto) / prezzo_acquisto`). Rimosse le card "Sotto scorta" e "Valore giacenza".
- ✅ **Tabella articoli** ricentrata su listino: colonne **Codice · Articolo · Categoria · Fornitore · Prezzo acquisto · Prezzo vendita · Ricarico % · Azioni**. Rimosse le colonne Q.tà e Scorta min. dalla vista principale. Ricarico visualizzato in verde primary se ≥ 20%, rosso se negativo.
- ✅ **Filtro "Solo sotto scorta"** rimosso dai filtri principali (contraddiceva l'orientamento listino).
- ✅ **Form articolo** riordinato: Codice + Fornitore in prima riga, Nome/Descrizione centrali, Categoria + UM, poi **Prezzo acquisto + Prezzo vendita** con card di anteprima ricarico calcolato + margine assoluto (€). Foto e Note come prima. Rinominato "Prezzo listino" → **"Prezzo vendita"** (più chiaro).
- ✅ **Sezione "Inventario (opzionale)"** collassabile in fondo al form, mostra Quantità + Scorta minima solo quando serve fare inventario. Badge con q.tà corrente quando la sezione è chiusa se giacenza > 0.
- ✅ Build frontend pulita.
- ℹ️ Il tab "Movimenti" resta disponibile per chi vuole tenere lo storico dei carichi/scarichi manuali. Il collegamento con i Lavori del cliente (scarico automatico + ripristino su DELETE) continua a funzionare per chi lo usa.

- Nuovo campo Cliente `larghezza_personalizzata` (opzionale): se impostato sovrascrive la larghezza automatica a scaglioni
- Helper `larghezza_barca(lunghezza, larghezza_personalizzata)` gestisce l'override
- Nel PDF preventivo la sezione Imbarcazione mostra ora "L. 8 m × 3 m (24 mq)" così il cliente vede la superficie applicata
- Nel form cliente, sotto la lunghezza, l'hint mostra in tempo reale la larghezza (con indicazione "personalizzata" se override attivo) e i mq

## Iter39 (2026-02-XX) — Bottone "Gestione magazzino" in Home
- ✅ **`Home.jsx`**: aggiunto nell'hero, subito dopo "Gestione clienti", un bottone **"Gestione magazzino"** (icona Package, `data-testid="cta-magazzino"`) che porta a `/magazzino`. Stesso stile outline dell'altro CTA per coerenza visiva.

## Iter40 (2026-02-XX) — Ricarico % editabile nel form articolo
- ✅ **`Magazzino.jsx` — ArticoloForm**: nuovo campo **Ricarico % (modificabile)** subito dopo i due prezzi. Comportamento bidirezionale:
  - Se il prezzo di acquisto è impostato e l'utente scrive un ricarico → il **prezzo di vendita** si ricalcola automaticamente (`acquisto × (1 + ricarico/100)`).
  - Se il prezzo di vendita viene modificato manualmente → il ricarico si aggiorna a sua volta nel campo (perché il valore mostrato è derivato).
  - Se non c'è ancora il prezzo di acquisto, il valore inserito viene memorizzato come "ricarico atteso" con un toast informativo che invita a inserire prima il costo.
- ✅ La card riassuntiva "Ricarico calcolato · margine €" resta visibile quando entrambi i prezzi sono presenti.


- Nuovo input "Larghezza personalizzata (m)" accanto alla lunghezza (lasciare vuoto per auto)
- Sosta (dentro/fuori/temporanea), Copertura e Antivegetativa ora calcolati sulla **superficie occupata** in mq = lunghezza × larghezza a scaglioni
- Larghezza automatica: **≤ 6,50 m → 2,5 m · ≤ 9 m → 3 m · > 9 m → 4 m** (helper `larghezza_barca` in `helpers.py`)
- Tariffe rinominate a €/mq (chiavi campo invariate per compatibilità DB, solo etichette e listino PDF aggiornati)

## Iter41 (2026-02-XX) — Aggiorna prezzi da DDT + Ricarichi default per categoria
- ✅ **Modello `RicaricoCategoria`**: nuova collezione `ricarichi_categoria` `{id, categoria, ricarico_percent, created_at}`.
- ✅ **Backend `magazzino.py`** nuovi endpoint:
  - `GET /magazzino/ricarichi-categoria` · `POST /magazzino/ricarichi-categoria` (upsert su categoria unica) · `DELETE /magazzino/ricarichi-categoria/{id}`
- ✅ **`POST /magazzino/importa-articoli`** ora accetta `aggiorna_prezzi` e `mantieni_ricarico`:
  - **Articolo esistente**: se aggiorna_prezzi=True aggiorna `prezzo_acquisto` col nuovo prezzo DDT; se mantieni_ricarico=True, ricalcola `prezzo_listino` conservando la percentuale di ricarico corrente (`(old_pv - old_pa) / old_pa`). Se il ricarico corrente non è calcolabile prova con il default della categoria.
  - **Articolo nuovo**: se esiste un ricarico default per la sua categoria, calcola `prezzo_listino = prezzo_acquisto × (1 + ricarico/100)`. Altrimenti `prezzo_listino = prezzo_acquisto`.
  - Risposta arricchita con `prezzi_aggiornati` (contatore).
- ✅ **`Magazzino.jsx`**: nuovo bottone **"Ricarichi categoria"** (icona Percent) nella toolbar Articoli. Dialog dedicato con lista + inline edit + delete + aggiunta rapida (dropdown categorie esistenti oppure input libero).
- ✅ **Dialog Scan DDT**: nuovo box "Gestione prezzi articoli esistenti" con 2 checkbox (`Aggiorna prezzo di acquisto` + `Mantieni il ricarico corrente`) attive di default, che passano i flag alla chiamata di import. Toast finale include `N prezzi aggiornati`.

## Iter42 (2026-02-XX) — Conferma eliminazione anche sui Ricarichi
- ✅ **`Magazzino.jsx` — RicarichiCategoriaDialog**: la rimozione di un ricarico predefinito adesso passa da un AlertDialog con conferma (prima era diretta). Testo del prompt personalizzato: "Vuoi rimuovere il ricarico predefinito per **[categoria]** (+X%)? I nuovi articoli di questa categoria non useranno più un ricarico automatico."
- ✅ Le altre eliminazioni del Magazzino avevano già la conferma: Articoli (con avviso movimenti collegati) e Fornitori (con avviso che gli articoli restano senza fornitore).


## Iter43 (2026-02-XX) — DDT: riconoscimento sconto e IVA 22%, editabile
- ✅ **Backend `scan-ddt`** — Prompt Gemini riscritto per spiegare esplicitamente le colonne DDT:
  - `prezzo_listino_ivato` = prezzo unitario IVA compresa (22%)
  - `sconto_percent` = percentuale sconto
  - `importo_netto` = prezzo unitario NETTO scontato IVA esclusa (= vero prezzo di acquisto)
  - `iva_percent` intestazione DDT (default 22)
- ✅ **Backend fallback matematico**: se l'AI legge solo 2 dei 3 valori (listino/sconto/netto), il backend calcola il mancante (`netto = listino/1.22 × (1-sconto/100)`, `sconto = (1 - netto / (listino/1.22)) × 100`).
- ✅ Retrocompatibilità: `prezzo_unitario` (usato dall'endpoint `importa-articoli`) è alias del `importo_netto` così l'articolo viene salvato con il prezzo di acquisto corretto.
- ✅ **Frontend ScanDDTDialog** — Tabella preview con 3 nuove colonne editabili:
  - **Listino IVA €** · **Sconto %** · **Netto acquisto €** (evidenziato in primary come valore chiave)
  - Ricalcolo bidirezionale live: modifichi Listino/Sconto → si aggiorna il Netto; modifichi il Netto → si aggiorna lo Sconto.
  - Nota in fondo tabella: "IVA assunta al 22%. Modifica anche solo lo sconto se non è stato riconosciuto".
- ✅ Build frontend pulita.

- ✅ E2E test: setup 2 ricarichi (Ferramenta +40%, Vernici +25%), articolo esistente `FTST-01` pa=10 pv=15 (ricarico 50%). Import DDT con `mantieni_ricarico=true` e prezzo nuovo 12 → risultato pa=12 pv=18 ricarico=50% ✓. Nuovo articolo `NUOVO-01` categoria Ferramenta pa=0.50 → pv=0.70 (+40% da default) ✓.

- Restano al metro lineare: lavaggi stagionali, maggiorazione scafo sporco, movimentazione/taccaggio fuori sede

## Iter44 (2026-02-XX) — Ricarico % predefinito per Fornitore (prevale su quello di categoria)
- ✅ **Modello `Fornitore`**: nuovo campo opzionale `ricarico_default_percent: Optional[float] = None`. Esteso anche `FornitoreCreate`.
- ✅ **Backend `magazzino.py`**: nuovo helper `_default_markup_for_articolo(fornitore_id, categoria)` che risolve la priorità: **1) ricarico fornitore → 2) ricarico categoria → 3) nessuno**.
- ✅ **`importa-articoli`** ora usa il nuovo helper sia per articoli nuovi che per quelli aggiornati senza ricarico corrente calcolabile.
- ✅ **Frontend `FornitoriTab`**: nuova colonna **Ricarico %** in tabella fornitori (badge primary se impostato, "—" altrimenti).
- ✅ **Frontend `FornitoreForm`**: nuovo campo **"Ricarico % predefinito"** con hint "Applicato ai nuovi articoli di questo fornitore importati da DDT. Ha priorità sul ricarico di categoria." Lasciando il campo vuoto si torna al fallback categoria.
- ✅ E2E test verificato: fornitore con ricarico 45% + categoria Vernici 25%. Import nuovo articolo Vernici → prezzo vendita = 100 × (1+45/100) = 145 ✓ (ricarico fornitore ha battuto quello di categoria come atteso).

- Verificato: L=5m (mq 12,5) sosta 2250€; L=8m (mq 24) sosta 4320€; L=10m (mq 40) sosta 7200€ + copertura 1800€ (tariffe default)


## Iter45 (2026-02-XX) — Report Spese Accessorie separato dal magazzino
- ✅ **Nuovo modello `SpesaAccessoria`** `{id, tipo, descrizione, importo, data, fornitore_id, fornitore_nome, documento_ref, note, created_at}` con 7 tipi predefiniti: bancarie, trasporto, spedizione, imballo, assicurazione, carburante, altro.
- ✅ **Backend endpoints**: `GET /magazzino/spese` (filtri tipo/fornitore/anno) · `POST` · `PUT` · `DELETE` · `GET /magazzino/spese-report` (aggregato per tipo via pipeline MongoDB con totali e count).
- ✅ **Backend `scan-ddt`**: prompt Gemini esteso per distinguere **articoli fisici** vs **spese accessorie** (banking, trasporto, imballo…). Response include ora `spese_accessorie`. Import DDT salva le spese nella collezione dedicata (non nel magazzino).
- ✅ **`importa-articoli`** accetta `spese_accessorie[]`, `documento_ref`, `data_documento`. Risposta include `spese_salvate`.
- ✅ **Frontend `Magazzino.jsx`**: nuovo tab **"Spese"** con KPI totale + 3 badge per tipo top, riepilogo per tipo con barre percentuali, tabella filtrabile per tipo, add manuale + delete con AlertDialog di conferma.
- ✅ **ScanDDTDialog**: dopo la preview articoli, se sono state rilevate spese appare la sezione **"Spese accessorie rilevate"** (evidenziata primary) con select tipo + descrizione + importo editabili e checkbox selezione. Toast conclusivo mostra "N spese salvate".
- ✅ E2E: 3 spese create (bancarie 8.50, trasporto 25+32=57, imballo 15) → report aggregato: totale 80.50€, trasporto 57€ (2 voci), imballo 15€, bancarie 8.50€ ✓.

## Toggle ricambi motore ON/OFF (2026-02)
- Nuovi campi Cliente + ClienteCreate: `filtro_olio_attivo`, `anodi_interni_attivo`, `anodi_esterni_attivo`, `olio_piede_attivo`, `ingrassaggio_attivo` (default True) + varianti `_2_attivo` per il 2° motore
- `calcola_ricambi` accetta i flag e azzera le voci disattivate
- UI: 5 toggle per motore (Filtro olio · Kit anodi interni · Kit anodi esterni · Olio piede · Ingrassaggio) sotto al Girante
- Verificato: 118€ delta per filtro+anodi + 24€ per olio piede (2l × 12€/l) + 30€ per ingrassaggio, coerente con le tariffe

## Preventivo condizioni editabili + Pagina Contratti (2026-02)
- Nuovi campi in Cantiere/CantiereUpdate: `preventivo_interno_titolo/testo`, `preventivo_piazzale_titolo/testo`, `preventivo_esclusi_titolo/testo`, `preventivo_condizioni_titolo/testo`, `contratto_template` (tutti editabili in Impostazioni)
- I 4 blocchi vengono stampati automaticamente in coda al PDF preventivo (default con testo da riferimento, ricambi INCLUSI)
- Nuova pagina `/contratti` (voce sidebar dedicata): selezione cliente + titolo + textarea (pre-caricata dal template) → genera PDF con intestazione, dati cliente, clausole e spazio firma
- Nuovo router backend `routers/contratti.py` con `POST /api/contratti/pdf` (nessun salvataggio in DB, solo download PDF)
- **Contratto v2 (2026-02)**: nuovo template legale completo (11 sezioni: parti/dati, oggetto giuridico, oggetti a bordo, assicurazione, limitazione responsabilità, sicurezza, pagamento/ritenzione, contestazioni, manleva, foro, clausole vessatorie art. 1341 c.c.). Supporto `**grassetto**` e sostituzione placeholder `{{cognome}}` `{{nome}}` `{{codice_fiscale}}` `{{indirizzo}}` `{{telefono}}` `{{email}}` `{{tipo_barca}}` `{{lunghezza}}` `{{potenza_motore}}` `{{posto_barca}}` `{{data_oggi}}`

## Motorizzazione Entrobordo/Fuoribordo (2026-02)
- Nuovo campo `tipo_motore` (fuoribordo/entrobordo, default fuoribordo) su 1° e 2° motore in Cliente + ClienteCreate
- **Fuoribordo**: manodopera a 4 scaglioni HP (`motore_labor_2_15hp`, `motore_labor_fino_40hp`, `motore_labor_40_150hp`, `motore_labor_oltre_150hp`)
- **Entrobordo**: tariffa unica `motore_labor_entrobordo` (default 250 €) valida per qualsiasi HP
- Selettore Fuoribordo/Entrobordo nel form cliente e preventivo veloce (per entrambi i motori)

## Core Requirements (static)
- Anagrafica clienti (cognome, nome, tel, email) — visualizzazione sempre nell'ordine Cognome → Nome
- Dati barca (tipo, lunghezza in metri, tipo sosta dentro/fuori, posto barca 1-200)
- Calcolo automatico costi: sosta, copertura, alaggio, varo, antivegetativa, manutenzione motore
- Override manuale per ogni singolo cliente
- Note lavori eseguiti + scadenze antivegetativa e manutenzione motore
- Vista mappa 200 posti barca
- Configurazione tariffe base globali
- Export CSV/Excel

## Implemented (2026-02-18)
- ✅ Backend FastAPI con MongoDB (motor)
  - CRUD `/api/clienti`
  - `/api/tariffe` GET/PUT (con scaglioni motore HP e lunghezza)
  - `/api/calcola-costi` preview costi
  - `/api/stats` KPI dashboard + scadenze prossime 30gg
  - `/api/posti-barca` griglia 200 posti con stato
  - `/api/export/clienti.csv` e `/api/export/clienti.xlsx`
  - Validazioni: posto duplicato, range 1-200, tipo_sosta valido
- ✅ Frontend React con react-router:
  - **Dashboard** — 4 KPI cards, occupancy progress, pie chart, bar chart, scadenze
  - **Clienti** — tabella con ricerca, filtri sosta, export CSV/Excel, PDF preventivo per riga, edit/delete
  - **ClienteForm** — sheet form con auto-calcolo costi live via API, toggle override, storico lavori strutturato, download PDF
  - **Tariffe** — configurazione con scaglioni (alaggio/varo per lunghezza, manodopera motore per HP, ricambi unitari) + simulazione live
  - **Posti Barca** — griglia 200 tile con popover dettagli cliente

## Iteration 2 (2026-02-18)
- ✅ **PDF Preventivo/Fattura** — endpoint `/api/clienti/{id}/preventivo.pdf` con reportlab (tema navy/teak Portomare), include anagrafica, dettaglio costi, scadenze, storico lavori
- ✅ **Storico lavori strutturato** — nuovo model `Lavoro`, CRUD `/api/lavori`, componente `LavoriSection` con dialog crea/modifica/elimina, stati pianificato/in_corso/completato
- ✅ Bottone PDF in ogni riga della lista Clienti + nel form cliente
- ✅ Testing: 17/17 backend, 11/11 frontend passati al 100%

## Iteration 4 (2026-02-19)
- ✅ **Costo olio motore al litro**: `costo_olio_motore` diventa €/L (default 12), moltiplicato per `litri_olio_motore` del cliente
- ✅ **Litri olio motore** aggiunto nella scheda cliente (nuovo campo, default 3L)
- ✅ **Cavalli motore** (HP) evidenziato meglio in griglia 4-col: Cavalli / Litri / N° candele / N° termostati
- ✅ PDF preventivo mostra "Olio: X L" nell'intestazione e la quantità nella riga olio motore

## Iteration 5 (2026-02-19)
- ✅ **Home landing page** (`/`) con logo, nome cantiere, slogan, indirizzo completo, contatti, orari, sito web, P.IVA. Card stats "Attività in corso". CTA Dashboard / Clienti / Impostazioni.
- ✅ **Impostazioni Cantiere** (`/impostazioni`): editor completo con caricamento logo (base64, PNG/JPG/SVG max 2MB, preview live)
- ✅ **Endpoint `/api/cantiere` GET/PUT** con modello Cantiere (12 campi)
- ✅ **PDF preventivo dinamico**: header mostra logo (se caricato) + nome cantiere + riga contatti completa (indirizzo, telefono, email, P.IVA)
- ✅ **Sidebar Layout dinamica**: brand-link → Home, logo/nome caricati da /api/cantiere
- ✅ **Sosta fuori sede** (nuovo tipo_sosta): sostituisce costo sosta con `costo_movimentazione` (€/m) + `costo_taccaggio` (€/m). Nessuna copertura/alaggio/varo.
- ✅ **Lavaggi stagionali**: switch e costi separati per inizio + fine stagione
- ✅ **Maggiorazione scafo sporco**: applicata automaticamente quando antivegetativa disattivata (€/metro)
- ✅ Testing iter5: 47/47 backend, 100% frontend

## Iteration 8 (2026-02-19)
- ✅ **Multi-anno**: ogni cliente e lavoro ora ha campo `anno` (default anno solare corrente)
- ✅ **Endpoint `/api/anni`**: lista anni con conteggio clienti · POST `/api/anni/apri` per creare nuovo anno (con opzione `duplica_da` che copia clienti e ricalcola costi con tariffe correnti) · DELETE `/api/anni/{anno}` per cancellare completamente un anno
- ✅ Tutti i GET filtrabili per anno: `/clienti`, `/stats`, `/posti-barca`, `/report/incassi` accettano `?anno=X`
- ✅ **Vincolo posto barca** ora unico **per anno** (posto #42 nel 2026 e posto #42 nel 2027 sono validi)
- ✅ **YearContext + YearSelector**: dropdown in sidebar con lista anni + conteggio clienti + azioni "Apri nuovo anno" (con conferma e opzione duplica) e "Elimina anno" (con warning). Selezione salvata in localStorage
- ✅ Tutte le pagine (Clienti, Dashboard, Report, PostiBarca) ricaricano dati al cambio anno
- ✅ Testing iter8: 21/21 backend + frontend flows verificati

## Iteration 7 (2026-02-19)
- ✅ **Autenticazione rimossa** su richiesta utente
- Backend `/api/*` routes ora pubbliche (rimosso `Depends(get_current_user)` da api_router). Router `/api/auth/*` e seed admin ancora presenti nel codice ma non utilizzati.
- Frontend: rimossi `ProtectedRoute`, `AuthProvider`, redirect a `/login`, bottoni logout in Home e sidebar. Ripristinato Layout originale.
- App accessibile direttamente senza credenziali.
- ✅ **Endpoint `/api/backup` GET** — esporta clienti, lavori, tariffe, cantiere in JSON scaricabile
- ✅ **Endpoint `/api/restore` POST** — ripristina completamente da JSON, con validazione pydantic e overwrite totale
- ✅ **Export PDF bulk**: nuovo endpoint `/api/export/preventivi.zip` che genera un archivio con un PDF per ogni cliente (filename `{posto}_{cognome}_{nome}.pdf` sanitizzato)
- ✅ **Autenticazione JWT email/password**:
  - Modello `users` in Mongo con bcrypt hash, seed admin automatico da `.env` (ADMIN_EMAIL/ADMIN_PASSWORD)
  - Auth router: `/api/auth/login`, `/api/auth/register`, `/api/auth/logout`, `/api/auth/me`
  - Cookie httpOnly `access_token` + supporto Bearer token
  - Tutti gli endpoint `/api/*` protetti tramite dependency router-level
  - Frontend: `AuthProvider` + `ProtectedRoute` + pagina `/login` + logout in sidebar e in Home
  - Admin default: `admin@portomare.it` / `portomare2026` (aggiorna in Impostazioni consigliato)
- ✅ Testing iter6: 73/73 backend, 7/7 frontend flows

## Iter9 (2026-02-20) — 4 richieste utente
- ✅ **PDF Report pagamenti stampabile** — nuovo endpoint `GET /api/report/pagamenti.pdf?anno=YYYY&stato=tutti|pagati|non_pagati`. Tabella con Posto, Cliente, Barca, Totale, Stato (verde/rosso), data pagamento. Header con logo/nome cantiere, riepilogo (totali pagati/non pagati), totale finale filtrato. Ordina per cognome.
- ✅ **Filtro Report per stato pagamento** — dropdown in `/report` (data-testid `select-filtro-stato`) con opzioni Tutti/Pagati/Non pagati. Filtra la tabella client-side e passa `stato` al link PDF. Contatore clienti filtrati accanto al dropdown.
- ✅ **Ricambi motore separati 1°/2° motore**:
  - Nuovo campo `girante_2_attivo` in `Cliente`/`ClienteCreate` (Optional[bool]=None per evitare bug reset).
  - Nuovi campi `costo_manodopera_motore_2` e `costo_ricambi_motore_2_totale` esposti dal calcolo.
  - `calcola_costi` restituisce `ricambi_dettaglio` e `ricambi_2_dettaglio` distinti.
  - PDF preventivo con **due tabelle motore separate** ("1° Motore — X HP" e "2° Motore — X HP"), ognuna con proprio subtotale header.
  - Form cliente mostra **due breakdown separati** in UI + toggle "Girante 2° motore" (data-testid `switch-girante-2`).
- ✅ **Backup accessibile in Home** — nuova card in `/` con bottoni "Salva backup" (data-testid `btn-home-backup-download`) e "Recupera backup" (data-testid `btn-home-restore-open`) + dialog di conferma ripristino. Bottoni Impostazioni conservati.

## Iter9 Testing
- ✅ Backend: 8/8 pytest cases in `/app/backend/tests/test_iter9_pdf_and_secondo_motore.py` (report PDF, calcola-costi motore 2, POST/GET cliente, PUT regression pagato+girante_2_attivo preserved, preventivo PDF con motore 2)
- ✅ Frontend self-test: Home backup buttons, Report filter+PDF href params, ClienteForm secondo motore + girante-2 toggle + entrambi i breakdown (subtotali 657€ + 657€ visibili)

## Iter10 (2026-02-20) — Ordine alfabetico + Lavorazioni extra
- ✅ **Ordinamento alfabetico case-insensitive per cognome** in tutti gli endpoint che restituiscono liste clienti: `GET /api/clienti`, `report_pagamenti`, `report_pagamenti.pdf`. Ordine: cognome asc, poi nome asc, ignorando maiuscole/spazi iniziali.
- ✅ **Lavorazioni extra per cliente** (max 20):
  - Nuovo campo `lavorazioni_extra: List[dict]` su `Cliente` (default []) e `Optional[List[dict]] = None` su `ClienteCreate` (per preservare in PUT parziale).
  - Helper backend `_sanitize_lavorazioni_extra`: cap a 20 (→ 400 se superato), normalizza a `{descrizione: str, prezzo: float}`, filtra righe con desc vuota E prezzo 0.
  - Helper `_totale_extra(doc)` riutilizzato in `/api/stats`, `/api/report/incassi` (nuova categoria "lavorazioni_extra"), `/api/report/pagamenti`, `/api/report/pagamenti.pdf`, PDF preventivo.
  - PDF preventivo: nuova sezione **"LAVORAZIONI EXTRA"** con tabella descrizione + prezzo + riga totale, inclusa nel totale principale ("Lavorazioni extra" come voce aggregata).
  - Frontend `ClienteForm.jsx`: sezione dedicata con `+ Aggiungi voce` (max 20), input descrizione + prezzo, pulsante X per rimozione, subtotale extra, contatore "X / 20 voci". Toast se limite raggiunto. Sommato nel "Totale annuale stimato".
  - Frontend `Clienti.jsx`: funzione totale include lavorazioni_extra.
  - Frontend `Report.jsx`: aggiunta categoria "Lavorazioni extra" con colore dedicato (#5A7A9A).

## Iter10 Testing
- ✅ Backend: 10/10 pytest cases in `/app/backend/tests/test_iter10_alpha_and_extra.py`
- ✅ Frontend self-test: ordine alfabetico visibile (Bianchi→Catra→Figo→Rossi→Sandra→Verdi), sezione Lavorazioni extra funzionante (subtotale 730€, totale annuale 2427€), rimozione voce OK

## Iter11 (2026-02-20) — Manodopera motore a 4 fasce
- ✅ Tariffe: aggiunta nuova fascia **2-15 HP** (default 90 €) accanto alle esistenti 16-40 / 41-150 / oltre 150 HP.
  - Backend: nuovo campo `motore_labor_2_15hp` in `Tariffe`/`TariffeUpdate`, logica `calcola_motore_labor` estesa a 4 scaglioni.
  - Frontend: pagina Tariffe con nuova riga "Da 2 a 15 HP", label aggiornati "Da 16 a 40 HP" / "Da 41 a 150 HP" / "Oltre 150 HP". Simulazione preview aggiornata. Hint fasce in ClienteForm aggiornato.
  - Verificato: HP=10 → €90 · HP=30 → €180 · HP=100 → €320 · HP=300 → €550. PUT del solo `motore_labor_2_15hp` non resetta le altre tariffe.

## Iter12 (2026-02-20) — Assegnazione posto barca automatica
- ✅ Nuovo endpoint `GET /api/posti-barca/next?anno=X&escludi_cliente_id=Y` che ritorna il primo posto libero (1-200) per l'anno indicato, escludendo opzionalmente il posto occupato dallo stesso cliente (utile in modifica).
- ✅ Frontend `ClienteForm.jsx`: pulsante ⚡ (Zap icon) accanto al campo "Posto barca" con `data-testid="btn-posto-auto"`. Click → chiama endpoint, riempie il campo e mostra toast con posto assegnato + posti liberi rimasti.

## Iter13 (2026-02-20) — Antivegetativa e Scafo sporco spunte indipendenti
- ✅ Prima: `antivegetativa_attiva=false` implicava automaticamente maggiorazione scafo sporco. Ora sono 2 spunte separate e indipendenti (4 combinazioni possibili).
- ✅ Backend: nuovo campo `scafo_sporco_attivo: bool = False` su `Cliente`, `Optional[bool] = None` su `ClienteCreate`. Signatura `calcola_costi` aggiornata (17° parametro). Endpoint preview `/api/calcola-costi`, POST/PUT `/api/clienti`, duplicazione anno tutti aggiornati.
- ✅ **Migrazione automatica** all'avvio: clienti esistenti con `costo_scafo_sporco > 0` ricevono `scafo_sporco_attivo=True`, tutti gli altri `False`. Idempotente (basata su `$exists`).
- ✅ Frontend `ClienteForm.jsx`: nuovo toggle "Scafo sporco" (data-testid `switch-scafo-sporco`) accanto ad "Antivegetativa". Rimosso il warning giallo obsoleto. Aggiunto info-testo quando entrambi sono OFF. Preview costi include il nuovo parametro.
- ✅ Test 4 combinazioni backend:
  - OFF/OFF → antivegetativa=0, scafo=0
  - ON/OFF → antivegetativa=200, scafo=0
  - ON/ON → antivegetativa=200, scafo=120
  - OFF/ON → antivegetativa=0, scafo=120
- ✅ Migrazione verificata: Bianchi (scafo 90€) e Semp (scafo 75€) preservati con scafo=True; altri 8 clienti con antivegetativa attiva → scafo=False.

## Iter14 (2026-02-20) — Copertura come spunta indipendente
- ✅ Prima: `costo_copertura` era applicato automaticamente per `tipo_sosta="fuori"`. Ora è **una spunta indipendente** (`copertura_attiva`) applicabile su qualsiasi tipo di sosta.
- ✅ Backend: nuovo campo `copertura_attiva: bool = False` (`Optional[bool]=None` in Update). Signature `calcola_costi` 18° parametro. Preview/POST/PUT/duplicazione anno aggiornati.
- ✅ **Migrazione iter14 all'avvio**: clienti con `costo_copertura > 0` ricevono `copertura_attiva=True` (rtr e Verdi preservati con costo 270€ e 360€), altri `False`. Idempotente.
- ✅ Frontend `ClienteForm.jsx`: nuovo toggle "Copertura" (data-testid `switch-copertura`) accanto ad Antivegetativa e Scafo sporco.
- ✅ **Bug fix** collaterale iter13: aggiunti `f.scafo_sporco_attivo` e `f.copertura_attiva` al vettore delle deps di `useEffect` per il ricalcolo preview (mancavano — il toggle non triggerava la refetch).
- ✅ Test 4 casi backend + frontend: dentro+COP-ON=2407€ / dentro+COP-OFF=2207€ (diff 200€), aggiungendo scafo=+120€ → 2527€. API network capture conferma le call.

## Iter16 (2026-02-20) — Copertura bloccata su sosta al coperto
- ✅ Frontend `ClienteForm.jsx`: quando `tipo_sosta === "dentro"` la spunta **Copertura** è disabilitata (opacità 50%, descrizione dinamica "Non applicabile con sosta al coperto") e forzata a `false` tramite `useEffect`.
- ✅ Component `ToggleRow` esteso con prop `disabled`.
- ✅ Test frontend: default (dentro) → disabled=True. Passa a "A terra (fuori)" → abilitato, click ON → totale 3.512€. Ritorno "Al coperto" → disabled=True, totale torna a 2.392€ (copertura esclusa).

## Iter15 (2026-02-20) — Olio piede a litri (come olio motore)
- ✅ Prima `costo_olio_piede` era un costo fisso (25 €). Ora la tariffa è **per litro** e il costo è moltiplicato per la quantità.
- ✅ Backend: nuovi campi `litri_olio_piede: float = 1.0` (default 1L per compat) e `litri_olio_piede_2: float = 1.0` su `Cliente`, `Optional[float]=None` su `ClienteCreate`. Signature `calcola_ricambi` e `calcola_costi` aggiornate. Preview/POST/PUT/duplicazione anno passano i nuovi parametri.
- ✅ PDF preventivo: righe "Olio piede" ora mostrano "X L" e importo = X × tariffa.
- ✅ Frontend: nuovo campo "Litri olio piede" nel form (1° motore) e "Lt olio piede 2°" nel blocco 2° motore. Griglia motore passata da 4 a 5 colonne su desktop. Breakdown dettaglio mostra "(XL)".
- ✅ Tariffe: label aggiornata "Olio piede — Costo per litro".
- ✅ Test: 1L → olio_piede=25€, 3L → 75€ (+50€ nel totale), 0.5L → 12.5€. Toggle re-calcolo funzionante grazie a `litri_olio_piede` nelle deps `useEffect`.
## Iter40 (2026-02-20) — BUGFIX: servizi opzionali sempre visibili
- 🐛 **BUG risolto**: quando si disattivava lo switch "Motore presente" il condizionale nascondeva **tutti** i servizi opzionali (antivegetativa, scafo sporco, copertura, lavaggi, alaggio/varo), impedendo di configurare un cliente senza motore che voleva questi servizi.
- ✅ Restrutturato JSX: la griglia di ToggleRow è ora **fuori** dal condizionale `primo_motore_attivo` e sempre visibile. Solo i 5 input motore (HP/olio/olio piede/candele/termostati) + il toggle "Sostituzione girante" restano condizionati.
- ✅ Rimossi tag di chiusura orfani (`</>` e `)}` lasciati dal refactoring).
- ✅ **Testing_agent iter14: 100% PASS frontend**. Backend testato: motore OFF + antivegetativa + lavaggi + alaggio/varo × 2 → totale 1650€ (senza costi motore).

## Iter39 (2026-02-20) — Spunta 1° motore (motore presente si/no)
- ✅ Backend: nuovo campo `primo_motore_attivo: bool = True` su `Cliente` (Optional in `ClienteCreate`). Default True per non alterare i clienti esistenti.
- ✅ `calcola_costi`: quando `primo_motore_attivo=False` manodopera + ricambi del 1° motore vengono azzerati (il costo_manutenzione_motore resta somma di eventuale 2° motore).
- ✅ Endpoint `/api/calcola-costi` accetta il nuovo parametro. Test: HP=50 attivo → manodopera ~150+ricambi. HP=50 disattivo → tutto zero.
- ✅ POST/PUT clienti, preventivo_pdf_inline, duplicazione anno, ricalcola-anno passano il parametro.
- ✅ Frontend `ClienteForm.jsx`: nel blocco "1° Motore" nuovo Switch **"Motore presente"** (`switch-primo-motore`, default ON). Se OFF, i campi HP/olio/candele/termostati/girante vengono sostituiti da un box "Motore disattivato" e nessun costo motore viene calcolato.

## Iter38 (2026-02-20) — Eliminato riquadro Simulazione dalla pagina Tariffe
- ✅ Rimosso interamente il pannello sticky "Simulazione" (input lunghezza/HP/sosta/olio/candele/termostati + preview + totale).
- ✅ Rimossa la funzione helper `PreviewRow` e tutte le state variabili `simL/simHP/simSosta/simGiorni/simOlio/simCandele/simTermostati`.
- ✅ Rimossi gli import non più usati (`Select` da shadcn).
- ✅ Layout ora single-column full-width per i gruppi di tariffe (grid-cols-1 anziché lg:grid-cols-3).

## Iter37 (2026-02-20) — Simulazione completa personalizzabile
- ✅ Aggiunto **Select "Tipo di sosta"** (`select-simulazione-sosta`): Al coperto / Su piazzale / Fuori sede / Temporanea. Il costo sosta si ricalcola con la formula corretta per ciascun tipo.
- ✅ Se scelto "Temporanea" appare input **N° giorni** (`input-simulazione-giorni`).
- ✅ Nuovi input configurabili in grid a 3 colonne: **Olio (L)**, **Candele**, **Termostati** — tutti impattano il calcolo ricambi motore in tempo reale.
- ✅ Sottotitolo dinamico mostra la configurazione attuale ("Sosta su piazzale · 4L olio, 4 candele, 1 termostato").

## Iter36 (2026-02-20) — Simulazione tariffe: potenza motore personalizzata
- ✅ Aggiunto input "Potenza motore (HP)" (`input-simulazione-hp`, default 120) accanto al campo lunghezza (grid 2 colonne).
- ✅ Ricalcolo automatico della manodopera in base allo scaglione (2–15, 16–40, 41–150, oltre 150 HP).
- ✅ Sotto il titolo compare lo **scaglione manodopera** in uso ("Scaglione manodopera: 41–150 HP") così l'utente vede subito quale bracket si sta applicando.
- ✅ Titolo dinamico "Barca Nm · X HP".

## Iter35 (2026-02-20) — Home: rimosso "Attività in corso" e rinominato bottone
- ✅ Bottone hero `cta-dashboard` label da "Vai al gestionale" a **"Panoramica"**.
- ✅ Rimosso completamente il riquadro laterale "Attività in corso" (`home-stats`) con clienti gestiti / posti barca / entrate stimate.
- ✅ Card "Sede & contatti" ora a larghezza piena (grid-cols-1) invece di occupare 2/3 della riga.

## Iter34 (2026-02-20) — Simulazione tariffe con lunghezza personalizzata
- ✅ Nel riquadro "Simulazione" della pagina Tariffe, aggiunto input numerico "Lunghezza barca (metri)" (`input-simulazione-lunghezza`, default 8m).
- ✅ Al variare della lunghezza si aggiornano in tempo reale tutte le voci (sosta, copertura, alaggio/varo con etichetta ≤5m/>5m, antivegetativa) e il totale annuale (`simulazione-totale`).
- ✅ Titolo dinamico "Barca Nm · 120 HP" che riflette il valore inserito.

## Iter33 (2026-02-20) — Storico cliente multi-anno PDF
- ✅ **Backend**: nuovi endpoint `GET /api/clienti-nominativi` (lista distinct cognome+nome con anni per ognuno) e `GET /api/clienti-storico.pdf?cognome=X&nome=Y` (PDF A4 dello storico).
- ✅ **Layout PDF A4**: header cantiere con logo, intestazione "STORICO CLIENTE + nome", sezione anagrafica (contatti, imbarcazione, anni tracciati), poi per ogni anno (in ordine decrescente): barra navy "ANNO YYYY", tabella costi dettagliati (con voci Alaggio/Varo che includono destinazione e × N mov., lavorazioni extra riga per riga), riga "TOTALE ANNO", stato pagamento colorato.
- ✅ In fondo box teak "TOTALE GENERALE STORICO" con la somma di tutti gli anni.
- ✅ **Frontend Clienti.jsx**: nuovo bottone "Storico cliente" (`btn-storico-cliente`) in header. Al click apre `dialog-storico-cliente` con menu a tendina di tutti i nominativi (cognome nome · anni presenti) e bottone "Genera PDF storico" che scarica il file.
- ✅ Rinominato route da `/clienti/storico.pdf` a `/clienti-storico.pdf` per evitare route-shadowing con la route parametrica `/clienti/{cliente_id}`.
- ✅ Test API: `GET /api/clienti-nominativi` → 12 nominativi. PDF Figo Giorgio (2 anni: 2026+2027) → HTTP 200, 19KB, header PDF valido.

## Iter32 (2026-02-20) — Excel commercialista: selezione anno
- ✅ Home → Azioni rapide → "Excel per commercialista" ora apre un dialog `dialog-export-excel` invece di scaricare direttamente l'anno corrente.
- ✅ Menu a tendina (`select-anno-excel`) con 6 opzioni: anno prossimo + anno corrente (marcato "· anno in corso") + 5 anni precedenti.
- ✅ Bottone "Scarica anno YYYY" (`btn-excel-scarica`) fa il download del file `.xlsx` con i clienti dell'anno selezionato + toast di conferma.
- ✅ Nessuna modifica backend: usa l'endpoint esistente `/api/export/clienti.xlsx?anno=X`.

## Iter31 (2026-02-20) — BUGFIX: modifica tariffa sosta temporanea non salvava
- 🐛 **BUG risolto**: il campo `sosta_temporanea_giornaliera` **mancava nel modello `TariffeUpdate`** → il PUT `/api/tariffe` ignorava silenziosamente la modifica e ripristinava il valore precedente.
- ✅ Aggiunto `sosta_temporanea_giornaliera: Optional[float] = None` in `TariffeUpdate`.
- ✅ Test: PUT 33.5 → GET 33.5 (prima: PUT 33.5 → GET 25.0). Ripristinato valore a 25 per non alterare i clienti esistenti.

## Iter30 (2026-02-20) — BUGFIX: salvataggio cliente sosta temporanea
- 🐛 **BUG risolto**: `create_cliente` e `update_cliente` validavano `tipo_sosta not in ("dentro","fuori","fuori_sede")` **senza includere "temporanea"** → HTTP 400 al salvataggio.
- ✅ Aggiunto "temporanea" nella whitelist di validazione in entrambi gli endpoint POST/PUT `/api/clienti`.
- ✅ Testing_agent iter12: **100% PASS backend+frontend** — creazione end-to-end via UI (Gommone 6m, 5 giorni temporanea) salva correttamente, badge "Piazzale (temp.)", modifica dei giorni funzionante.

## Iter29 (2026-02-20) — Sosta temporanea = sempre su piazzale
- ✅ Migrazione automatica all'avvio: clienti esistenti con `tipo_sosta="temporanea"` ricevono `alaggio_varo_attivo=True` (visto che sono sempre su piazzale).
- ✅ Frontend `ClienteForm.jsx`: quando l'utente seleziona `tipo_sosta="temporanea"`, `alaggio_varo_attivo` viene attivato automaticamente. Testo informativo sotto il campo giorni: "Sosta temporanea = sempre su piazzale (fuori). Tariffa: € / giorno / metro."
- ✅ Lista clienti `Clienti.jsx`: il badge per temporanea ora mostra "Piazzale (temp.)" per riflettere la natura outdoor.

## Iter28 (2026-02-20) — Filtro Pagati/Non pagati e riepilogo incassi
- ✅ **3 card KPI cliccabili** sopra la lista: "Tutti", "Da incassare" (rosso, con totale € e conteggio non pagati), "Incassato" (verde, con totale € e conteggio pagati). Click → filtra la lista.
- ✅ **Dropdown filtro "Pagamento"** (data-testid `filter-pagamento`) affianco al filtro tipo sosta: Tutti / Solo non pagati / Solo pagati.
- ✅ **Nuova colonna "Pagamento"** nella tabella con badge verde "Pagato" o outline rosso "Non pagato".
- ✅ **Toggle rapido pagato/non pagato** (data-testid `btn-toggle-pagato-{id}`) tra le azioni riga: icona check verde se non pagato → segna come pagato (data odierna); icona X rossa se pagato → segna come non pagato.
- ✅ Test PUT diretto backend conferma il flag `pagato` e `data_pagamento` vengono aggiornati.

## Iter27 (2026-02-20) — Sosta temporanea: tariffa × giorni × metri
- ✅ `calcola_costi`: per `tipo_sosta="temporanea"` il costo è ora `lunghezza × giorni × sosta_temporanea_giornaliera` (prima solo `giorni × tariffa`).
- ✅ Aggiornati label pagina Tariffe e PDF Listino: "€ / giorno / metro".
- ✅ Test: L=7 × 10 gg × 25€ = 1.750€. L=5 × 5 gg × 25€ = 625€ (con tariffa base 25).

## Iter26 (2026-02-20) — Home: nuova collocazione e aspetto dei tasti
- ✅ Hero snellito: 3 sole azioni principali ("Vai al gestionale" primario con shadow, "Gestione clienti" outline con icona Anchor, "Info cantiere" ghost).
- ✅ Nuova sezione **"Azioni rapide"** con 3 card icona+titolo+sottotitolo per: Preventivo veloce (card primary evidenziata), Listino prezzi PDF, Excel commercialista. Ogni card con hover lift, ombra e freccia animata.
- ✅ Nuovo componente `QuickActionCard` con supporto onClick e href (download/newTab).

## Iter25 (2026-02-20) — Dettaglio cliente in-app (senza scaricare PDF)
- ✅ Nuovo componente `/app/frontend/src/pages/ClienteDettaglio.jsx`: dialog che mostra il conteggio completo di ogni cliente direttamente in pagina.
- ✅ Sezioni: Sosta & trattamenti · Alaggio & Varo (con destinazione e × N mov.) · Manutenzione motore (dettaglio 1°+2°) · Lavorazioni extra riga per riga · **TOTALE ANNUALE** grande.
- ✅ Info sintesi in alto: barca, sosta, posto, stato pagamento.
- ✅ Nuova icona "occhio" nella lista clienti (`btn-dettaglio-{id}`) apre il dialog. Pulsante "Scarica preventivo PDF" all'interno del dialog per continuità.
- ✅ Nasconde automaticamente le voci a 0 € per una lettura pulita.
- 🐛 **BUGFIX**: il componente `<ClienteDettaglio>` era importato ma non veniva renderizzato nel JSX di `Clienti.jsx` → l'icona occhio non apriva nulla. Aggiunto rendering del componente. Testing_agent iter11: 100% PASS su tutti gli scenari (apertura dialog, contenuto, chiusura Chiudi/ESC/click-esterno, PDF link, totale coerente con lista).

## Iter24 (2026-02-20) — Moltiplicatore movimenti alaggio+varo
- ✅ Backend: nuovo campo `numero_movimenti: int = 1` su `Cliente` (Optional in `ClienteCreate`). `calcola_costi` accetta il parametro e moltiplica `costo_alaggio` e `costo_varo` per il numero di movimenti richiesti (solo con destinazione="marina_di_campo"; per "altra" resta manuale).
- ✅ Endpoint `/api/calcola-costi` accetta `numero_movimenti`. Test: L=8, 3 movimenti → 300€/300€ (100€ forfait × 3).
- ✅ POST/PUT clienti, preventivo_pdf_inline, duplicazione anno e ricalcola-anno passano il nuovo parametro.
- ✅ PDF preventivo: voci "Alaggio × N mov." e "Varo × N mov." (mostrate solo se N>1).
- ✅ Excel export: nuova colonna "N° movimenti".
- ✅ Frontend `ClienteForm.jsx`: nel blocco "Destinazione alaggio / varo" (visibile solo se toggle ON) c'è un input "Numero movimenti (alaggio + varo)" con placeholder e testo esplicativo.

## Iter23 (2026-02-20) — Alaggio/Varo oltre 5 m come forfait
- ✅ Backend `calcola_alaggio` e `calcola_varo`: la tariffa `alaggio_oltre_5m_per_metro` (e la corrispondente per il varo) è ora trattata come **forfait fisso** per barche > 5 m (prima veniva moltiplicata per la lunghezza). Nome del campo mantenuto per compatibilità DB.
- ✅ PDF Listino e pagina Tariffe: descrizione aggiornata a "Forfait per barche > 5 m".
- ✅ Simulazione anteprima Tariffe usa il valore fisso.
- ✅ Test: L=8 → tariffa forfait "oltre 5m" fissa (non 8× moltiplicato). L=4 → tariffa forfait "fino a 5m".

## Iter22 (2026-02-20) — Ricalcolo automatico all'aggiornamento tariffe
- ✅ Backend: nuovo endpoint `POST /api/tariffe/ricalcola?anno=X` che ricalcola i costi di tutti i clienti dell'anno indicato usando le tariffe correnti. Rispetta `override_costi` (non tocca chi ha costi manuali globali) e destinazione="altra" per alaggio/varo (preserva valori manuali di destinazioni diverse).
- ✅ Frontend `Tariffe.jsx`: salvando le tariffe viene automaticamente chiamato l'endpoint con l'anno in corso (`useYear` context). Toast informa "Tariffe aggiornate · N/M clienti YYYY ricalcolati".

## Iter21 (2026-02-20) — Alaggio/Varo modificabili con destinazione "Altra"
- ✅ Frontend `ClienteForm.jsx`: quando `alaggio_varo_attivo=true` e destinazione="altra" i campi Alaggio/Varo mostrano la **tariffa Marina di Campo come punto di partenza** (pre-fill automatico se valore=0). L'utente può poi modificarli liberamente in base alla nuova destinazione.
- ✅ Preserva i valori manuali: cambi di lunghezza/motore non azzerano più i costi alaggio/varo digitati manualmente.
- ✅ Testo di aiuto aggiornato: "Modifica i costi qui sotto se il movimento verso questa destinazione ha un prezzo diverso dalla tariffa di Marina di Campo."

## Iter20 (2026-02-20) — Spunta indipendente "Alaggio e varo"
- ✅ Nuovo campo `alaggio_varo_attivo: bool = False` su `Cliente` (Optional in `ClienteCreate`).
- ✅ `calcola_costi`: quando `alaggio_varo_attivo=True` i costi alaggio/varo vengono **sempre calcolati** indipendentemente dal tipo di sosta (dentro/fuori/fuori_sede/temporanea). Se destinazione="altra" → costi manuali.
- ✅ Endpoint `/api/calcola-costi` accetta `alaggio_varo_attivo`. Verificato: dentro+7m+attivo=marina → 700€/700€. dentro+attivo=false → 0€. attivo+altra → 0€ (manuale).
- ✅ create/update cliente, preventivo_pdf_inline e duplicazione anno passano il nuovo parametro.
- ✅ **Migrazione iter20** all'avvio: clienti con `tipo_sosta="fuori"` esistenti ricevono `alaggio_varo_attivo=True` (preserva comportamento pre-esistente). Idempotente.
- ✅ Frontend `ClienteForm.jsx`: nuovo toggle "Alaggio e varo" (`switch-alaggio-varo`). Blocco destinazione + costi alaggio/varo ora visibile per **qualsiasi tipo di sosta** quando il toggle è attivo. Deps `useEffect` aggiornate.
- ✅ Test CRUD: POST cliente sosta="dentro"+alaggio_attivo=true → costo_alaggio/varo 600€ calcolati. PDF preventivo contiene "Alaggio" e "Varo" ✅.

## Iter19 (2026-02-20) — Export Excel completo per commercialista
- ✅ Backend `/api/export/clienti.xlsx?anno=X`: rigenerato da zero. 33 colonne human-readable in italiano (Anno, Posto, Cognome, Nome, CF, Indirizzo, Contatti, Barca, Lunghezza, Tipo sosta, Destinazione alaggio, tutti i costi separati con "€", Lavorazioni extra €, TOTALE €, Pagato, Scadenze, Note).
- ✅ Formattazione openpyxl: header navy + testo bianco, riga TOTALI arancio con formule `=SUM()` sulle colonne valuta, formato `#,##0.00 "€"`, larghezze personalizzate, freeze panes A2. Filtro per anno con sheet name "Clienti YYYY".
- ✅ Frontend `Clienti.jsx`: bottone Excel passa `?anno=` corrente.
- ✅ Frontend `Home.jsx`: nuovo CTA "Excel clienti (commercialista)" accanto a Listino prezzi.
- ✅ Test: HTTP 200, file .xlsx 7.4KB, riga TOTALI in fondo con formule SUM.

## Iter18 (2026-02-20) — Lavaggi stagionali al metro lineare
- ✅ Backend: `costo_lavaggio_inizio_stagione` e `costo_lavaggio_fine_stagione` ora sono **tariffe al metro** e vengono moltiplicate per la lunghezza barca in `calcola_costi`.
- ✅ PDF Listino: gruppo "Copertura & trattamenti scafo" mostra "€ / metro" per i lavaggi (prima "forfait").
- ✅ Frontend Tariffe: descrizione dei lavaggi aggiornata a "€ / metro".
- ✅ Test API: L=8 con tariffa 80 → 640€ · L=5 → 400€.

## Iter17 (2026-02-20) — Destinazione alaggio/varo (Marina di Campo vs Altra)
- ✅ Nuovi campi `destinazione_alaggio_varo: str = "marina_di_campo"` e `destinazione_altra_nome: str = ""` su `Cliente` (Optional in `ClienteCreate`).
- ✅ `calcola_costi` estesa: se `destinazione_alaggio_varo == "altra"` e `tipo_sosta == "fuori"` → costo_alaggio/varo restituiti a 0 (l'utente li compila manualmente).
- ✅ Endpoint `/api/calcola-costi` accetta il nuovo parametro. Verificato: Marina + 6m → 600€/600€. Altra + 6m → 0€/0€.
- ✅ `create_cliente`/`update_cliente`/`preventivo_pdf_inline`: quando destinazione="altra", i costi alaggio/varo dell'utente sono sempre preservati (bypass di `override_costi`).
- ✅ PDF preventivo: le voci "Alaggio" e "Varo" mostrano il nome destinazione tra parentesi se destinazione="altra" (es. "Alaggio (Portoferraio)").
- ✅ Frontend `ClienteForm.jsx`: nuovo blocco "Destinazione alaggio / varo" (visibile solo per sosta="fuori") con Select 2 opzioni (Marina di Campo / Altra destinazione) + input testo "Nome destinazione" quando "Altra". I campi Alaggio/Varo diventano editabili senza bisogno di override quando destinazione="altra".
- ✅ Test CRUD backend: POST altra+Portoferraio→350€ preservato · PUT switch a marina_di_campo → auto-ricalcolo 750€ per 7.5m ✅

### P1 — enhancements (aggiornato)
- [ ] Calendario scadenze completo con view mensile (shadcn Calendar)
- [ ] PDF export bello (fattura preventivo per cliente)
- [ ] Sistema promemoria email/SMS per scadenze (integrazione Resend/Twilio)
- [ ] Upload foto barca / documenti (object storage)
- [ ] Storico lavori strutturato (invece di note libere): data, tipo, costo, materiali

### P2 — future
- [ ] Multi-utente con ruoli (segreteria vs meccanico)
- [ ] Report annuale con grafici entrate mensili
- [ ] Autenticazione biometrica via WebAuthn
- [ ] Assegnazione automatica posto barca in base a lunghezza
- [ ] Integrazione WhatsApp Business per comunicazioni clienti


## 2026-06 – Foto da fotocamera (Magazzino)
- Aggiunto pulsante "Scatta foto" (input file con `capture="environment"`) accanto a "Da file" in: form articolo, Scan articolo AI, Scan DDT AI. Su cellulare apre la fotocamera posteriore; su PC apre il selettore file.


## 2026-06 – Lavori dal cantiere (app dipendenti)
- Bluetooth verso browser non possibile → scelto: API via internet + QR offline.
- Backend: `routers/dipendenti.py` (CRUD dipendenti con chiave PM-XXXX-XXXX-XXXX hashata sha256; coda `lavori_pending` con approva/rifiuta/import-qr), `routers/mobile.py` (prefisso /api/mobile, header X-Api-Key: me, clienti, articoli, POST lavori con dedupe client_uid). Lavoro ha nuovi campi `ore`, `dipendente`. Backup include `dipendenti`, `lavori_pending`.
- Frontend: pagina /dipendenti "Lavori dal cantiere" (tab Da approvare + Dipendenti e chiavi con QR chiave); PWA pubblica /app-dipendente (login chiave/QR, coda offline in localStorage, Invia, Mostra QR paginato 6 lavori/pagina, manifest.json + sw.js). LavoriSection mostra ore/dipendente.
- Nota: AuthProvider/YearProvider e interceptor 401 saltano il path /app-dipendente (rotta pubblica).
- Test: iteration_17.json (19/19 backend, frontend OK dopo fix ApprovaDialog null + redirect PWA).


## 2026-06 – Programma "nativo" senza dipendenze Emergent
- `backend/ai_client.py`: vision AI con provider da .env → GEMINI_API_KEY (REST Google diretto, modello GEMINI_MODEL default gemini-2.5-flash) oppure fallback EMERGENT_LLM_KEY. Usato da magazzino/suzuki/gommoni.
- `email_service.py`: SMTP standard (SMTP_HOST/PORT/USER/PASSWORD/FROM, es. Aruba) con fallback proxy Emergent.
- index.html ripulito (no emergent-main.js/posthog); rimosso pacchetto @emergentbase/visual-edits (craco lo gestisce come opzionale).
- `deploy/`: Dockerfile.backend, Dockerfile.frontend (build React → Caddy con HTTPS automatico), Caddyfile, docker-compose.yml (mongo, backend, frontend, backup giornaliero), .env.example, INSTALLAZIONE.md (dominio genbnautica.it su Aruba).
- `docs/API_MOBILE.md`: documentazione API app dipendenti.
- `mobile_android/`: progetto Flutter (login chiave/QR, nuovo lavoro, coda, invio, QR paginato). NON compilato/testato in questo ambiente (richiede Android SDK).
- Verifiche: build produzione frontend OK, ai_client OK, backend OK.

## 2026-06 – Costo orario manodopera
- Nuovo campo `costo_orario_manodopera` (Tariffe, default 45 €/h) in pagina Tariffe (gruppo "Manodopera generica") e nel PDF Listino prezzi rimessaggio (sezione MANODOPERA GENERICA).

## 2026-06 – App dipendenti separata dal gestionale
- Host dedicato `lavori.<dominio>` (APP_DOMAIN in deploy/.env): App.js rende SOLO AppDipendente su quel host (`lib/appHost.js`); Caddy espone solo /api/mobile/* (resto 403) e sul dominio principale /app-dipendente reindirizza all host app. QR chiave e link usano REACT_APP_APP_DIPENDENTI_HOST se impostato. In preview resta /app-dipendente.

## 2026-06 – Costo automatico ore
- Approvazione lavoro: costo manodopera = ore × costo_orario_manodopera (Tariffe), precompilato e ricalcolato nel dialogo (modificabile); fallback lato server se costo assente/0.

## 2026-06 – Archivio report dipendenti
- Tab "Archivio report" in /dipendenti: tutti i report ricevuti (nome dipendente, data lavoro, data ricezione, stato), filtri per dipendente/stato, eliminazione singola e multipla (POST /lavori-pending/elimina {ids}). I lavori approvati restano nella scheda cliente.

## 2026-06 – Fix: lavoro approvato non visibile in scheda cliente
- Causa: clienti per-anno; app sceglieva scheda anno più recente. Fix: GET /clienti/{id}/lavori unisce i lavori di tutte le schede annuali della stessa persona (cognome+nome); /api/mobile/clienti sceglie la scheda dell anno corrente.

## 2026-06 – Lavori storico nei totali/preventivi
- Denormalizzazione: `sync_lavori_cliente` (routers/lavori.py) scrive su ogni scheda annuale della persona `costo_lavori` e `lavori_storico` (lavori con data nell anno della scheda). Chiamata su create/update/delete lavoro; migrazione al primo avvio.
- Inclusi in: dettaglio cliente (sezione "Lavori eseguiti"), totale lista clienti, PDF preventivo, PDF storico multi-anno, report/stats (via _totale_extra), export Excel (colonna "Lavori eseguiti €").

## 2026-06 – Lavorazioni esterne
- Collezione `clienti_esterni` (solo nominativo, telefono, note) + `routers/esterni.py`; pagina /esterni con scheda lavori (riusa LavoriSection; POST /lavori accetta id esterno).
- App dipendenti: se il cliente non è in archivio, pulsante "+ Nuovo cliente" (cliente_id null, cliente_nome, nuovo_cliente). In approvazione: scelta "Nuovo cliente esterno" (body esterno_nome → crea esterno e lavoro) oppure "Cliente già in archivio". I clienti esterni compaiono anche nella lista clienti dell app.

## 2026-06 – Conto PDF lavorazioni esterne
- GET /api/esterni/{id}/conto.pdf?anno= (inline) → `build_conto_esterno_pdf` in pdf_builders.py. Pagina /esterni: selettore anno/tutti, pulsante "Conto PDF" per riga e nel dialog scheda; anteprima con PdfPreviewOverlay prima del download.

## 2026-06 – Rifinitura finale (Home professionale)
- Home: griglia 8 riquadri-modulo (`components/ModuleTile.jsx`) con numeri da GET /api/home/riepilogo (stats.py); hero più compatto.
- Sidebar raggruppata (Officina · Vendita · Documenti) con badge "da approvare" aggiornato via evento window `pending-changed` + focus.
- PWA: riquadro "Installa sul telefono" (beforeinstallprompt) in LoginKey.
- Fix da iteration_18: ApprovaDialog carica tariffa prima di inizializzare il form (nessuna race); plurale "1 lavoro".
- Test: iteration_18.json (frontend regression), fix verificati via screenshot.

## 2026-06 – Fix elimina cliente esterno
- DELETE /esterni/{id} ora elimina anche i lavori collegati (via delete_lavoro, ripristina giacenze) invece di bloccare con 400; conferma esplicita nel frontend.

## 2026-06 – Documenti di servizio (Banca & Privacy)
- `routers/servizio.py` + collezione singleton `documenti_servizio`: dati bancari (IBAN → CIN/ABI/CAB/conto calcolati), testo privacy modificabile (default GDPR con segnaposto {cantiere} {indirizzo} {telefono} {email}), POST /servizio/privacy/estrai (AI vision trascrive PDF/foto), GET /servizio/coordinate.pdf[?cliente_id&importo&causale], GET /servizio/privacy.pdf[?cliente_id]. Builder `build_documento_servizio_pdf`.
- Pagina /servizio "Banca & Privacy" (tab Dati bancari / Consenso privacy) con anteprima PDF; voce menu in Documenti.

## 2026-06 – Fix anteprima PDF Banca & Privacy
- Causa: openBlob passa un updater-function a setUrl; in DocumentiServizio veniva salvata la funzione invece dell URL blob. Fix: useState dedicato previewUrl. Nota per il futuro: passare a openBlob sempre un setter di useState diretto.

## 2026-06 – Privacy 1 pagina + verifica backup
- build_documento_servizio_pdf: per il consenso riduce progressivamente scala font/margini finché pdf.page <= 1 (sempre un solo A4).
- Verificato backup GET /api/backup (26 collezioni + GridFS) e POST /api/restore round-trip (marker eliminato, conteggi corretti).

## 2026-06 – Preventivi clienti esterni
- Collezione `preventivi_esterni` (numerazione annuale). Endpoint in routers/esterni.py: GET/POST /esterni/{id}/preventivi, PUT/DELETE /esterni/preventivi/{pid}, GET .../pdf (build_preventivo_esterno_pdf), POST .../converti → crea Lavoro via create_lavoro (scarico magazzino, ore manodopera, costo netto voci non-articolo).
- UI: pulsante "Preventivo" per riga in /esterni; nel dialog scheda tab Lavori eseguiti / Preventivi; editor righe (manodopera a tariffa oraria, ricerca ricambi magazzino con prezzo listino e giacenza, voci libere), sconto/IVA, PDF anteprima, "Crea lavoro".

## 2026-06 – Ricambi non in magazzino nei preventivi esterni
- Riga tipo articolo con articolo_id null: pulsante "Ricambio non in magazzino" + opzione nella ricerca "Aggiungi ... come ricambio non in magazzino". In conversione a lavoro contano nel costo (non scaricano magazzino).

## 2026-06 – Euro spaziato + IVA scorporata
- helpers._euro usa "€" + 2 nbsp (tutti i PDF). Preventivo esterno: ricambi da magazzino inseriti a prezzo netto (listino / (1+IVA)) nel frontend; intestazione colonna "PREZZO (netto)" e nota IVA nel PDF.

## 2026-06 – Azioni rapide spostate in Rimessaggio
- Rimosse da Home (QuickActionCard, dialog Excel). In Clienti.jsx header: Preventivo veloce (ClienteForm mode=preventivo), Listino prezzi PDF, CSV, "Excel commercialista {anno}" (usa anno di lavoro selezionato).

## 2026-06 – ArticoloPicker (ricerca articolo ovunque)
- `components/ArticoloPicker.jsx`: ricerca per codice/nome con elenco risultati (giacenza, prezzo). Sostituisce le tendine in LavoriSection (scheda cliente/esterni), Magazzino → Movimenti (carico/scarico/rettifica) e app dipendenti (NuovoLavoro). Preventivo esterno aveva già la ricerca.

## 2026-06 – Costo manodopera predefinito nel lavoro
- LavoriSection: costo = ore × costo_orario_manodopera (Tariffe) finché l utente non modifica il costo a mano (flag costoManuale); hint "60 €/h da Tariffe". In modifica lavoro il costo non viene ricalcolato automaticamente.

## 2026-06 – Campi numerici vuoti invece di 0
- components/ui/input.jsx: per type=number il valore 0/"0" viene mostrato vuoto (globale); al focus su "0" seleziona il testo. Il salvataggio usa Number(x)||0 quindi nessun impatto.

## 2026-06 – Finestra Nuovo lavoro più grande
- lavoro-dialog max-w-4xl w-[95vw] max-h-[92vh]; descrizione → Textarea 3 righe; materiali 3 righe. esterno-dialog max-w-5xl.
