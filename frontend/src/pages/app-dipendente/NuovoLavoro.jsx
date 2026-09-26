import { useMemo, useState } from "react";
import { mobileStore, uid } from "@/lib/mobileStore";
import { Button } from "@/components/ui/button";
import { ArticoloPicker } from "@/components/ArticoloPicker";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Save, Search, X } from "lucide-react";

const TIPI = ["Riparazione", "Manutenzione motore", "Antivegetativa", "Pulizia", "Elettrico", "Altro"];
const L = ({ children }) => <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{children}</Label>;
const empty = () => ({ cliente_id: "", cliente_nuovo: "", data: new Date().toISOString().slice(0, 10), tipo: "Riparazione", descrizione: "", ore: "", materiali: "", articoli: [] });

export default function NuovoLavoro({ onSaved }) {
  const clienti = mobileStore.clienti();
  const articoli = mobileStore.articoli();
  const [f, setF] = useState(empty());
  const [q, setQ] = useState("");
  const set = (k, v) => setF((s) => ({ ...s, [k]: v }));

  const filtrati = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return [];
    return clienti.filter((c) => `${c.cognome} ${c.nome} ${c.tipo_barca || ""}`.toLowerCase().includes(s)).slice(0, 8);
  }, [q, clienti]);
  const cliente = clienti.find((c) => c.id === f.cliente_id) || (f.cliente_nuovo ? { id: "", cognome: f.cliente_nuovo, nome: "", tipo_barca: "Nuovo cliente (non in archivio)" } : null);

  const addArt = (id) => { if (!id || f.articoli.some((a) => a.articolo_id === id)) return; set("articoli", [...f.articoli, { articolo_id: id, quantita: 1 }]); };

  const salva = () => {
    if (!f.cliente_id && !f.cliente_nuovo) return toast.error("Scegli il cliente");
    if (!f.descrizione.trim()) return toast.error("Descrivi il lavoro eseguito");
    const c = cliente;
    onSaved({
      client_uid: uid(), cliente_id: f.cliente_id || null, cliente_nome: `${c.cognome} ${c.nome}`.trim(), nuovo_cliente: !f.cliente_id, data: f.data, tipo: f.tipo,
      descrizione: f.descrizione.trim(), ore: Number(f.ore) || 0, materiali: f.materiali,
      articoli_magazzino: f.articoli.map((a) => ({ articolo_id: a.articolo_id, quantita: Number(a.quantita) || 1 })),
      creato_at: new Date().toISOString(), inviato: false,
    });
    setF(empty()); setQ("");
  };

  return (
    <div className="space-y-4" data-testid="nuovo-lavoro-mobile">
      <div className="space-y-1.5">
        <L>Cliente</L>
        {cliente ? (
          <div className="flex items-center gap-2 p-3 rounded-md border border-primary/40 bg-primary/5" data-testid="cliente-scelto">
            <div className="flex-1"><div className="font-semibold">{cliente.cognome} {cliente.nome}</div><div className="text-xs text-muted-foreground">{cliente.tipo_barca} {cliente.lunghezza ? `· ${cliente.lunghezza} m` : ""}</div></div>
            <button onClick={() => setF((s) => ({ ...s, cliente_id: "", cliente_nuovo: "" }))} data-testid="btn-cambia-cliente"><X className="w-4 h-4" /></button>
          </div>
        ) : (
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca cognome, nome o barca…" className="pl-9 h-12" data-testid="input-cerca-cliente" />
            {q.trim().length >= 3 && (
              <div className={`${filtrati.length > 0 ? "absolute z-20 left-0 right-0 mt-1 bg-card border rounded-md shadow-lg divide-y max-h-64 overflow-y-auto" : "mt-1"}`}>
                {filtrati.map((c) => (
                  <button key={c.id} onClick={() => { set("cliente_id", c.id); setQ(""); }} className="w-full text-left px-3 py-2.5 hover:bg-muted text-sm" data-testid={`cliente-opt-${c.id}`}>
                    <div className="font-medium">{c.cognome} {c.nome}</div><div className="text-xs text-muted-foreground">{c.tipo_barca}</div>
                  </button>
                ))}
                <button onClick={() => { set("cliente_nuovo", q.trim()); setQ(""); }} className="w-full text-left px-3 py-2.5 hover:bg-muted text-sm text-primary border border-dashed border-primary/40 rounded-md bg-primary/5" data-testid="btn-cliente-nuovo">
                  <div className="font-medium">+ Nuovo cliente: "{q.trim()}"</div><div className="text-xs text-muted-foreground">Non in archivio · verrà creato come cliente esterno</div>
                </button>
              </div>
            )}
            {clienti.length === 0 && <div className="text-xs text-amber-700 mt-1">Nessun cliente scaricato: premi l'icona aggiorna in alto quando sei online.</div>}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5"><L>Data</L><Input type="date" value={f.data} onChange={(e) => set("data", e.target.value)} className="h-12" data-testid="input-mobile-data" /></div>
        <div className="space-y-1.5"><L>Ore lavoro</L><Input type="number" inputMode="decimal" step="0.5" min="0" value={f.ore} onChange={(e) => set("ore", e.target.value)} placeholder="es. 10" className="h-12 font-mono-num" data-testid="input-mobile-ore" /></div>
      </div>
      <div className="space-y-1.5"><L>Tipo</L>
        <Select value={f.tipo} onValueChange={(v) => set("tipo", v)}>
          <SelectTrigger className="h-12" data-testid="select-mobile-tipo"><SelectValue /></SelectTrigger>
          <SelectContent>{TIPI.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5"><L>Lavoro eseguito</L><Textarea rows={3} value={f.descrizione} onChange={(e) => set("descrizione", e.target.value)} placeholder="Es. Sostituita pompa sentina, riparazione motore" data-testid="input-mobile-descrizione" /></div>
      <div className="space-y-1.5"><L>Materiali (note)</L><Input value={f.materiali} onChange={(e) => set("materiali", e.target.value)} placeholder="Es. pompa 12V, 2 fascette" className="h-12" data-testid="input-mobile-materiali" /></div>

      {articoli.length > 0 && (
        <div className="space-y-1.5"><L>Articoli dal magazzino</L>
          {f.articoli.map((a, i) => {
            const art = articoli.find((x) => x.id === a.articolo_id);
            return (
              <div key={a.articolo_id} className="flex items-center gap-2 text-sm" data-testid={`mobile-art-${i}`}>
                <div className="flex-1 truncate">{art?.codice ? `[${art.codice}] ` : ""}{art?.nome}</div>
                <Input type="number" inputMode="decimal" min="0.5" step="0.5" value={a.quantita} onChange={(e) => set("articoli", f.articoli.map((x, j) => j === i ? { ...x, quantita: e.target.value } : x))} className="w-20 h-10 text-right" />
                <button onClick={() => set("articoli", f.articoli.filter((_, j) => j !== i))}><X className="w-4 h-4 text-destructive" /></button>
              </div>
            );
          })}
          <ArticoloPicker articoli={articoli} exclude={f.articoli.map((a) => a.articolo_id)} onSelect={(a) => addArt(a.id)} showPrezzo={false} placeholder="+ Cerca articolo (codice o nome)…" testId="select-mobile-articolo" />
        </div>
      )}

      <Button onClick={salva} className="w-full h-12 bg-primary hover:bg-primary/90 text-base" data-testid="btn-mobile-salva"><Save className="w-4 h-4 mr-2" /> Salva lavoro</Button>
    </div>
  );
}
