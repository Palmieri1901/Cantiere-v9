import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, API } from "@/lib/api";
import { salvaBackupInCartella } from "@/lib/backupFolder";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sailboat, MapPin, Phone, Mail, Clock, ArrowRight, Anchor, Building2, Globe, Database, Download, Upload, AlertTriangle, Settings, Package, Ship, LifeBuoy, Truck, Smartphone, HardHat } from "lucide-react";
import { ModuleTile } from "@/components/ModuleTile";
import { toast } from "sonner";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "@/components/ui/alert-dialog";

export default function Home() {
  const [c, setC] = useState(null);
  const restoreRef = useRef(null);
  const [restoreData, setRestoreData] = useState(null);
  const [restoring, setRestoring] = useState(false);
  const [backingUp, setBackingUp] = useState(false);
  const [backupInfo, setBackupInfo] = useState(null);
  const [r, setR] = useState(null);

  const doBackup = async () => {
    setBackingUp(true);
    try {
      const r = await salvaBackupInCartella();
      if (r.mode === "folder") {
        toast.success(`Backup salvato in "${r.folder}" · ${r.kept} copie conservate${r.deleted ? ` · ${r.deleted} vecchie eliminate` : ""}`);
      } else {
        toast.success(`Backup salvato: ${r.filename}`);
        if (r.mode === "download") toast.info("Il browser non permette di scegliere la cartella: file scaricato nella cartella Download.");
      }
      api.get("/backup/ultimo").then((x) => setBackupInfo(x.data)).catch(() => {});
    } catch (e) {
      if (e?.name === "AbortError") return;
      toast.error(e?.response?.data?.detail || e?.message || "Errore durante il backup");
    } finally { setBackingUp(false); }
  };
  const currentYear = new Date().getFullYear();

  const load = () => {
    api.get("/cantiere").then((r) => setC(r.data));
    api.get("/backup/ultimo").then((r) => setBackupInfo(r.data)).catch(() => {});
    api.get("/home/riepilogo").then((x) => setR(x.data)).catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const onRestoreSelected = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        // Un backup valido deve contenere almeno una sezione riconosciuta
        const hasAny = (data.collections && Object.keys(data.collections).length > 0) ||
          ["clienti", "lavori", "tariffe", "cantiere", "articoli", "fornitori", "spese_accessorie", "movimenti_magazzino", "ricarichi_categoria"]
            .some((k) => data[k] !== undefined && data[k] !== null);
        if (!hasAny) {
          toast.error("File di backup non valido");
          return;
        }
        setRestoreData(data);
      } catch {
        toast.error("File JSON non valido");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const doRestore = async () => {
    if (!restoreData) return;
    setRestoring(true);
    try {
      const r = await api.post("/restore", restoreData);
      const rst = r.data.restored;
      const parts = Object.entries(rst).filter(([, n]) => n).map(([k, n]) => `${n} ${k.replace(/_/g, " ")}`);
      toast.success(`Ripristinati: ${parts.join(" · ") || "impostazioni"}`);
      setRestoreData(null);
      load();
    } catch {
      toast.error("Errore durante il ripristino");
    } finally {
      setRestoring(false);
    }
  };

  if (!c) return <div className="p-8 text-muted-foreground">Caricamento…</div>;

  const address = [c.indirizzo, [c.cap, c.citta, c.provincia && `(${c.provincia})`].filter(Boolean).join(" ")].filter(Boolean).join(", ");

  return (
    <div className="min-h-screen bg-background" data-testid="home-page">
      {/* Hero */}
      <div className="relative overflow-hidden bg-gradient-to-b from-secondary/40 to-background border-b border-border">
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{
          backgroundImage: "radial-gradient(circle at 20% 30%, hsl(var(--primary)) 1px, transparent 1px), radial-gradient(circle at 80% 70%, hsl(var(--chart-2)) 1px, transparent 1px)",
          backgroundSize: "60px 60px, 80px 80px",
        }} />
        <div className="relative max-w-6xl mx-auto px-6 md:px-10 py-12 md:py-16">
          {c.logo_base64 ? (
            <img src={c.logo_base64} alt="Logo" className="h-20 md:h-24 mb-6 object-contain" data-testid="home-logo" />
          ) : (
            <div className="w-16 h-16 rounded-lg bg-primary text-primary-foreground grid place-items-center mb-6">
              <Sailboat className="w-9 h-9" strokeWidth={1.8} />
            </div>
          )}

          <div className="label-mini mb-3">Cantiere Nautico</div>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-foreground leading-[1.02]">
            {c.nome}
          </h1>
          {c.slogan && (
            <p className="mt-4 text-lg md:text-xl text-muted-foreground max-w-2xl font-display italic">
              {c.slogan}
            </p>
          )}

          <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="home-moduli">
            <ModuleTile to="/clienti" icon={Anchor} title="Rimessaggio" desc="Clienti, barche, posti e preventivi annuali" stat={r?.clienti} statLabel={`clienti ${r?.anno || ""}`} accent testId="cta-clienti" />
            <ModuleTile to="/magazzino" icon={Package} title="Magazzino" desc="Articoli, fornitori, carichi e scarichi" stat={r?.articoli} statLabel={r?.sotto_scorta > 0 ? `articoli · ${r.sotto_scorta} sotto scorta` : "articoli"} testId="cta-magazzino" />
            <ModuleTile to="/dipendenti" icon={Smartphone} title="Lavori dal cantiere" desc="Report dei dipendenti da approvare" stat={r?.pending} statLabel="da approvare" badge={r?.pending} testId="cta-dipendenti" />
            <ModuleTile to="/esterni" icon={HardHat} title="Lavorazioni esterne" desc="Clienti fuori rimessaggio e conti PDF" stat={r?.esterni} statLabel="clienti esterni" testId="cta-esterni" />
            <ModuleTile to="/tubolari" icon={Ship} title="Tubolari" desc="Preventivi rifacimento tubolari" stat={r?.tubolari} statLabel="preventivi" testId="cta-tubolari" />
            <ModuleTile to="/suzuki" icon={Sailboat} title="Fuoribordo Suzuki" desc="Catalogo motori e preventivi" stat={r?.suzuki} statLabel="modelli" testId="cta-suzuki" />
            <ModuleTile to="/gommoni" icon={LifeBuoy} title="Gommoni GEB" desc="Modelli, accessori e preventivi" stat={r?.gommoni} statLabel="modelli" testId="cta-gommoni" />
            <ModuleTile to="/ddt" icon={Truck} title="DDT & Destinazione" desc="Documenti di trasporto e rubrica" stat={r?.ddt} statLabel={`DDT ${r?.anno || ""}`} testId="cta-ddt" />
          </div>
          <div className="mt-6">
            <Link to="/impostazioni" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors" data-testid="cta-impostazioni">
              <Settings className="w-4 h-4" /> Impostazione dati cantiere
            </Link>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="max-w-6xl mx-auto px-6 md:px-10 py-14 grid grid-cols-1 gap-6">
        {/* Contatti */}
        <Card className="p-6" data-testid="home-contatti">
          <div className="label-mini mb-4 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5" /> Sede & contatti
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {address && (
              <InfoBlock icon={MapPin} label="Indirizzo" testId="info-indirizzo">
                {address}
              </InfoBlock>
            )}
            {c.telefono && (
              <InfoBlock icon={Phone} label="Telefono" testId="info-telefono">
                <a href={`tel:${c.telefono}`} className="hover:text-primary">{c.telefono}</a>
              </InfoBlock>
            )}
            {c.email && (
              <InfoBlock icon={Mail} label="Email" testId="info-email">
                <a href={`mailto:${c.email}`} className="hover:text-primary">{c.email}</a>
              </InfoBlock>
            )}
            {c.orari && (
              <InfoBlock icon={Clock} label="Orari" testId="info-orari">
                {c.orari}
              </InfoBlock>
            )}
            {c.sito_web && (
              <InfoBlock icon={Globe} label="Sito web" testId="info-sito">
                <a href={c.sito_web.startsWith("http") ? c.sito_web : `https://${c.sito_web}`} target="_blank" rel="noreferrer" className="hover:text-primary">
                  {c.sito_web}
                </a>
              </InfoBlock>
            )}
            {c.piva && (
              <InfoBlock icon={Building2} label="P.IVA" testId="info-piva">
                {c.piva}
              </InfoBlock>
            )}
          </div>

          {!address && !c.telefono && !c.email && !c.orari && (
            <div className="text-sm text-muted-foreground bg-muted/40 rounded-md p-4 border border-dashed border-border">
              Nessuna informazione impostata. <Link to="/impostazioni" className="text-primary underline">Aggiungi ora →</Link>
            </div>
          )}
        </Card>
      </div>

      {/* Backup & Ripristino */}
      <div className="max-w-6xl mx-auto px-6 md:px-10 pb-14">
        {backupInfo?.scaduto && (
          <div className="mb-4 flex items-start gap-3 rounded-lg border-2 border-amber-400 bg-amber-50 px-4 py-3 text-amber-900" data-testid="backup-reminder">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-amber-600" />
            <div className="flex-1 text-sm">
              <div className="font-semibold">Promemoria backup</div>
              <div>
                {backupInfo.ultimo_backup
                  ? <>L'ultimo backup risale a <b>{backupInfo.giorni} giorni</b> fa ({new Date(backupInfo.ultimo_backup).toLocaleDateString("it-IT")}). Ti consigliamo di salvarne uno nuovo.</>
                  : <>Non è mai stato eseguito un backup. Salva subito una copia di sicurezza di tutti i dati.</>}
              </div>
            </div>
            <Button size="sm" onClick={doBackup} disabled={backingUp} className="bg-amber-600 hover:bg-amber-700 text-white shrink-0" data-testid="btn-backup-reminder">
              <Download className="w-4 h-4 mr-1.5" /> Salva backup ora
            </Button>
          </div>
        )}
        <Card className="p-6" data-testid="home-backup">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 label-mini mb-2">
                <Database className="w-3.5 h-3.5" /> Backup dati
              </div>
              <h3 className="font-display text-xl font-semibold">Backup completo & Ripristino</h3>
              {backupInfo?.ultimo_backup && !backupInfo.scaduto && (
                <div className="text-xs text-emerald-700 mt-1" data-testid="backup-last-ok">
                  Ultimo backup: {new Date(backupInfo.ultimo_backup).toLocaleString("it-IT")} ({backupInfo.giorni === 0 ? "oggi" : `${backupInfo.giorni} giorni fa`})
                </div>
              )}
              <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
                Scarica un file di backup con <b>tutto l'archivio di ogni settore</b>: Rimessaggio (clienti, lavori, tariffe, cantiere),
                Magazzino, Tubolari, Suzuki, Gommoni GEB (con PDF omologazione), DDT e rubrica indirizzi. Conservalo come
                archivio o ripristinalo in caso di problemi. Al salvataggio ti verrà chiesta la <b>cartella</b> di destinazione:
                vengono conservate al massimo <b>3 copie</b>, le più vecchie si eliminano automaticamente.
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <Button variant="outline" size="lg" onClick={doBackup} disabled={backingUp} data-testid="btn-home-backup-download">
                <Download className="w-4 h-4 mr-2" />
                {backingUp ? "Salvataggio…" : "Salva backup"}
              </Button>
              <input ref={restoreRef} type="file" accept="application/json,.json" hidden onChange={onRestoreSelected} data-testid="input-home-restore-file" />
              <Button variant="outline" size="lg" onClick={() => restoreRef.current?.click()} data-testid="btn-home-restore-open">
                <Upload className="w-4 h-4 mr-2" />
                Recupera backup
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <AlertDialog open={!!restoreData} onOpenChange={(o) => !o && setRestoreData(null)}>
        <AlertDialogContent data-testid="home-restore-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Confermi il ripristino?
            </AlertDialogTitle>
            <AlertDialogDescription>
              <div className="space-y-2 mt-2">
                <div>Il backup contiene:</div>
                {restoreData?.collections ? (
                  <ul className="list-disc pl-5 text-sm space-y-1 max-h-48 overflow-y-auto" data-testid="restore-summary">
                    {Object.entries(restoreData.settori || {}).map(([settore, colls]) => {
                      const n = colls.reduce((s, c) => s + (restoreData.collections[c]?.length || 0), 0);
                      return <li key={settore}><b>{settore}</b>: {n} record</li>;
                    })}
                    {Object.entries(restoreData.files_counts || {}).map(([b, n]) => <li key={b}>File {b.replace(/_/g, " ")}: <b>{n}</b></li>)}
                  </ul>
                ) : (
                <ul className="list-disc pl-5 text-sm space-y-1">
                  <li><b>{restoreData?.clienti?.length || 0}</b> clienti</li>
                  <li><b>{restoreData?.lavori?.length || 0}</b> lavori</li>
                  <li><b>{restoreData?.articoli?.length || 0}</b> articoli magazzino</li>
                  <li><b>{restoreData?.fornitori?.length || 0}</b> fornitori</li>
                  <li><b>{restoreData?.spese_accessorie?.length || 0}</b> spese accessorie</li>
                  <li><b>{restoreData?.movimenti_magazzino?.length || 0}</b> movimenti magazzino</li>
                  <li><b>{restoreData?.ricarichi_categoria?.length || 0}</b> ricarichi per categoria</li>
                  <li>Tariffe: <b>{restoreData?.tariffe ? "sì" : "no"}</b></li>
                  <li>Cantiere: <b>{restoreData?.cantiere ? "sì" : "no"}</b></li>
                </ul>
                )}
                <div className="text-destructive mt-3 text-sm font-medium">
                  ⚠️ Tutti i dati attuali verranno sovrascritti. L'operazione non è reversibile.
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="home-restore-cancel">Annulla</AlertDialogCancel>
            <AlertDialogAction onClick={doRestore} disabled={restoring} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="home-restore-confirm">
              {restoring ? "Ripristino…" : "Sì, ripristina"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function InfoBlock({ icon: Icon, label, children, testId }) {
  return (
    <div data-testid={testId}>
      <div className="flex items-center gap-1.5 label-mini mb-1.5">
        <Icon className="w-3 h-3" /> {label}
      </div>
      <div className="text-sm text-foreground leading-relaxed">{children}</div>
    </div>
  );
}

