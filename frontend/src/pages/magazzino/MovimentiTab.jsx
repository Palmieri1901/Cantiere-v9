import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArticoloPicker } from "@/components/ArticoloPicker";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { ArrowUpCircle, ArrowDownCircle, RefreshCw } from "lucide-react";
import { FormField } from "./common";

export default function MovimentiTab() {
  const [movs, setMovs] = useState([]);
  const [articoli, setArticoli] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [tipo, setTipo] = useState("carico");
  const [articoloId, setArticoloId] = useState("");
  const [quantita, setQuantita] = useState(0);
  const [motivo, setMotivo] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [m, a] = await Promise.all([
        api.get("/magazzino/movimenti"),
        api.get("/magazzino/articoli"),
      ]);
      setMovs(m.data);
      setArticoli(a.data);
    } catch { toast.error("Errore caricamento"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const artMap = useMemo(() => Object.fromEntries(articoli.map((a) => [a.id, a])), [articoli]);

  const openForm = (t) => {
    setTipo(t); setArticoloId(""); setQuantita(0); setMotivo(""); setNote("");
    setFormOpen(true);
  };

  const save = async () => {
    if (!articoloId) { toast.error("Seleziona un articolo"); return; }
    if (Number(quantita) <= 0 && tipo !== "rettifica") { toast.error("Quantità deve essere > 0"); return; }
    setSaving(true);
    try {
      await api.post("/magazzino/movimenti", {
        articolo_id: articoloId, tipo, quantita: Number(quantita),
        motivo, note, data: new Date().toISOString().slice(0, 10),
      });
      toast.success("Movimento registrato");
      setFormOpen(false);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Errore"); }
    finally { setSaving(false); }
  };

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <Button onClick={() => openForm("carico")} className="bg-primary hover:bg-primary/90" data-testid="btn-nuovo-carico">
          <ArrowUpCircle className="w-4 h-4 mr-1.5" /> Nuovo carico
        </Button>
        <Button onClick={() => openForm("scarico")} variant="outline" data-testid="btn-nuovo-scarico">
          <ArrowDownCircle className="w-4 h-4 mr-1.5" /> Nuovo scarico
        </Button>
        <Button onClick={() => openForm("rettifica")} variant="outline" data-testid="btn-rettifica">
          <RefreshCw className="w-4 h-4 mr-1.5" /> Rettifica inventario
        </Button>
      </div>

      <div className="rounded-md border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40">
              <TableHead>Data</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Articolo</TableHead>
              <TableHead className="text-right">Q.tà</TableHead>
              <TableHead className="text-right">Giacenza dopo</TableHead>
              <TableHead>Motivo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">Caricamento…</TableCell></TableRow>}
            {!loading && movs.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground" data-testid="empty-movimenti">Nessun movimento</TableCell></TableRow>}
            {movs.map((m) => {
              const art = artMap[m.articolo_id];
              const badgeVariant = m.tipo === "carico" ? "default" : m.tipo === "scarico" ? "destructive" : "secondary";
              return (
                <TableRow key={m.id} data-testid={`row-movimento-${m.id}`}>
                  <TableCell className="font-mono text-xs">{m.data}</TableCell>
                  <TableCell><Badge variant={badgeVariant}>{m.tipo}</Badge></TableCell>
                  <TableCell>{art?.nome || <span className="text-muted-foreground italic">Eliminato</span>}</TableCell>
                  <TableCell className="text-right font-mono-num">{m.tipo === "scarico" ? "-" : "+"}{Math.abs(m.quantita)}</TableCell>
                  <TableCell className="text-right font-mono-num">{m.quantita_dopo}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {m.motivo || "—"}
                    {m.cliente_nome && <span className="block text-[10px] text-primary/80 mt-0.5">Cliente: {m.cliente_nome}</span>}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent data-testid="dialog-movimento">
          <DialogHeader>
            <DialogTitle>
              {tipo === "carico" && "Carico magazzino"}
              {tipo === "scarico" && "Scarico magazzino"}
              {tipo === "rettifica" && "Rettifica inventario"}
            </DialogTitle>
            <DialogDescription>
              {tipo === "rettifica"
                ? "Imposta la quantità reale rilevata dall'inventario fisico."
                : "Aggiungi la quantità movimentata."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <FormField label="Articolo *" full>
              {articoloId && artMap[articoloId] ? (
                <div className="flex items-center justify-between gap-2 p-2.5 rounded-md border border-primary/40 bg-primary/5 text-sm" data-testid="mov-articolo-scelto">
                  <span className="truncate">{artMap[articoloId].codice ? `[${artMap[articoloId].codice}] ` : ""}{artMap[articoloId].nome} <span className="text-muted-foreground text-xs">· giac. {artMap[articoloId].quantita}</span></span>
                  <button type="button" onClick={() => setArticoloId("")} className="text-xs text-primary underline" data-testid="mov-cambia-articolo">cambia</button>
                </div>
              ) : (
                <ArticoloPicker articoli={articoli} onSelect={(a) => setArticoloId(a.id)} showPrezzo={false} testId="mov-select-articolo" />
              )}
            </FormField>
            <FormField label={tipo === "rettifica" ? "Quantità reale" : "Quantità"} full>
              <Input type="number" step="0.01" value={quantita} onChange={(e) => setQuantita(e.target.value)} data-testid="mov-input-quantita" />
            </FormField>
            <FormField label="Motivo" full>
              <Input value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder="es. Consumo per lavoro cliente X" data-testid="mov-input-motivo" />
            </FormField>
            <FormField label="Note" full>
              <Textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} data-testid="mov-input-note" />
            </FormField>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFormOpen(false)}>Annulla</Button>
            <Button onClick={save} disabled={saving} className="bg-primary hover:bg-primary/90" data-testid="btn-save-movimento">
              {saving ? "Salvataggio…" : "Registra"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
