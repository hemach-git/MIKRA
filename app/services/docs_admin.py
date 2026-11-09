"""Document lifecycle: draft -> (manager approve) -> published (old version retired) | rejected.

Supervisors and the answer pipeline only ever see PUBLISHED versions.
"""
from __future__ import annotations

import json
import re

from app.data import db
from app.models.schemas import DocumentIn, ReviewDecision
from app.observability.logging import log_event
from app.services import audit, retriever
from app.services.guardrails import scan_document

_H2 = re.compile(r"^##\s+(.*)$", re.M)


def split_sections(content: str) -> list[tuple[str, str]]:
    """Split markdown on '## ' headings. Content before the first heading becomes 'General'."""
    parts = _H2.split(content)
    out = []
    if parts[0].strip():
        out.append(("General", parts[0].strip()))
    for i in range(1, len(parts), 2):
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            out.append((parts[i].strip(), body))
    return out


def _insert(c, doc: DocumentIn, version: int, status: str, actor: str, is_synthetic: int) -> str:
    doc_id = f"{doc.doc_key}-v{version}"
    flags = scan_document(doc.content)
    c.execute("""INSERT INTO documents (doc_id, doc_key, title, category, version, status, owner, equipment,
                 content, created_by, created_at, guardrail_flags, is_synthetic)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (doc_id, doc.doc_key, doc.title, doc.category, version, status, doc.owner, doc.equipment,
               doc.content, actor, db.now_iso(), json.dumps(flags), is_synthetic))
    for n, (section, text) in enumerate(split_sections(doc.content), 1):
        c.execute("INSERT INTO chunks (chunk_id, doc_id, section_no, section, text) VALUES (?,?,?,?,?)",
                  (f"{doc_id}#s{n}", doc_id, n, section, text))
    return doc_id


def list_documents(role: str = "supervisor", status: str | None = None, category: str | None = None) -> list[dict]:
    """Supervisors: published only. Managers: all statuses (optionally filtered)."""
    sql = """SELECT d.doc_id, d.doc_key, d.title, d.category, d.version, d.status, d.owner, d.equipment,
                    d.created_by, d.created_at, d.reviewed_by, d.reviewed_at, d.review_note,
                    d.guardrail_flags, d.is_synthetic, COUNT(c.chunk_id) AS sections
             FROM documents d LEFT JOIN chunks c ON c.doc_id = d.doc_id WHERE 1=1"""
    params: list = []
    if role != "manager":
        sql += " AND d.status='published'"
    elif status:
        sql += " AND d.status=?"
        params.append(status)
    if category:
        sql += " AND d.category=?"
        params.append(category)
    sql += " GROUP BY d.doc_id ORDER BY d.category, d.doc_key, d.version DESC"
    return db.rows(sql, tuple(params))


def get_document(doc_id: str, role: str = "supervisor") -> dict | None:
    r = db.rows("SELECT * FROM documents WHERE doc_id=?", (doc_id,))
    if not r or (role != "manager" and r[0]["status"] != "published"):
        return None
    r[0]["sections"] = db.rows("SELECT chunk_id, section_no, section, text FROM chunks WHERE doc_id=? ORDER BY section_no", (doc_id,))
    return r[0]


def get_chunk(chunk_id: str) -> dict | None:
    r = db.rows("""SELECT c.*, d.doc_key, d.title, d.version, d.status, d.category FROM chunks c
                   JOIN documents d ON d.doc_id=c.doc_id WHERE c.chunk_id=?""", (chunk_id,))
    return r[0] if r else None


def submit_draft(doc: DocumentIn | dict, actor: str, is_synthetic: int = 0) -> str:
    """Create a new draft version (new doc_key -> v1, existing -> next version). Never auto-publishes."""
    doc = DocumentIn.model_validate(doc)
    with db.tx() as c:
        existing = c.execute("SELECT category, MAX(version) v FROM documents WHERE doc_key=?", (doc.doc_key,)).fetchone()
        if existing["v"] and existing["category"] != doc.category:
            raise ValueError(f"{doc.doc_key} is a {existing['category']} document; category cannot change.")
        if c.execute("SELECT 1 FROM documents WHERE doc_key=? AND status='draft'", (doc.doc_key,)).fetchone():
            raise ValueError(f"{doc.doc_key} already has a pending draft. Approve or reject it first.")
        version = (existing["v"] or 0) + 1
        doc_id = _insert(c, doc, version, "draft", actor, is_synthetic)
        audit.record(actor, "manager", "submit_draft", doc_id, "draft", details={"title": doc.title}, conn=c)
    log_event("doc_draft", doc_id=doc_id, actor=actor)
    return doc_id


def review_document(doc_id: str, decision: ReviewDecision | dict) -> dict:
    """Manager approval gate. Approve -> publish + retire previous published version + re-index."""
    d = ReviewDecision.model_validate(decision)
    with db.tx() as c:
        row = c.execute("SELECT doc_key, status FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
        if not row:
            raise ValueError(f"Unknown document {doc_id}")
        if row["status"] != "draft":
            raise ValueError(f"{doc_id} is {row['status']}, only drafts can be reviewed.")
        new_status = "published" if d.decision == "approved" else "rejected"
        retired = []
        if new_status == "published":
            retired = [r["doc_id"] for r in c.execute(
                "SELECT doc_id FROM documents WHERE doc_key=? AND status='published'", (row["doc_key"],))]
            c.execute("UPDATE documents SET status='retired' WHERE doc_key=? AND status='published'", (row["doc_key"],))
        c.execute("""UPDATE documents SET status=?, reviewed_by=?, reviewed_at=?, review_note=? WHERE doc_id=?""",
                  (new_status, d.reviewer, db.now_iso(), d.note, doc_id))
        audit.record(d.reviewer, "manager", "review_document", doc_id, d.decision,
                     details={"retired": retired, "note": d.note}, conn=c)
    retriever.invalidate()
    log_event("doc_review", doc_id=doc_id, decision=d.decision)
    return {"doc_id": doc_id, "status": new_status, "retired": retired}


def retire_document(doc_id: str, actor: str, note: str = "") -> dict:
    with db.tx() as c:
        n = c.execute("UPDATE documents SET status='retired' WHERE doc_id=? AND status='published'", (doc_id,)).rowcount
        if not n:
            raise ValueError(f"{doc_id} is not a published document.")
        audit.record(actor, "manager", "retire_document", doc_id, "retired", details={"note": note}, conn=c)
    retriever.invalidate()
    return {"doc_id": doc_id, "status": "retired"}
