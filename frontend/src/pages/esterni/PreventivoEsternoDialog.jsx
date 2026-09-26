import { useEffect, useMemo, useState } from "react";
import { api, fmtEuro } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Trash2, Package, Clock, Tag, Search } from "lucide-react";

const L = ({ children }) => <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{children}</Label>;
const empty = () => ({ data: new Date().toISOString().slice(0, 10), oggetto: "", righe: [], sconto_pct: 0, iva_pct: 22, note: "", validita_giorni: 30 });

export default function PreventivoEsternoDialog({ esterno, preventivo, open, onClose, onSaved }) {
  const [f, setF] = useState(empty());
  const [articoli, setArticoli] = useState([]);
  const [tariffa, setTariffa] = useState(0);
  const [q, setQ] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setF(preventivo ? { ...empty(), ...preventivo } : empty());
    setQ("");
    api.get("/magazzino/articoli").then((r) => setArticoli(r.data)).catch(() => {});
    api.get("/tariffe").then((r) => setTariffa(Number(r.data.costo_orario_manodopera) || 0)).catch(() => {});
  }, [open, preventivo]);

  const set = (k, v) => setF((s) => ({ ...s, [k]: v }));
  const setRiga = (i, k, v) => set("righe", f.righe.map((r, j) => j === i ? { ...r, [k]: v } : r));
  const addRiga = (r) => set("righe", [...f.righe, r]);

  const trovati = useMemo(() => {
    const s = q.trim().toLowerCase();
    return s.length < 2 ? [] : articoli.filter((a) => `${a.codice} ${a.nome}`.toLowerCase().includes(s)).slice(0, 8);
  }, [q, articoli]);

  const imponibile = f.righe.reduce((s, r) => s + (Number(r.quantita) || 0) * (Number(r.prezzo_unitario) || 0), 0);
  const sconto = imponibile * (Number(f.sconto_pct) || 0) / 100;
  const netto = imponibile - sconto;
  const iva = netto * (Number(f.iva_pct) || 0) / 100;

  const salva = async () => {
    if (f.righe.length === 0) return toast.error("Aggiungi almeno una riga");
    setSaving(true);
    try {
      const body = { ...f, righe: f.righe.map((r) => ({ ...r, quantita: Number(r.quantita) || 0, prezzo_unitario: Number(r.prezzo_unitario) || 0 })), sconto_pct: Number(f.sconto_pct) || 0, iva_pct: Number(f.iva_pct) || 0, validita_giorni: Number(f.validita_giorni) || 30 };
      const r = preventivo ? await api.put(`/esterni/preventivi/${preventivo.id}`, body) : await api.post(`/esterni/${esterno.id}/preventivi`, body);
      toast.success(preventivo ? "Preventivo aggiornato" : `Preventivo n. ${r.data.numero}/${r.data.anno} creato`);
      onSaved(r.data); onClose();
    } catch (e) { toast.error(e.response?.data?.detail || "Errore salvataggio"); }
    finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl max-h-[92vh] overflow-y-auto" data-testid="prev-esterno-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-xl">{preventivo ? `Preventivo n. ${preventivo.numero}/${preventivo.anno}` : "Nuovo preventivo"} · {esterno?.nome}</DialogTitle>
          <DialogDescription>Manodopera a ore, ricambi dal magazzino e voci libere. Il PDF si genera dopo il salvataggio.</DialogDescription>
        </DialogHeader>

        <div className="grid sm:grid-cols-3 gap-3">
          <div className="space-y-1.5"><L>Data</L><Input type="date" value={f.data} onChange={(e) => set("data", e.target.value)} data-testid="prev-data" /></div>
          <div className="space-y-1.5 sm:col-span-2"><L>Oggetto</L><Input value={f.oggetto} onChange={(e) => set("oggetto", e.target.value)} placeholder="Es. Revisione motore e sostituzione pompa" data-testid="prev-oggetto" /></div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <L>Righe</L>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => addRiga({ tipo: "manodopera", descrizione: "Manodopera", quantita: 1, prezzo_unitario: tariffa })} data-testid="btn-riga-manodopera"><Clock className="w-3.5 h-3.5 mr-1" /> Manodopera {tariffa ? `(${tariffa} €/h)` : ""}</Button>
              <Button size="sm" variant="outline" onClick={() => addRiga({ tipo: "voce", descrizione: "", quantita: 1, prezzo_unitario: 0 })} data-testid="btn-riga-voce"><Tag className="w-3.5 h-3.5 mr-1" /> Voce libera</Button>
            </div>
          </div>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca ricambio in magazzino (codice o nome)…" className="pl-9" data-testid="prev-cerca-articolo" />
            {trovati.length > 0 && (
              <div className="absolute z-30 left-0 right-0 mt-1 bg-card border rounded-md shadow-lg divide-y max-h-64 overflow-y-auto">
                {trovati.map((a) => (
                  <button key={a.id} onClick={() => { addRiga({ tipo: "articolo", articolo_id: a.id, codice: a.codice, descrizione: a.nome, quantita: 1, prezzo_unitario: a.prezzo_listino || 0 }); setQ(""); }} className="w-full text-left px-3 py-2 hover:bg-muted text-sm flex justify-between gap-3" data-testid={`prev-art-${a.id}`}>
                    <span className="truncate"><Package className="w-3.5 h-3.5 inline mr-1.5 text-primary" />{a.codice ? `[${a.codice}] ` : ""}{a.nome}</span>
                    <span className="font-mono-num text-xs text-muted-foreground shrink-0">{fmtEuro(a.prezzo_listino || 0)} · giac. {a.quantita}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {f.righe.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-6 border border-dashed rounded-md">Nessuna riga. Aggiungi manodopera, un ricambio dal magazzino o una voce libera.</div>
          ) : (
            <div className="border rounded-md divide-y" data-testid="prev-righe">
              {f.righe.map((r, i) => (
                <div key={i} className="p-2 grid grid-cols-12 gap-2 items-center text-sm" data-testid={`prev-riga-${i}`}>
                  <div className="col-span-1 text-muted-foreground">{r.tipo === "articolo" ? <Package className="w-4 h-4" /> : r.tipo === "manodopera" ? <Clock className="w-4 h-4" /> : <Tag className="w-4 h-4" />}</div>
                  <Input className="col-span-5 h-9" value={r.descrizione} onChange={(e) => setRiga(i, "descrizione", e.target.value)} placeholder="Descrizione" />
                  <Input type="number" step="0.5" min="0" className="col-span-2 h-9 font-mono-num text-right" value={r.quantita} onChange={(e) => setRiga(i, "quantita", e.target.value)} title={r.tipo === "manodopera" ? "Ore" : "Quantità"} />
                  <Input type="number" step="0.01" min="0" className="col-span-2 h-9 font-mono-num text-right" value={r.prezzo_unitario} onChange={(e) => setRiga(i, "prezzo_unitario", e.target.value)} />
                  <div className="col-span-1 font-mono-num text-right text-xs">{fmtEuro((Number(r.quantita) || 0) * (Number(r.prezzo_unitario) || 0))}</div>
                  <button className="col-span-1 justify-self-end" onClick={() => set("righe", f.righe.filter((_, j) => j !== i))} data-testid={`prev-del-riga-${i}`}><Trash2 className="w-4 h-4 text-destructive" /></button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="grid sm:grid-cols-4 gap-3 items-end">
          <div className="space-y-1.5"><L>Sconto %</L><Input type="number" step="0.5" min="0" value={f.sconto_pct} onChange={(e) => set("sconto_pct", e.target.value)} className="font-mono-num" data-testid="prev-sconto" /></div>
          <div className="space-y-1.5"><L>IVA %</L><Input type="number" step="1" min="0" value={f.iva_pct} onChange={(e) => set("iva_pct", e.target.value)} className="font-mono-num" data-testid="prev-iva" /></div>
          <div className="space-y-1.5"><L>Validità giorni</L><Input type="number" min="1" value={f.validita_giorni} onChange={(e) => set("validita_giorni", e.target.value)} className="font-mono-num" /></div>
          <div className="text-right text-sm space-y-0.5">
            <div className="text-muted-foreground">Imponibile {fmtEuro(imponibile)}{sconto > 0 ? ` · sconto −${fmtEuro(sconto)}` : ""} · IVA {fmtEuro(iva)}</div>
            <div className="font-display text-2xl font-semibold text-primary" data-testid="prev-totale">{fmtEuro(netto + iva)}</div>
          </div>
        </div>
        <div className="space-y-1.5"><L>Note</L><Textarea rows={2} value={f.note} onChange={(e) => set("note", e.target.value)} data-testid="prev-note" /></div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Annulla</Button>
          <Button onClick={salva} disabled={saving} className="bg-primary hover:bg-primary/90" data-testid="btn-prev-salva"><Plus className="w-4 h-4 mr-1" /> {preventivo ? "Salva modifiche" : "Crea preventivo"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
