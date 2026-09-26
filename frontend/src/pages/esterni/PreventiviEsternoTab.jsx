import { useEffect, useState } from "react";
import { api, fmtEuro } from "@/lib/api";
import { confirmDialog } from "@/components/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, FileText, Pencil, Trash2, CheckCircle2 } from "lucide-react";
import PreventivoEsternoDialog from "@/pages/esterni/PreventivoEsternoDialog";

const STATO = { bozza: "text-muted-foreground", inviato: "text-sky-700 border-sky-300", accettato: "text-emerald-700 border-emerald-300" };

export default function PreventiviEsternoTab({ esterno, anteprima, onLavoroCreato }) {
  const [list, setList] = useState([]);
  const [edit, setEdit] = useState(null); // null | {} (nuovo) | preventivo
  const load = () => api.get(`/esterni/${esterno.id}/preventivi`).then((r) => setList(r.data));
  useEffect(() => { load(); }, [esterno.id]);

  const del = async (p) => {
    if (!await confirmDialog(`Eliminare il preventivo n. ${p.numero}/${p.anno}?`)) return;
    await api.delete(`/esterni/preventivi/${p.id}`); load();
  };
  const converti = async (p) => {
    const nArt = p.righe.filter((r) => r.tipo === "articolo").length;
    if (!await confirmDialog(`Accettare il preventivo n. ${p.numero}/${p.anno} e creare il lavoro?${nArt ? ` Verranno scaricati ${nArt} ricambi dal magazzino.` : ""}`, { title: "Converti in lavoro", okLabel: "Crea lavoro", danger: false })) return;
    try { await api.post(`/esterni/preventivi/${p.id}/converti`); toast.success("Lavoro creato dal preventivo"); load(); onLavoroCreato?.(); }
    catch (e) { toast.error(e.response?.data?.detail || "Errore conversione"); }
  };

  return (
    <div className="space-y-3" data-testid="prev-esterno-tab">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">{list.length} preventivi</div>
        <Button size="sm" onClick={() => setEdit({})} className="bg-primary hover:bg-primary/90" data-testid="btn-nuovo-prev-esterno"><Plus className="w-4 h-4 mr-1" /> Nuovo preventivo</Button>
      </div>
      {list.length === 0 ? (
        <div className="text-sm text-muted-foreground py-8 text-center border border-dashed rounded-md">Nessun preventivo per questo cliente.</div>
      ) : (
        <div className="border rounded-md divide-y">
          {list.map((p) => (
            <div key={p.id} className="p-3 flex items-center gap-3 hover:bg-muted/40" data-testid={`prev-row-${p.id}`}>
              <div className="w-20 shrink-0"><div className="font-mono-num text-sm font-semibold">n. {p.numero}/{p.anno}</div><div className="text-[11px] text-muted-foreground">{p.data}</div></div>
              <div className="flex-1 min-w-0">
                <div className="text-sm truncate">{p.oggetto || p.righe.map((r) => r.descrizione).filter(Boolean).slice(0, 3).join(", ") || "—"}</div>
                <div className="text-[11px] text-muted-foreground">{p.righe.length} righe · {p.righe.filter((r) => r.tipo === "articolo").length} ricambi{p.lavoro_id ? " · lavoro creato" : ""}</div>
              </div>
              <Badge variant="outline" className={`text-[10px] ${STATO[p.stato] || ""}`}>{p.stato}</Badge>
              <div className="font-mono-num text-sm font-semibold w-24 text-right">{fmtEuro(p.totale)}</div>
              <Button size="sm" variant="outline" onClick={() => anteprima(`/esterni/preventivi/${p.id}/pdf`, `Preventivo_${p.numero}_${p.anno}.pdf`)} data-testid={`btn-prev-pdf-${p.id}`}><FileText className="w-3.5 h-3.5 mr-1" /> PDF</Button>
              {!p.lavoro_id && <Button size="sm" variant="outline" onClick={() => converti(p)} title="Accetta e crea lavoro" data-testid={`btn-prev-converti-${p.id}`}><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Crea lavoro</Button>}
              {!p.lavoro_id && <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setEdit(p)} data-testid={`btn-prev-edit-${p.id}`}><Pencil className="w-3.5 h-3.5" /></Button>}
              <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => del(p)} data-testid={`btn-prev-del-${p.id}`}><Trash2 className="w-3.5 h-3.5 text-destructive" /></Button>
            </div>
          ))}
        </div>
      )}
      <PreventivoEsternoDialog esterno={esterno} preventivo={edit && edit.id ? edit : null} open={edit !== null} onClose={() => setEdit(null)} onSaved={load} />
    </div>
  );
}
