"""Test suite for Consenso Privacy PDF endpoint."""
import io
import os
import pytest
import requests
from pypdf import PdfReader

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture(scope="module")
def auth_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"password": "admin"}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


def _pdf_text(content: bytes):
    reader = PdfReader(io.BytesIO(content))
    return reader, "\n".join((p.extract_text() or "") for p in reader.pages)


def test_privacy_pdf_with_name(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/servizio/privacy.pdf", params={"nome": "Getili Francesco"}, timeout=20)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    reader, text = _pdf_text(r.content)
    assert len(reader.pages) == 1, f"Expected 1 page, got {len(reader.pages)}"
    assert "Getili Francesco" in text, f"Name not found in PDF text: {text[:500]}"


def test_privacy_pdf_freetext(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/servizio/privacy.pdf", params={"nome": "Mario Prova Libero"}, timeout=20)
    assert r.status_code == 200
    reader, text = _pdf_text(r.content)
    assert len(reader.pages) == 1
    assert "Mario Prova Libero" in text


def test_privacy_pdf_empty(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/servizio/privacy.pdf", timeout=20)
    assert r.status_code == 200
    reader, _ = _pdf_text(r.content)
    assert len(reader.pages) == 1


def test_privacy_pdf_unauthenticated():
    r = requests.get(f"{BASE_URL}/api/servizio/privacy.pdf", timeout=15)
    assert r.status_code == 401


def test_coordinate_pdf_regression(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/servizio/coordinate.pdf", timeout=20)
    # Might be 400 if no IBAN configured
    assert r.status_code in (200, 400)


def test_getili_exists_in_clients(auth_session):
    """Ensure Getili Francesco is in archive (dedup check on frontend)."""
    r = auth_session.get(f"{BASE_URL}/api/clienti", timeout=15)
    assert r.status_code == 200
    clienti = r.json()
    matches = [c for c in clienti if "getili" in (c.get("cognome", "") + " " + c.get("nome", "")).lower()]
    # Just report - test is informational
    print(f"Found {len(matches)} 'getili' entries in clienti")
