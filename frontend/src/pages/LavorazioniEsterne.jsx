import { useEffect, useState } from "react";
import { api, fmtEuro } from "@/lib/api";
import { confirmDialog } from "@/components/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Trash2, Pencil, HardHat, Search, ChevronRight, FileText } from "lucide-react";
import LavoriSection from "@/pages/LavoriSection";
import PreventiviEsternoTab from "@/pages/esterni/PreventiviEsternoTab";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PdfPreviewOverlay } from "@/components/PdfPreviewOverlay";
import { openBlob } from "@/pages/ddt/common";

export default function LavorazioniEsterne() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [nome, setNome] = useState("");
  const [open, setOpen] = useState(null);
  const [edit, setEdit] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewName, setPreviewName] = useState("conto.pdf");
  const [contoAnno, setContoAnno] = useState("tutti");
  const [lavoriKey, setLavoriKey] = useState(0);

  const anteprimaConto = async (e) => {
    try {
      const anno = contoAnno === "tutti" ? "" : `?anno=${contoAnno}`;
      setPreviewName(`Conto_${e.nome.replace(/\s+/g, "_")}${contoAnno === "tutti" ? "" : `_${contoAnno}`}.pdf`);
      await openBlob(api, "get", `/esterni/${e.id}/conto.pdf${anno}`, null, setPreviewUrl, setPreviewOpen);
    } catch (err) { toast.error(err.response?.data?.detail || "Errore PDF"); }
  };

  const load = () => api.get("/esterni").then((r) => setList(r.data));
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!nome.trim()) return toast.error("Inserisci il nominativo");
    const r = await api.post("/esterni", { nome });
    setNome(""); await load(); setOpen(r.data);
  };
  const salvaEdit = async () => {
    await api.put(`/esterni/${edit.id}`, edit); setEdit(null); load(); toast.success("Salvato");
  };
  const del = async (e) => {
    const msg = e.n > 0
      ? `Eliminare "${e.nome}" e i suoi ${e.n} ${e.n === 1 ? "lavoro" : "lavori"} (${fmtEuro(e.totale)})? Gli articoli scaricati tornano in magazzino. Operazione irreversibile.`
      : `Eliminare "${e.nome}"?`;
    if (!await confirmDialog(msg, { title: "Elimina cliente esterno", okLabel: "Elimina" })) return;
    try { await api.delete(`/esterni/${e.id}`); load(); toast.success("Cliente esterno eliminato"); }
    catch (err) { toast.error(err.response?.data?.detail || "Errore"); }
  };

  const visibili = list.filter((e) => e.nome.toLowerCase().includes(q.toLowerCase()));
  const totale = visibili.reduce((s, e) => s + (e.totale || 0), 0);

  return (
    <div className="p-6 md:p-10 max-w-6xl" data-testid="esterni-page">
      <div className="label-mini flex items-center gap-1.5 mb-2"><HardHat className="w-3.5 h-3.5" /> Lavorazioni esterne</div>
      <h1 className="font-display text-4xl sm:text-5xl font-semibold mb-2">Clienti esterni</h1>
      <p className="text-muted-foreground text-base md:text-lg mb-8 max-w-2xl">Lavori per clienti non in rimessaggio: basta il nominativo. Qui trovi anche i clienti creati approvando i lavori dei dipendenti.</p>

      <Card className="p-5 mb-6">
        <div className="label-mini mb-2">Nuovo cliente esterno</div>
        <div className="flex gap-2 max-w-md">
          <Input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Nominativo (es. Rossi Mario)" onKeyDown={(e) => e.key === "Enter" && add()} data-testid="input-esterno-nome" />
          <Button onClick={add} className="bg-primary hover:bg-primary/90" data-testid="btn-add-esterno"><Plus className="w-4 h-4 mr-1" /> Aggiungi</Button>
        </div>
      </Card>

      <div className="flex items-center gap-3 mb-3">
        <div className="relative flex-1 max-w-sm"><Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" /><Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca nominativo…" className="pl-9" data-testid="input-cerca-esterno" /></div>
        <div className="text-sm text-muted-foreground">{visibili.length} clienti · totale lavori {fmtEuro(totale)}</div>
        <div className="flex items-center gap-2 ml-auto text-xs text-muted-foreground">
          Conto PDF per
          <select className="h-9 rounded-md border border-input bg-background px-2 text-sm font-mono-num" value={contoAnno} onChange={(ev) => setContoAnno(ev.target.value)} data-testid="select-conto-anno">
            <option value="tutti">tutti gli anni</option>
            {Array.from({ length: 4 }, (_, i) => new Date().getFullYear() - i).map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>

      {visibili.length === 0 ? (
        <div className="text-sm text-muted-foreground py-10 text-center border border-dashed rounded-md">Nessun cliente esterno.</div>
      ) : (
        <div className="border border-border rounded-md divide-y divide-border">
          {visibili.map((e) => (
            <div key={e.id} className="p-3 flex items-center gap-3 hover:bg-muted/40 cursor-pointer" onClick={() => setOpen(e)} data-testid={`esterno-row-${e.id}`}>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">{e.nome}{e.telefono && <span className="text-muted-foreground font-normal"> · {e.telefono}</span>}</div>
                <div className="text-xs text-muted-foreground">{e.n} {e.n === 1 ? "lavoro" : "lavori"} · {e.ore} h{e.ultimo ? ` · ultimo ${e.ultimo}` : ""}{e.note ? ` · ${e.note}` : ""}</div>
              </div>
              <div className="font-mono-num text-sm font-semibold">{fmtEuro(e.totale)}</div>
              <Button size="sm" variant="outline" onClick={(ev) => { ev.stopPropagation(); setOpen(e); }} data-testid={`btn-preventivo-${e.id}`}><FileText className="w-3.5 h-3.5 mr-1" /> Preventivo</Button>
              <Button size="sm" variant="outline" onClick={(ev) => { ev.stopPropagation(); anteprimaConto(e); }} data-testid={`btn-conto-${e.id}`}><FileText className="w-3.5 h-3.5 mr-1" /> Conto PDF</Button>
              <Button size="icon" variant="ghost" className="h-8 w-8" onClick={(ev) => { ev.stopPropagation(); setEdit({ ...e }); }} data-testid={`btn-edit-esterno-${e.id}`}><Pencil className="w-3.5 h-3.5" /></Button>
              <Button size="icon" variant="ghost" className="h-8 w-8" onClick={(ev) => { ev.stopPropagation(); del(e); }} data-testid={`btn-del-esterno-${e.id}`}><Trash2 className="w-3.5 h-3.5 text-destructive" /></Button>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            </div>
          ))}
        </div>
      )}

      <Dialog open={!!open} onOpenChange={(o) => { if (!o) { setOpen(null); load(); } }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="esterno-dialog">
          <DialogHeader>
            <DialogTitle className="font-display text-2xl">{open?.nome}</DialogTitle>
            <DialogDescription>Scheda lavori del cliente esterno.</DialogDescription>
          </DialogHeader>
          {open && (
            <Tabs defaultValue="lavori">
              <div className="flex items-center justify-between flex-wrap gap-2 -mt-2 mb-2">
                <TabsList>
                  <TabsTrigger value="lavori" data-testid="tab-esterno-lavori">Lavori eseguiti</TabsTrigger>
                  <TabsTrigger value="preventivi" data-testid="tab-esterno-preventivi">Preventivi</TabsTrigger>
                </TabsList>
                <Button size="sm" variant="outline" onClick={() => anteprimaConto(open)} data-testid="btn-conto-dialog"><FileText className="w-3.5 h-3.5 mr-1" /> Anteprima conto PDF</Button>
              </div>
              <TabsContent value="lavori"><LavoriSection key={lavoriKey} clienteId={open.id} /></TabsContent>
              <TabsContent value="preventivi"><PreventiviEsternoTab esterno={open} anteprima={(url, name) => { setPreviewName(name); openBlob(api, "get", url, null, setPreviewUrl, setPreviewOpen).catch((e) => toast.error(e.response?.data?.detail || "Errore PDF")); }} onLavoroCreato={() => setLavoriKey((k) => k + 1)} /></TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>

      <PdfPreviewOverlay open={previewOpen} onClose={() => setPreviewOpen(false)} url={previewUrl} filename={previewName} />

      <Dialog open={!!edit} onOpenChange={(o) => !o && setEdit(null)}>
        <DialogContent className="max-w-md" data-testid="esterno-edit-dialog">
          <DialogHeader><DialogTitle>Modifica cliente esterno</DialogTitle></DialogHeader>
          {edit && (
            <div className="space-y-3">
              <Input value={edit.nome} onChange={(e) => setEdit({ ...edit, nome: e.target.value })} placeholder="Nominativo" data-testid="input-edit-nome" />
              <Input value={edit.telefono || ""} onChange={(e) => setEdit({ ...edit, telefono: e.target.value })} placeholder="Telefono" data-testid="input-edit-telefono" />
              <Input value={edit.note || ""} onChange={(e) => setEdit({ ...edit, note: e.target.value })} placeholder="Note (barca, contatto…)" data-testid="input-edit-note" />
              <Button onClick={salvaEdit} className="w-full bg-primary hover:bg-primary/90" data-testid="btn-salva-esterno">Salva</Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
