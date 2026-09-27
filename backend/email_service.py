"""Invio email: SMTP standard (es. Aruba)."""
import os
import re
import ssl
import asyncio
import smtplib
import ipaddress
import logging
from email.message import EmailMessage
from html.parser import HTMLParser
from urllib.parse import urlparse
from fastapi import HTTPException

logger = logging.getLogger("cantiere.email")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = (
    "reply with your password", "reply with the code", "send your password", "cvv",
    "send us your password", "enter your password below", "confirm your card number",
    "your full card number", "seed phrase", "recovery phrase", "verify your card",
    "social security number", "confirm your bank details",
)
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} ≠ real link host {real!r} (G3)")


def _send_smtp(to: str, subject: str, html: str) -> str:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    sender = os.environ.get("SMTP_FROM", user)
    from_name = os.environ.get("EMAIL_FROM_NAME", "Portomare")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{sender}>"
    msg["To"] = to
    msg.set_content("Questo messaggio richiede un client che supporti HTML.")
    msg.add_alternative(html, subtype="html")
    ctx = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
            if user:
                s.login(user, password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls(context=ctx)
            if user:
                s.login(user, password)
            s.send_message(msg)
    return msg["Message-ID"] or "smtp"


async def send_email(*, to: str, subject: str, html: str) -> str | None:
    """Invia un'email via SMTP (SMTP_HOST)."""
    _assert_safe_email(subject, html)
    if not os.environ.get("SMTP_HOST"):
        raise HTTPException(status_code=500, detail="Email non configurata: imposta SMTP_HOST nel file .env")
    try:
        return await asyncio.to_thread(_send_smtp, to, subject, html)
    except Exception as e:
        logger.error(f"SMTP send error: {e}")
        raise HTTPException(status_code=502, detail="Impossibile inviare email (SMTP)")


def build_password_reset_email(reset_link: str, requesting_email: str) -> tuple[str, str]:
    """Restituisce (subject, html) del messaggio di recupero password."""
    brand = os.environ.get("EMAIL_FROM_NAME", "Portomare")
    subject = f"{brand} — Recupero password gestionale"
    html = f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:32px 0;font-family:Arial,Helvetica,sans-serif">
  <tr><td align="center">
    <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
      <tr><td style="padding-bottom:16px">
        <div style="font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:#64748b">Gestionale Cantiere</div>
        <div style="font-size:22px;font-weight:600;color:#0f172a;margin-top:4px">{brand}</div>
      </td></tr>
      <tr><td>
        <h1 style="font-size:20px;color:#0f172a;margin:0 0 12px 0">Richiesta di recupero password</h1>
        <p style="font-size:14px;color:#334155;line-height:1.6;margin:0 0 12px 0">
          È stata richiesta la reimpostazione della password del gestionale
          dall'account <strong>{requesting_email}</strong>.
        </p>
        <p style="font-size:14px;color:#334155;line-height:1.6;margin:0 0 24px 0">
          Clicca sul pulsante qui sotto per impostare una nuova password. Il link
          è valido per <strong>1 ora</strong> e può essere utilizzato una sola volta.
        </p>
        <p style="text-align:center;margin:24px 0">
          <a href="{reset_link}" style="display:inline-block;background:#0f172a;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:6px;font-weight:600;font-size:14px">
            Reimposta la password
          </a>
        </p>
        <p style="font-size:12px;color:#64748b;line-height:1.6;margin:24px 0 0 0">
          Se non hai richiesto tu la reimpostazione puoi ignorare questa email:
          la password attuale rimarrà valida. Il link diretto è:<br/>
          <span style="word-break:break-all;color:#334155">{reset_link}</span>
        </p>
      </td></tr>
      <tr><td style="padding-top:24px;border-top:1px solid #e2e8f0;margin-top:24px">
        <p style="font-size:11px;color:#94a3b8;line-height:1.5;margin:16px 0 0 0">
          Messaggio automatico inviato da {brand}. Non richiediamo mai la tua
          password né dati bancari via email.
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
"""
    return subject, html
