# Deploy su Railway

Guida per il dominio **gestionale.gebnautica.it**. Il gestionale su Railway
gira come 3 servizi separati nello stesso progetto: MongoDB, backend, frontend.

## 1. Crea il progetto
Su railway.app → **New Project** → **Deploy from GitHub repo** → seleziona
`Palmieri1901/Cantiere-v9`.

## 2. Servizio MongoDB
Nel progetto → **+ New** → **Database** → **Add MongoDB**.
Railway crea automaticamente la variabile `MONGO_URL` (o `MONGO_PUBLIC_URL`/
`MONGO_PRIVATE_URL`, a seconda della versione): la useremo nel backend.

## 3. Servizio Backend
**+ New** → **GitHub Repo** → stesso repo → dagli un nome, es. `backend`.

In **Settings** del servizio:
- **Root Directory**: lascia vuoto (usa la radice del repo)
- **Build** → aggiungi variabile `RAILWAY_DOCKERFILE_PATH` = `deploy/Dockerfile.backend`

In **Variables** del servizio, imposta:
```
MONGO_URL=${{MongoDB.MONGO_URL}}      # riferimento al servizio Mongo (autocompletato da Railway)
DB_NAME=portomare
FRONTEND_URL=https://gestionale.gebnautica.it
ADMIN_PASSWORD=<scegli una password forte>
RECOVERY_PIN=<scegli un pin>
JWT_SECRET=<stringa lunga casuale>
GEMINI_API_KEY=<opzionale, per le funzioni AI>
SMTP_HOST=<opzionale, per il recupero password via email>
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=...
EMAIL_FROM_NAME=Portomare
```
(Controlla `backend/database.py` e `backend/auth.py` per l'elenco esatto
delle variabili lette, i nomi sopra sono quelli usati nel `.env.example` del
deploy VPS.)

In **Settings → Networking**, attiva **Generate Domain** per avere un URL
pubblico tipo `backend-xxxx.up.railway.app` — ti servirà per il frontend, o
opzionalmente collega direttamente il tuo dominio `api.gebnautica.it`.

## 4. Servizio Frontend
**+ New** → **GitHub Repo** → stesso repo → nome `frontend`.

In **Settings**:
- **Root Directory**: vuoto
- **Build** → variabile `RAILWAY_DOCKERFILE_PATH` = `deploy/Dockerfile.frontend.railway`
- **Build Args** (Railway le passa come build-time ARG se le definisci come
  variabili con lo stesso nome): `REACT_APP_BACKEND_URL` = l'URL pubblico del
  servizio backend (es. `https://api.gebnautica.it` o l'URL `.up.railway.app`)

In **Settings → Networking → Custom Domain**, aggiungi `gestionale.gebnautica.it`.
Railway ti darà un record CNAME da creare nel pannello DNS del tuo dominio
(dove gestisci `gebnautica.it`). Railway emette da solo il certificato HTTPS
per questo dominio, una volta che il CNAME è propagato.

## 5. Nota sull'app dipendenti (sottodominio "lavori")
Nel deploy VPS, la separazione tra gestionale e app dipendenti è gestita da
Caddy in base al dominio (`Caddyfile`). Su Railway questa logica non c'è
ancora: se ti serve anche il sottodominio dedicato ai dipendenti, va
predisposto un servizio frontend aggiuntivo (stessa build, dominio diverso)
e una restrizione lato backend sulle rotte `/api/mobile/*`. Dimmi se vuoi che
lo prepari.

## 6. Differenze rispetto al VPS
- Niente Caddy, niente gestione manuale dei certificati: se ne occupa Railway
- Niente backup automatico giornaliero via container `backup`: valuta il
  backup integrato di Railway per MongoDB, o usa la funzione Home → Backup
  del programma stesso
- I costi sono a consumo (CPU/RAM/traffico), non un canone fisso da VPS
