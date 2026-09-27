import React, { useEffect, useMemo, useState } from "react";
import { api, API, fmtEuro } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import {
  Plus, Search, Trash2, Pencil, FileDown, FileSpreadsheet,
  Camera, ScanLine, AlertTriangle, ArrowDownCircle, ArrowUpCircle,
  Filter, ShoppingCart, Percent,
} from "lucide-react";
import { EMPTY_ART } from "./common";
import ArticoloForm from "./ArticoloForm";
import ScanArticoloDialog from "./ScanArticoloDialog";
import ScanDDTDialog from "./ScanDDTDialog";
import RicarichiCategoriaDialog from "./RicarichiCategoriaDialog";
import ComponiOrdineDialog from "./ComponiOrdineDialog";

export default function ArticoliTab() {
  const [invDateOpen, setInvDateOpen] = useState(false);
  const [invDate, setInvDate] = useState(new Date().toISOString().slice(0, 10));
  const [articoli, setArticoli] = useState([]);
  const [fornitori, setFornitori] = useState([]);
  const [categorie, setCategorie] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [fFornitore, setFFornitore] = useState("all");
  const [fCategoria, setFCategoria] = useState("all");
  const [soloSottoScorta, setSoloSottoScorta] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [scanOpen, setScanOpen] = useState(false);
  const [ddtOpen, setDdtOpen] = useState(false);
  const [exportForn, setExportForn] = useState("all");
  const [exportCat, setExportCat] = useState("all");
  const [exportOpen, setExportOpen] = useState(false);
  const [ricarichiOpen, setRicarichiOpen] = useState(false);
  const [componiOpen, setComponiOpen] = useState(false);
  const [scaricoInput, setScaricoInput] = useState({});
  const [scaricoLoading, setScaricoLoading] = useState({});
  const [raggruppa, setRaggruppa] = useState(false);
  const [gruppoAperto, setGruppoAperto] = useState({});

  const load = async () => {
    setLoading(true);
    try {
      const [aRes, fRes, cRes] = await Promise.all([
        api.get("/magazzino/articoli"),
        api.get("/magazzino/fornitori"),
        api.get("/magazzino/articoli/categorie"),
      ]);
      setArticoli(aRes.data);
      setFornitori(fRes.data);
      setCategorie(cRes.data);
    } catch {
      toast.error("Errore caricamento magazzino");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    return articoli.filter((a) => {
      if (fFornitore !== "all" && a.fornitore_id !== fFornitore) return false;
      if (fCategoria !== "all" && a.categoria !== fCategoria) return false;
      if (soloSottoScorta && a.quantita > a.scorta_minima) return false;
      if (q) {
        const s = q.toLowerCase();
        if (![a.codice, a.nome, a.descrizione, a.categoria].filter(Boolean).some((v) => v.toLowerCase().includes(s))) return false;
      }
      return true;
    });
  }, [articoli, q, fFornitore, fCategoria, soloSottoScorta]);

  const fornMap = useMemo(() => Object.fromEntries(fornitori.map((f) => [f.id, f.nome])), [fornitori]);

  const gruppi = useMemo(() => {
    if (!raggruppa) return null;
    const map = new Map();
    for (const a of filtered) {
      const cat = (a.categoria || "").trim() || "Senza categoria";
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat).push(a);
    }
    return Array.from(map.entries())
      .sort(([a], [b]) => {
        if (a === "Senza categoria") return 1;
        if (b === "Senza categoria") return -1;
        return a.localeCompare(b, "it");
      })
      .map(([categoria, items]) => {
        const nArt = items.length;
        const valore = items.reduce((s, x) => s + Number(x.quantita || 0) * Number(x.prezzo_acquisto || 0), 0);
        const ricariciCat = items
          .map((x) => {
            const pa = Number(x.prezzo_acquisto || 0);
            const pv = Number(x.prezzo_listino || 0);
            return pa > 0 && pv > 0 ? ((pv - pa) / pa) * 100 : null;
          })
          .filter((v) => v !== null);
        const ricMedio = ricariciCat.length ? ricariciCat.reduce((s, v) => s + v, 0) / ricariciCat.length : null;
        const qtaTot = items.reduce((s, x) => s + Number(x.quantita || 0), 0);
        return { categoria, items, nArt, valore, ricMedio, qtaTot };
      });
  }, [filtered, raggruppa]);

  const ricariciValidi = articoli
    .map((a) => {
      const pa = Number(a.prezzo_acquisto || 0);
      const pv = Number(a.prezzo_listino || 0);
      return pa > 0 && pv > 0 ? ((pv - pa) / pa) * 100 : null;
    })
    .filter((v) => v !== null);
  const ricaricoMedio = ricariciValidi.length
    ? ricariciValidi.reduce((s, v) => s + v, 0) / ricariciValidi.length
    : 0;
  const fornitoriAttivi = new Set(articoli.map((a) => a.fornitore_id).filter(Boolean)).size;

  const remove = async () => {
    if (!confirmDelete) return;
    try {
      await api.delete(`/magazzino/articoli/${confirmDelete.id}`);
      toast.success("Articolo eliminato");
      setConfirmDelete(null);
      load();
    } catch {
      toast.error("Errore eliminazione");
    }
  };

  const buildListinoUrl = () => {
    const p = new URLSearchParams();
    if (exportForn !== "all") p.set("fornitore_id", exportForn);
    if (exportCat !== "all") p.set("categoria", exportCat);
    const qs = p.toString();
    return `${API}/magazzino/listino.pdf${qs ? `?${qs}` : ""}`;
  };

  const doMovimento = async (art, tipo) => {
    const raw = (scaricoInput[art.id] || "").toString().replace(",", ".").trim();
    const qt = parseFloat(raw);
    if (!qt || qt <= 0) { toast.error("Inserisci una quantità positiva"); return; }
    const disponibile = Number(art.quantita || 0);
    setScaricoLoading((s) => ({ ...s, [art.id]: true }));
    try {
      await api.post("/magazzino/movimenti", {
        articolo_id: art.id,
        tipo,
        quantita: qt,
        motivo: tipo === "carico" ? "Carico rapido" : "Scarico rapido",
      });
      const nuovaQta = tipo === "carico" ? disponibile + qt : disponibile - qt;
      setArticoli((prev) => prev.map((x) => x.id === art.id ? { ...x, quantita: nuovaQta } : x));
      setScaricoInput((s) => ({ ...s, [art.id]: "" }));
      toast[nuovaQta < 0 ? "warning" : "success"](`${tipo === "carico" ? "Caricato" : "Scaricato"} ${qt} ${art.unita_misura || "pz"} — nuova giacenza ${nuovaQta}${nuovaQta < 0 ? " (NEGATIVA: da riordinare)" : ""}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || `Errore ${tipo}`);
    } finally {
      setScaricoLoading((s) => ({ ...s, [art.id]: false }));
    }
  };
  const doScarico = (art) => doMovimento(art, "scarico");
  const doCarico = (art) => doMovimento(art, "carico");

  const renderRow = (a) => {
    const pa = Number(a.prezzo_acquisto || 0);
    const pv = Number(a.prezzo_listino || 0);
    const rk = pa > 0 && pv > 0 ? ((pv - pa) / pa) * 100 : null;
    return (
      <TableRow key={a.id} data-testid={`row-articolo-${a.id}`}>
        <TableCell className="font-mono text-xs">{a.codice || "—"}</TableCell>
        <TableCell className="font-medium">
          <div className="flex items-center gap-2">
            {a.immagine_base64 && <img src={a.immagine_base64} alt="" className="w-8 h-8 rounded object-cover" />}
            <div>
              <div>{a.nome}</div>
            </div>
          </div>
        </TableCell>
        <TableCell>{a.categoria && <Badge variant="secondary">{a.categoria}</Badge>}</TableCell>
        <TableCell className="text-sm text-muted-foreground">{fornMap[a.fornitore_id] || "—"}</TableCell>
        <TableCell className="text-right font-mono-num text-muted-foreground">{fmtEuro(pa)}</TableCell>
        <TableCell className="text-right font-mono-num font-semibold">{fmtEuro(pv)}</TableCell>
        <TableCell className="text-right font-mono-num text-primary" data-testid={`cell-pv-iva-${a.id}`}>{fmtEuro(pv * 1.22)}</TableCell>
        <TableCell className="text-right font-mono-num text-xs">
          {rk !== null ? (
            <span className={rk < 0 ? "text-destructive" : rk >= 20 ? "text-primary" : "text-muted-foreground"}>
              {rk >= 0 ? "+" : ""}{rk.toFixed(0)}%
            </span>
          ) : <span className="text-muted-foreground">—</span>}
        </TableCell>
        <TableCell className="text-right font-mono-num text-sm" data-testid={`cell-giacenza-${a.id}`}>
          <span className={Number(a.quantita) < 0 ? "text-destructive font-bold bg-destructive/10 px-1.5 rounded" : Number(a.quantita) === 0 ? "text-destructive font-semibold" : Number(a.quantita) <= Number(a.scorta_minima) ? "text-amber-600 font-semibold" : "font-semibold"} data-testid={`giacenza-${a.id}`}>
            {Number(a.quantita || 0)}
          </span>
          <span className="text-muted-foreground text-xs ml-1">{a.unita_misura || "pz"}</span>
        </TableCell>
        <TableCell className="text-right">
          <div className="flex items-center gap-1 justify-end">
            <Input
              type="number"
              step="0.01"
              min="0"
              placeholder="q.tà"
              value={scaricoInput[a.id] ?? ""}
              onChange={(e) => setScaricoInput((s) => ({ ...s, [a.id]: e.target.value }))}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); doScarico(a); } }}
              disabled={!!scaricoLoading[a.id]}
              className="h-8 w-[70px] text-right font-mono-num text-sm px-2"
              data-testid={`input-scarico-${a.id}`}
            />
            <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => doCarico(a)} disabled={!!scaricoLoading[a.id] || !scaricoInput[a.id]} title="Carica (entrata merce)" data-testid={`btn-carico-${a.id}`}>
              <ArrowUpCircle className="w-4 h-4 text-emerald-600" />
            </Button>
            <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => doScarico(a)} disabled={!!scaricoLoading[a.id] || !scaricoInput[a.id]} title="Scarica (uscita merce)" data-testid={`btn-scarico-${a.id}`}>
              <ArrowDownCircle className="w-4 h-4 text-destructive" />
            </Button>
          </div>
        </TableCell>
        <TableCell className="text-right">
          <Button variant="ghost" size="icon" onClick={() => { setEditing(a); setFormOpen(true); }} data-testid={`btn-edit-${a.id}`}>
            <Pencil className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setConfirmDelete(a)} data-testid={`btn-delete-${a.id}`}>
            <Trash2 className="w-3.5 h-3.5 text-destructive" />
          </Button>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4">
        <Card className="p-4">
          <div className="label-mini">Articoli in listino</div>
          <div className="font-mono-num text-2xl font-semibold mt-1" data-testid="kpi-articoli-tot">{articoli.length}</div>
        </Card>
        <Card className="p-4">
          <div className="label-mini">Categorie</div>
          <div className="font-mono-num text-2xl font-semibold mt-1">{categorie.length}</div>
        </Card>
        <Card className="p-4">
          <div className="label-mini">Fornitori attivi</div>
          <div className="font-mono-num text-2xl font-semibold mt-1" data-testid="kpi-fornitori">{fornitoriAttivi}</div>
        </Card>
        <Card className="p-4">
          <div className="label-mini">Ricarico medio</div>
          <div className="font-mono-num text-2xl font-semibold mt-1" data-testid="kpi-ricarico">
            {ricariciValidi.length > 0 ? `${ricaricoMedio.toFixed(0)}%` : "—"}
          </div>
        </Card>
      </div>

      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <div className="relative flex-1 min-w-[220px] max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Cerca per codice, nome, descrizione…"
              className="pl-9"
              data-testid="input-search-articoli"
            />
          </div>
          <Select value={fFornitore} onValueChange={setFFornitore}>
            <SelectTrigger className="w-[180px]" data-testid="filter-fornitore">
              <SelectValue placeholder="Fornitore" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutti i fornitori</SelectItem>
              {fornitori.map((f) => <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={fCategoria} onValueChange={setFCategoria}>
            <SelectTrigger className="w-[160px]" data-testid="filter-categoria">
              <SelectValue placeholder="Categoria" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutte le categorie</SelectItem>
              {categorie.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button
            variant={raggruppa ? "default" : "outline"}
            size="sm"
            onClick={() => setRaggruppa((v) => !v)}
            className={raggruppa ? "bg-primary hover:bg-primary/90" : ""}
            data-testid="btn-raggruppa"
            title="Raggruppa articoli per categoria con totali"
          >
            <Filter className="w-4 h-4 mr-1.5" /> {raggruppa ? "Raggruppato" : "Raggruppa"}
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-4 border-t border-border/60 pt-4">
          <Button onClick={() => { setEditing({ ...EMPTY_ART }); setFormOpen(true); }} className="bg-primary hover:bg-primary/90" data-testid="btn-nuovo-articolo">
            <Plus className="w-4 h-4 mr-1.5" /> Nuovo articolo
          </Button>
          <Button variant="outline" onClick={() => setScanOpen(true)} data-testid="btn-scan-articolo">
            <Camera className="w-4 h-4 mr-1.5" /> Scan articolo (AI)
          </Button>
          <Button variant="outline" onClick={() => setDdtOpen(true)} data-testid="btn-scan-ddt">
            <ScanLine className="w-4 h-4 mr-1.5" /> Scan DDT (AI)
          </Button>
          <Button variant="outline" onClick={() => setRicarichiOpen(true)} data-testid="btn-ricarichi-categoria">
            <Percent className="w-4 h-4 mr-1.5" /> Ricarichi categoria
          </Button>
          <div className="ml-auto flex gap-2">
            <Button variant="outline" onClick={() => setExportOpen(true)} data-testid="btn-listino-pdf">
              <FileDown className="w-4 h-4 mr-1.5" /> Listino PDF
            </Button>
            <Button variant="outline" onClick={() => setComponiOpen(true)} data-testid="btn-componi-ordine">
              <ShoppingCart className="w-4 h-4 mr-1.5" /> Componi ordine
            </Button>
            <Button variant="outline" onClick={() => setInvDateOpen(true)} data-testid="btn-inventario-pdf">
              <FileDown className="w-4 h-4 mr-1.5" /> Inventario PDF
            </Button>
            <Button asChild variant="outline" data-testid="btn-inventario-xlsx">
              <a href={`${API}/magazzino/inventario.xlsx`} download>
                <FileSpreadsheet className="w-4 h-4 mr-1.5" /> Inventario Excel
              </a>
            </Button>
          </div>
        </div>

        <div className="rounded-md border border-border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40">
                <TableHead>Codice</TableHead>
                <TableHead>Articolo</TableHead>
                <TableHead>Categoria</TableHead>
                <TableHead>Fornitore</TableHead>
                <TableHead className="text-right">Prezzo acquisto</TableHead>
                <TableHead className="text-right">Prezzo vendita</TableHead>
                <TableHead className="text-right" title="Prezzo di vendita + IVA 22%">Vendita IVA inc.</TableHead>
                <TableHead className="text-right">Ricarico</TableHead>
                <TableHead className="text-right w-[80px]">Giacenza</TableHead>
                <TableHead className="text-right w-[170px]" title="Digita la quantità: ↑ carica (entrata), ↓ scarica (uscita). Invio = scarico">Carica / Scarica</TableHead>
                <TableHead className="text-right w-[100px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && <TableRow><TableCell colSpan={11} className="text-center text-muted-foreground py-8">Caricamento…</TableCell></TableRow>}
              {!loading && filtered.length === 0 && (
                <TableRow><TableCell colSpan={11} className="text-center text-muted-foreground py-8" data-testid="empty-articoli">Nessun articolo</TableCell></TableRow>
              )}
              {!loading && !raggruppa && filtered.map((a) => renderRow(a))}
              {!loading && raggruppa && gruppi && gruppi.map((g) => {
                const aperto = gruppoAperto[g.categoria] !== false;
                return (
                  <React.Fragment key={g.categoria}>
                    <TableRow className="bg-primary/5 hover:bg-primary/10 cursor-pointer border-y-2 border-primary/20" onClick={() => setGruppoAperto((s) => ({ ...s, [g.categoria]: !aperto }))} data-testid={`gruppo-header-${g.categoria}`}>
                      <TableCell colSpan={4} className="font-semibold">
                        <span className="inline-flex items-center gap-2">
                          <span className={`inline-block transition-transform ${aperto ? "rotate-90" : ""}`}>▶</span>
                          <Badge className="bg-primary text-primary-foreground">{g.categoria}</Badge>
                          <span className="text-xs text-muted-foreground font-normal">{g.nArt} articoli · {g.qtaTot.toLocaleString("it-IT")} pz totali</span>
                        </span>
                      </TableCell>
                      <TableCell colSpan={3} className="text-right text-xs text-muted-foreground">
                        Valore giacenza gruppo: <b className="text-foreground font-mono-num">{fmtEuro(g.valore)}</b>
                      </TableCell>
                      <TableCell className="text-right font-mono-num text-xs">
                        {g.ricMedio !== null ? (
                          <span className="text-primary font-semibold">+{g.ricMedio.toFixed(0)}%</span>
                        ) : <span className="text-muted-foreground">—</span>}
                      </TableCell>
                      <TableCell colSpan={3}></TableCell>
                    </TableRow>
                    {aperto && g.items.map((a) => renderRow(a))}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </Card>

      <ArticoloForm
        open={formOpen}
        onOpenChange={setFormOpen}
        value={editing}
        fornitori={fornitori}
        onSaved={() => { setFormOpen(false); load(); }}
      />

      <ScanArticoloDialog
        open={scanOpen}
        onOpenChange={setScanOpen}
        fornitori={fornitori}
        onDone={() => { setScanOpen(false); load(); }}
      />

      <ScanDDTDialog
        open={ddtOpen}
        onOpenChange={setDdtOpen}
        fornitori={fornitori}
        onDone={() => { setDdtOpen(false); load(); }}
      />

      <RicarichiCategoriaDialog
        open={ricarichiOpen}
        onOpenChange={setRicarichiOpen}
        categorie={categorie}
      />

      <ComponiOrdineDialog
        open={componiOpen}
        onOpenChange={setComponiOpen}
        articoli={articoli}
        fornitori={fornitori}
      />

      <Dialog open={exportOpen} onOpenChange={setExportOpen}>
        <DialogContent className="max-w-md" data-testid="dialog-listino">
          <DialogHeader>
            <DialogTitle>Listino PDF</DialogTitle>
            <DialogDescription>Filtra il listino da esportare oppure lascia "Tutti" per l'intero magazzino.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">Fornitore</Label>
              <Select value={exportForn} onValueChange={setExportForn}>
                <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti</SelectItem>
                  {fornitori.map((f) => <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">Categoria</Label>
              <Select value={exportCat} onValueChange={setExportCat}>
                <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte</SelectItem>
                  {categorie.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExportOpen(false)}>Annulla</Button>
            <Button asChild className="bg-primary hover:bg-primary/90" onClick={() => setExportOpen(false)} data-testid="btn-download-listino">
              <a href={buildListinoUrl()} download><FileDown className="w-4 h-4 mr-1.5" /> Scarica PDF</a>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!confirmDelete} onOpenChange={(o) => !o && setConfirmDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Elimina articolo
            </AlertDialogTitle>
            <AlertDialogDescription>
              Vuoi davvero eliminare <b>{confirmDelete?.nome}</b>? Verranno rimossi anche i movimenti collegati. L'operazione non è reversibile.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="btn-delete-cancel">Annulla</AlertDialogCancel>
            <AlertDialogAction onClick={remove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="btn-delete-confirm">
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={invDateOpen} onOpenChange={setInvDateOpen}>
        <DialogContent className="max-w-sm" data-testid="dialog-inventario-data">
          <DialogHeader>
            <DialogTitle>Data inventario</DialogTitle>
            <DialogDescription>Indica la data di riferimento da stampare sul PDF dell'inventario.</DialogDescription>
          </DialogHeader>
          <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Inventario al</Label>
          <Input type="date" value={invDate} onChange={(e) => setInvDate(e.target.value)} data-testid="in-inventario-data" />
          <DialogFooter>
            <Button variant="outline" onClick={() => setInvDateOpen(false)}>Annulla</Button>
            <Button className="bg-primary" disabled={!invDate} onClick={() => { window.open(`${API}/magazzino/inventario.pdf?data=${invDate}`, "_blank"); setInvDateOpen(false); }} data-testid="btn-inventario-pdf-confirm">
              <FileDown className="w-4 h-4 mr-1.5" /> Esporta PDF
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
