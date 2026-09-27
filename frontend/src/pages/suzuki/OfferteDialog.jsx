import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { Tag, Save, Search } from "lucide-react";
import { fmt } from "./common";

export default function OfferteDialog({ open, onClose, onSaved }) {
  const [modelli, setModelli] = useState([]);
  const [offerte, setOfferte] = useState({}); // { id: prezzo }
  const [contributi, setContributi] = useState({}); // { id: contributo casa madre € }
  const [q, setQ] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    api.get("/suzuki/modelli").then((r) => {
      setModelli(r.data || []);
      const o = {}; const c = {};
      for (const m of r.data || []) if (Number(m.prezzo_offerta) > 0) { o[m.id] = m.prezzo_offerta; if (Number(m.contributo_offerta) > 0) c[m.id] = m.contributo_offerta; }
      setOfferte(o); setContributi(c);
    }).catch(() => toast.error("Errore caricamento modelli"));
  }, [open]);

  const rows = useMemo(() => {
    const rx = q.trim().toLowerCase();
    return rx ? modelli.filter((m) => (m.modello || "").toLowerCase().includes(rx) || (m.codice || "").toLowerCase().includes(rx)) : modelli;
  }, [modelli, q]);

  const toggle = (m, on) => setOfferte((prev) => {
    if (!on) { const { [m.id]: _, ...rest } = prev; return rest; }
    return { ...prev, [m.id]: prev[m.id] ?? m.prezzo_pubblico ?? "" };
  });

  const save = async () => {
    const missing = Object.entries(offerte).filter(([, p]) => !(Number(p) > 0));
    if (missing.length) { toast.error("Inserisci il prezzo imposto per tutti i motori selezionati"); return; }
    setSaving(true);
    try {
      const r = await api.put("/suzuki/offerte", { offerte, contributi });
      toast.success(`${r.data.count} motori in offerta salvati`);
      onSaved?.();
      onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Errore salvataggio");
    } finally { setSaving(false); }
  };

  const nSel = Object.keys(offerte).length;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl h-[85vh] p-0 gap-0 overflow-hidden flex flex-col" data-testid="dialog-offerte">
        <DialogHeader className="px-5 py-3 border-b bg-orange-50 shrink-0">
          <DialogTitle className="flex items-center gap-2 text-orange-700"><Tag className="w-5 h-5" /> Motori in offerta casa madre</DialogTitle>
          <DialogDescription className="text-xs">
            Seleziona i modelli in promozione e inserisci il <b>prezzo imposto</b> (IVA incl.). Nel listino concessionario gli sconti
            saranno bloccati a 0%; nel listino pubblico e nei preventivi verrà usato il prezzo imposto.
          </DialogDescription>
          <div className="flex items-center gap-2 pt-2">
            <Search className="w-4 h-4 text-muted-foreground shrink-0" />
            <Input placeholder="Filtra per modello o codice…" value={q} onChange={(e) => setQ(e.target.value)} className="h-8" data-testid="in-offerte-search" />
            <span className="text-xs text-muted-foreground whitespace-nowrap"><b className="text-orange-700">{nSel}</b> in offerta</span>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-auto">
          <table className="w-full text-xs" data-testid="offerte-table">
            <thead className="bg-muted sticky top-0 z-10 text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="w-10 px-3 py-2"></th>
                <th className="text-left px-2 py-2">Modello</th>
                <th className="text-right px-2 py-2 w-14">HP</th>
                <th className="text-right px-2 py-2 w-28">Pubblico IVA incl.</th>
                <th className="text-right px-2 py-2 w-40">Prezzo imposto € (IVA incl.)</th>
                <th className="text-right px-2 py-2 w-36" title="Contributo della casa madre al concessionario (IVA escl.): riduce il netto concessionario">Contributo casa madre €</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((m) => {
                const on = m.id in offerte;
                return (
                  <tr key={m.id} className={`border-t border-border/60 ${on ? "bg-orange-50" : "hover:bg-muted/40"}`} data-testid={`offerta-row-${m.id}`}>
                    <td className="px-3 py-1.5 text-center">
                      <Checkbox checked={on} onCheckedChange={(v) => toggle(m, !!v)} data-testid={`chk-offerta-${m.id}`} />
                    </td>
                    <td className="px-2 py-1.5">
                      <div className="font-semibold">{m.modello}</div>
                      <div className="text-[10px] text-muted-foreground">{m.codice || ""}{m.categoria ? ` · ${m.categoria}` : ""}</div>
                    </td>
                    <td className="px-2 py-1.5 text-right font-mono-num">{m.potenza_hp || "—"}</td>
                    <td className="px-2 py-1.5 text-right font-mono-num">{fmt(m.prezzo_pubblico)}</td>
                    <td className="px-2 py-1.5">
                      <Input type="number" step="1" min="0" disabled={!on} value={on ? offerte[m.id] : ""} placeholder={on ? "Prezzo imposto" : "—"}
                        onChange={(e) => setOfferte((p) => ({ ...p, [m.id]: e.target.value }))}
                        className="h-7 text-xs text-right font-mono-num" data-testid={`in-offerta-${m.id}`} />
                    </td>
                    <td className="px-2 py-1.5">
                      <Input type="number" step="1" min="0" disabled={!on} value={on ? (contributi[m.id] ?? "") : ""} placeholder={on ? "Contributo €" : "—"}
                        onChange={(e) => setContributi((p) => ({ ...p, [m.id]: e.target.value }))}
                        className="h-7 text-xs text-right font-mono-num" data-testid={`in-contributo-${m.id}`} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <DialogFooter className="px-5 py-3 border-t bg-muted/40 shrink-0 gap-2">
          <Button variant="outline" onClick={onClose} data-testid="btn-offerte-close">Annulla</Button>
          <Button onClick={save} disabled={saving} className="bg-orange-600 hover:bg-orange-700" data-testid="btn-offerte-save">
            <Save className="w-4 h-4 mr-1.5" /> {saving ? "Salvataggio…" : "Salva offerte"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
