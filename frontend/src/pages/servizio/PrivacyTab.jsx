import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { confirmDialog } from "@/components/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { Save, Eye, RotateCcw, Sparkles, Camera, Upload } from "lucide-react";

const L = ({ children }) => <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{children}</Label>;

export default function PrivacyTab({ dati, onSaved, anteprima }) {
  const [testo, setTesto] = useState(dati.privacy_testo || "");
  const [clienti, setClienti] = useState([]);
  const [nomeCliente, setNomeCliente] = useState("");
  const [showSugg, setShowSugg] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    Promise.all([api.get("/clienti").catch(() => ({ data: [] })), api.get("/esterni").catch(() => ({ data: [] }))]).then(([c, e]) => {
      const seen = new Set(); const out = [];
      for (const x of c.data) {
        const label = `${x.cognome || ""} ${x.nome || ""}`.trim(); const k = label.toLowerCase();
        if (!k || seen.has(k)) continue; seen.add(k); out.push({ key: x.id, label, extra: x.tipo_barca || "" });
      }
      for (const x of e.data) { const k = (x.nome || "").toLowerCase(); if (!k || seen.has(k)) continue; seen.add(k); out.push({ key: x.id, label: x.nome, extra: "cliente esterno" }); }
      setClienti(out.sort((a, b) => a.label.localeCompare(b.label)));
    });
  }, []);
  const suggerimenti = useMemo(() => {
    const q = nomeCliente.trim().toLowerCase();
    return (q ? clienti.filter((c) => c.label.toLowerCase().includes(q)) : clienti).slice(0, 8);
  }, [nomeCliente, clienti]);

  const salva = async () => { const r = await api.put("/servizio/dati", { privacy_testo: testo }); onSaved(r.data); toast.success("Testo privacy salvato"); };
  const ripristina = async () => {
    if (!await confirmDialog("Sostituire il testo attuale con l'informativa standard?", { title: "Ripristina testo", okLabel: "Ripristina", danger: false })) return;
    const r = await api.get("/servizio/privacy/default"); setTesto(r.data.testo);
  };
  const onFile = async (e) => {
    const file = e.target.files?.[0]; e.target.value = "";
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) return toast.error("File troppo grande (max 8MB)");
    setBusy(true);
    try {
      const b64 = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(file); });
      const r = await api.post("/servizio/privacy/estrai", { file_base64: b64 });
      if (!await confirmDialog("Testo riconosciuto. Sostituire il testo attuale con quello estratto dal documento?", { title: "Importa da documento", okLabel: "Sostituisci", danger: false })) return;
      setTesto(r.data.testo); toast.success("Testo importato: controlla e salva");
    } catch (err) { toast.error(err.response?.data?.detail || "Estrazione non riuscita"); }
    finally { setBusy(false); }
  };

  return (
    <div className="space-y-4" data-testid="privacy-tab">
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="label-mini">Testo dell'informativa (modificabile)</div>
          <div className="flex gap-2 flex-wrap">
            <label className="cursor-pointer">
              <input type="file" accept="image/*,application/pdf" hidden onChange={onFile} data-testid="input-privacy-file" />
              <span className="inline-flex items-center gap-1.5 px-3 py-2 border border-input rounded-md text-sm hover:bg-muted"><Upload className="w-3.5 h-3.5" /> {busy ? "Lettura in corso…" : "Carica PDF/foto (AI)"}</span>
            </label>
            <label className="cursor-pointer">
              <input type="file" accept="image/*" capture="environment" hidden onChange={onFile} data-testid="input-privacy-camera" />
              <span className="inline-flex items-center gap-1.5 px-3 py-2 border border-input rounded-md text-sm hover:bg-muted"><Camera className="w-3.5 h-3.5" /> Scatta foto</span>
            </label>
            <Button variant="ghost" size="sm" onClick={ripristina} data-testid="btn-privacy-default"><RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Testo standard</Button>
          </div>
        </div>
        <Textarea rows={18} value={testo} onChange={(e) => setTesto(e.target.value)} className="font-mono text-xs leading-relaxed" data-testid="textarea-privacy" />
        <div className="text-xs text-muted-foreground flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> Segnaposto disponibili: <code>{"{cantiere}"}</code> <code>{"{indirizzo}"}</code> <code>{"{telefono}"}</code> <code>{"{email}"}</code> — vengono sostituiti con i dati del cantiere. Righe in MAIUSCOLO o numerate "1. TITOLO" diventano titoli nel PDF.</div>
        <div className="flex gap-2 flex-wrap items-end">
          <Button onClick={salva} className="bg-primary hover:bg-primary/90" data-testid="btn-salva-privacy"><Save className="w-4 h-4 mr-1.5" /> Salva testo</Button>
          <div className="space-y-1.5 min-w-80 relative"><L>Nome cliente sul modulo (opzionale)</L>
            <Input value={nomeCliente} onChange={(e) => { setNomeCliente(e.target.value); setShowSugg(true); }} onFocus={() => setShowSugg(true)} onBlur={() => setTimeout(() => setShowSugg(false), 150)} placeholder="Cerca in archivio o scrivi un nome…" data-testid="input-privacy-cliente" />
            {showSugg && suggerimenti.length > 0 && (
              <div className="absolute z-30 left-0 right-0 top-full mt-1 bg-card border rounded-md shadow-lg divide-y max-h-56 overflow-y-auto" data-testid="privacy-suggerimenti">
                {suggerimenti.map((s) => (
                  <button key={s.key} type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => { setNomeCliente(s.label); setShowSugg(false); }} className="w-full text-left px-3 py-2 hover:bg-muted text-sm" data-testid={`privacy-sugg-${s.key}`}>
                    {s.label}{s.extra && <span className="text-xs text-muted-foreground"> · {s.extra}</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button variant="outline" onClick={() => anteprima(`/servizio/privacy.pdf${nomeCliente.trim() ? `?nome=${encodeURIComponent(nomeCliente.trim())}` : ""}`, `Consenso_privacy${nomeCliente.trim() ? `_${nomeCliente.trim().replace(/\s+/g, "_")}` : ""}.pdf`)} data-testid="btn-pdf-privacy"><Eye className="w-4 h-4 mr-1.5" /> Anteprima PDF consenso</Button>
        </div>
      </Card>
    </div>
  );
}
