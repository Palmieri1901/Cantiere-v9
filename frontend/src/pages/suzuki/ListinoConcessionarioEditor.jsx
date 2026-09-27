import { useEffect, useMemo, useState } from "react";
import { confirmDialog } from "@/components/ConfirmDialog";
import { api, API } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { FileText, Save, RotateCcw, X, Search } from "lucide-react";
import { fmt } from "./common";

const IT = (n) => new Intl.NumberFormat("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(n) || 0);

export default function ListinoConcessionarioEditor({ open, onClose }) {
  const [modelli, setModelli] = useState([]);
  const [cantiere, setCantiere] = useState(null);
  const [defaultSc1, setDefaultSc1] = useState(10);
  const [defaultSc2, setDefaultSc2] = useState(5);
  const [overrides, setOverrides] = useState({});  // { id: { sc1, sc2 } }
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const ivaPerc = Number(cantiere?.iva_percentuale ?? 22);
  const IVA_M = 1 + ivaPerc / 100;

  useEffect(() => {
    if (!open) return;
    let alive = true;
    setLoading(true);
    Promise.all([
      api.get("/suzuki/modelli"),
      api.get("/suzuki/listino-conc-overrides"),
      api.get("/cantiere"),
    ])
      .then(([rm, ro, rc]) => {
        if (!alive) return;
        setModelli(rm.data || []);
        setDefaultSc1(ro.data.default_sc1 ?? 10);
        setDefaultSc2(ro.data.default_sc2 ?? 5);
        setOverrides(ro.data.overrides || {});
        setCantiere(rc.data);
      })
      .catch(() => toast.error("Errore caricamento dati"))
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [open]);

  const rows = useMemo(() => {
    const rx = q.trim().toLowerCase();
    const filtered = rx
      ? modelli.filter((m) =>
          (m.modello || "").toLowerCase().includes(rx) ||
          (m.codice || "").toLowerCase().includes(rx) ||
          (m.categoria || "").toLowerCase().includes(rx)
        )
      : modelli;
    return filtered.map((m) => {
      const ov = overrides[m.id];
      const offerta = Number(m.prezzo_offerta) || 0;
      const inOfferta = offerta > 0;
      const s1 = inOfferta ? 0 : Number(ov?.sc1 ?? defaultSc1) || 0;
      const s2 = inOfferta ? 0 : Number(ov?.sc2 ?? defaultSc2) || 0;
      const pl = Number(m.prezzo_listino) || 0;
      const pub = inOfferta ? offerta : Number(m.prezzo_pubblico) || 0;
      const s1Mod = Number(m.sconto_perc_1) || 0;
      const s2Mod = Number(m.sconto_perc_2) || 0;
      const nettoConc = Math.max(0, pl * (1 - s1Mod / 100) * (1 - s2Mod / 100) - (inOfferta ? Number(m.contributo_offerta) || 0 : 0));
      const pubEscl = pub ? pub / IVA_M : 0;
      const scListPerc = pubEscl > 0 && pl > 0 ? ((pubEscl - pl) / pubEscl) * 100 : 0;
      const nettoVenditaIncl = pub * (1 - s1 / 100) * (1 - s2 / 100);
      const nettoVenditaEscl = nettoVenditaIncl / IVA_M;
      const guadagno = pl && pub ? nettoVenditaEscl - nettoConc : 0;
      return { m, s1, s2, pl, pub, nettoConc, scListPerc, nettoVenditaIncl, guadagno, isOverride: !!ov && !inOfferta, inOfferta };
    });
  }, [modelli, overrides, defaultSc1, defaultSc2, q, IVA_M]);

  const setOverride = (id, key, value) => {
    setOverrides((prev) => {
      const curr = prev[id] || { sc1: defaultSc1, sc2: defaultSc2 };
      const next = { ...curr, [key]: value === "" ? "" : Number(value) };
      return { ...prev, [id]: next };
    });
  };

  const resetRow = (id) => {
    setOverrides((prev) => {
      const { [id]: _, ...rest } = prev;
      return rest;
    });
  };

  const applyDefaultsToAll = async () => {
    if (!await confirmDialog("Reimpostare tutte le righe ai valori di default?")) return;
    setOverrides({});
    toast.success("Tutte le righe azzerate ai default");
  };

  const buildPayload = () => {
    const clean = {};
    for (const [id, v] of Object.entries(overrides)) {
      const s1 = Number(v?.sc1);
      const s2 = Number(v?.sc2);
      if (Number.isFinite(s1) && Number.isFinite(s2)) {
        // salva solo se diverso dai default (compattezza)
        if (s1 !== Number(defaultSc1) || s2 !== Number(defaultSc2)) {
          clean[id] = { sc1: s1, sc2: s2 };
        }
      }
    }
    return {
      default_sc1: Number(defaultSc1) || 0,
      default_sc2: Number(defaultSc2) || 0,
      overrides: clean,
    };
  };

  const save = async () => {
    setSaving(true);
    try {
      await api.put("/suzuki/listino-conc-overrides", buildPayload());
      toast.success("Sconti salvati per modello");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Errore salvataggio");
    } finally { setSaving(false); }
  };

  const saveAndExport = async () => {
    setSaving(true);
    try {
      await api.put("/suzuki/listino-conc-overrides", buildPayload());
      const params = new URLSearchParams({ sc1: String(defaultSc1), sc2: String(defaultSc2), _t: String(Date.now()) });
      window.open(`${API}/suzuki/listino-concessionario.pdf?${params.toString()}`, "_blank");
      toast.success("PDF aperto in nuova scheda");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Errore salvataggio");
    } finally { setSaving(false); }
  };

  const nNegatives = rows.filter((r) => r.guadagno < 0 && r.pl && r.pub).length;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-[95vw] w-[95vw] h-[92vh] p-0 gap-0 overflow-hidden flex flex-col" data-testid="dialog-listino-editor">
        <DialogHeader className="px-5 py-3 border-b bg-muted/40 shrink-0">
          <DialogTitle className="flex items-center gap-2 text-red-700">
            <FileText className="w-5 h-5" /> Listino concessionario — Editor sconti per modello
          </DialogTitle>
          <DialogDescription className="text-xs">
            Modifica <b>Sc.1</b> e <b>Sc.2</b> per ogni modello direttamente in tabella. Il guadagno si aggiorna in tempo reale;
            i valori negativi sono evidenziati in rosso. Le modifiche vengono salvate e usate nel PDF.
          </DialogDescription>
          <div className="flex items-center gap-3 flex-wrap pt-2">
            <div className="flex items-center gap-2 flex-1 min-w-[260px]">
              <Search className="w-4 h-4 text-muted-foreground shrink-0" />
              <Input placeholder="Filtra per modello, codice, categoria…" value={q} onChange={(e) => setQ(e.target.value)} className="h-8" data-testid="in-editor-search" />
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground">Default:</span>
              <label className="flex items-center gap-1">Sc.1 <Input type="number" step="0.5" min="0" max="100" value={defaultSc1} onChange={(e) => setDefaultSc1(e.target.value)} className="h-7 w-16 text-xs" data-testid="in-editor-default-sc1" />%</label>
              <label className="flex items-center gap-1">Sc.2 <Input type="number" step="0.5" min="0" max="100" value={defaultSc2} onChange={(e) => setDefaultSc2(e.target.value)} className="h-7 w-16 text-xs" data-testid="in-editor-default-sc2" />%</label>
              <Button variant="ghost" size="sm" onClick={applyDefaultsToAll} className="h-7 px-2" data-testid="btn-editor-reset-all"><RotateCcw className="w-3 h-3 mr-1" /> Reset tutti</Button>
            </div>
            <div className="text-xs text-muted-foreground">
              {rows.length} modelli · <span className={nNegatives ? "text-destructive font-semibold" : "text-emerald-700"}>{nNegatives}</span> in perdita
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-auto" data-testid="editor-table-scroll">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Caricamento…</div>
          ) : (
            <table className="w-full text-xs" data-testid="editor-table">
              <thead className="bg-muted sticky top-0 z-10 text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="text-left px-3 py-2">Modello</th>
                  <th className="text-right px-2 py-2 w-12">HP</th>
                  <th className="text-right px-2 py-2 w-28" title="Prezzo di listino concessionario, IVA inclusa">Listino conc. IVA incl.</th>
                  <th className="text-right px-2 py-2 w-24">Pubblico IVA incl.</th>
                  <th className="text-right px-2 py-2 w-16">% Sc. list.</th>
                  <th className="text-center px-2 py-2 w-20">Sc.1 (%)</th>
                  <th className="text-center px-2 py-2 w-20">Sc.2 (%)</th>
                  <th className="text-right px-2 py-2 w-24">Netto conc.</th>
                  <th className="text-right px-2 py-2 w-28">Guadagno</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr><td colSpan={10} className="text-center py-8 text-muted-foreground">Nessun modello trovato.</td></tr>
                ) : rows.map(({ m, s1, s2, pl, pub, nettoConc, scListPerc, guadagno, isOverride, inOfferta }) => {
                  const neg = guadagno < 0 && pl && pub;
                  return (
                    <tr key={m.id} className={`border-t border-border/60 ${neg ? "bg-red-50" : inOfferta ? "bg-orange-50/60" : "hover:bg-muted/40"}`} data-testid={`editor-row-${m.id}`}>
                      <td className="px-3 py-1.5">
                        <div className="font-semibold flex items-center gap-2">
                          {m.modello}
                          {inOfferta && <span className="rounded-full bg-orange-100 text-orange-700 text-[9px] font-bold px-1.5 py-0.5 uppercase" data-testid={`editor-badge-offerta-${m.id}`}>Offerta</span>}
                        </div>
                        <div className="text-[10px] text-muted-foreground">{m.codice || ""}{m.categoria ? ` · ${m.categoria}` : ""}</div>
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono-num">{m.potenza_hp || "—"}</td>
                      <td className="px-2 py-1.5 text-right font-mono-num">{pl ? IT(pl * IVA_M) + " €" : "—"}</td>
                      <td className={`px-2 py-1.5 text-right font-mono-num ${inOfferta ? "text-orange-700 font-bold" : ""}`}>{pub ? IT(pub) + " €" : "—"}</td>
                      <td className="px-2 py-1.5 text-right text-muted-foreground">{scListPerc > 0 ? scListPerc.toFixed(1) + "%" : "—"}</td>
                      <td className="px-1 py-1.5">
                        <Input type="number" step="0.5" min="0" max="100" disabled={inOfferta} title={inOfferta ? "Prezzo imposto: sconto bloccato" : ""} value={inOfferta ? 0 : overrides[m.id]?.sc1 ?? defaultSc1} onChange={(e) => setOverride(m.id, "sc1", e.target.value)} className={`h-7 text-xs text-center font-mono-num ${isOverride ? "border-primary/50 bg-primary/5" : ""} ${inOfferta ? "bg-orange-100 text-orange-700" : ""}`} data-testid={`in-sc1-${m.id}`} />
                      </td>
                      <td className="px-1 py-1.5">
                        <Input type="number" step="0.5" min="0" max="100" disabled={inOfferta} title={inOfferta ? "Prezzo imposto: sconto bloccato" : ""} value={inOfferta ? 0 : overrides[m.id]?.sc2 ?? defaultSc2} onChange={(e) => setOverride(m.id, "sc2", e.target.value)} className={`h-7 text-xs text-center font-mono-num ${isOverride ? "border-primary/50 bg-primary/5" : ""} ${inOfferta ? "bg-orange-100 text-orange-700" : ""}`} data-testid={`in-sc2-${m.id}`} />
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono-num">{nettoConc ? IT(nettoConc) + " €" : "—"}{inOfferta && Number(m.contributo_offerta) > 0 && <div className="text-[10px] text-emerald-700" title="Contributo casa madre già detratto">− contr. {IT(Number(m.contributo_offerta))} €</div>}</td>
                      <td className={`px-2 py-1.5 text-right font-mono-num font-bold ${neg ? "text-red-700" : "text-emerald-700"}`} data-testid={`guadagno-${m.id}`}>
                        {pl && pub ? (guadagno >= 0 ? "+ " : "− ") + IT(Math.abs(guadagno)) + " €" : "—"}
                      </td>
                      <td className="px-1 py-1.5 text-center">
                        {isOverride && (
                          <button type="button" onClick={() => resetRow(m.id)} className="text-muted-foreground hover:text-destructive" title="Ripristina default" data-testid={`btn-reset-${m.id}`}>
                            <X className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <DialogFooter className="px-5 py-3 border-t bg-muted/40 shrink-0 gap-2">
          <div className="flex-1 text-xs text-muted-foreground">
            Righe con <span className="text-primary font-semibold">bordo blu</span> hanno sconti personalizzati diversi dal default. Clicca la <X className="w-3 h-3 inline align-text-bottom" /> per rimuovere l'override.
            Le righe <span className="text-orange-700 font-semibold">OFFERTA</span> hanno prezzo imposto e sconti bloccati a 0%.
          </div>
          <Button variant="outline" onClick={onClose} data-testid="btn-editor-close">Chiudi</Button>
          <Button variant="outline" onClick={save} disabled={saving} data-testid="btn-editor-save">
            <Save className="w-4 h-4 mr-1.5" /> {saving ? "Salvataggio…" : "Salva"}
          </Button>
          <Button onClick={saveAndExport} disabled={saving || loading} className="bg-primary" data-testid="btn-editor-export">
            <FileText className="w-4 h-4 mr-1.5" /> Salva ed esporta PDF
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
