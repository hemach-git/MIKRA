import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))  # noqa: E702

import difflib
import json

import streamlit as st

from app.services import docs_admin
from app.ui import common
from app.ui.common import CAT_COLORS, CAT_LABELS, chip, esc, pill

common.init()
mgr = common.is_manager()
STATUS_COLORS = {"published": "#2E7D32", "draft": "#F9A825", "rejected": "#C62828", "retired": "#64748B"}
CATS = ["safety", "maintenance", "quality"]

EXAMPLE = """## 1. Purpose
Describe what this procedure covers and who it applies to.

## 2. Procedure
1. First step.
2. Second step.

## 3. Safety notes
List any hazards and required PPE.
"""


def viewer(doc_id: str) -> None:
    d = docs_admin.get_document(doc_id, common.role())
    if not d:
        st.info("Document not available.")
        return
    st.markdown(chip(CAT_LABELS.get(d["category"], d["category"]), CAT_COLORS.get(d["category"], "#475569"))
                + pill(d["status"], STATUS_COLORS.get(d["status"], "#475569")), unsafe_allow_html=True)
    st.markdown(f"### {d['title']}")
    st.caption(f"{d['doc_key']} v{d['version']} · Owner: {d.get('owner') or '-'} · Equipment: {d.get('equipment') or '-'}")
    for s in d.get("sections", []):
        with st.expander(s["section"], expanded=False):
            st.markdown(s["text"])


def browse() -> None:
    c1, c2, c3 = st.columns(3)
    status = None
    if mgr:
        status = c1.selectbox("Status", ["all", "published", "draft", "rejected", "retired"])
        status = None if status == "all" else status
    cat = c2.selectbox("Category", ["all"] + CATS, format_func=lambda x: CAT_LABELS.get(x, "All"))
    docs = docs_admin.list_documents(role=common.role(), status=status, category=None if cat == "all" else cat)
    if not docs:
        st.info("No documents match these filters.")
        return
    labels = {d["doc_id"]: f"{d['doc_key']} v{d['version']} - {d['title']}" + (f" [{d['status']}]" if mgr else "")
              for d in docs}
    sel = c3.selectbox("Document", list(labels), format_func=labels.get)
    with st.container(border=True):
        viewer(sel)


def new_doc_form() -> None:
    with st.form("new_doc"):
        a, b = st.columns(2)
        key = a.text_input("Document key", placeholder="e.g. MM-CONV-02 (existing key = new version)")
        title = b.text_input("Title")
        c, d, e = st.columns(3)
        cat = c.selectbox("Category", CATS, format_func=CAT_LABELS.get)
        owner = d.text_input("Owner", value="Plant Manager")
        equip = e.text_input("Equipment (optional)")
        content = st.text_area("Content (Markdown, sections start with '## ')", value=EXAMPLE, height=260)
        go = st.form_submit_button("Submit draft for approval", type="primary")
    if go:
        try:
            doc_id = docs_admin.submit_draft({"doc_key": key.strip().upper(), "title": title.strip(), "category": cat,
                                              "owner": owner.strip(), "equipment": equip.strip(),
                                              "content": content}, common.user())
            st.success(f"Draft submitted ({doc_id}). It needs approval below before supervisors can see it.")
        except ValueError as exc:
            st.error(f"Could not submit: {exc}")


def pending() -> None:
    drafts = docs_admin.list_documents(role="manager", status="draft")
    if not drafts:
        st.info("No drafts waiting for approval.")
        return
    published = docs_admin.list_documents(role="manager", status="published")
    for dr in drafts:
        with st.container(border=True):
            st.markdown(f"**{dr['doc_key']} v{dr['version']}** - {esc(dr['title'])}")
            st.caption(f"Submitted by {dr.get('created_by') or '-'} on {str(dr.get('created_at'))[:16]}")
            try:
                flags = json.loads(dr.get("guardrail_flags") or "[]")
            except (TypeError, ValueError):
                flags = []
            if flags:
                st.warning("Automatic checks flagged: " + ", ".join(map(str, flags)))
            new = docs_admin.get_document(dr["doc_id"], "manager") or {}
            cur_meta = next((p for p in published if p["doc_key"] == dr["doc_key"]), None)
            cur = docs_admin.get_document(cur_meta["doc_id"], "manager") if cur_meta else None
            old_txt = (cur or {}).get("content", "")
            new_txt = new.get("content", "")
            left, right = st.columns(2)
            cur_label = f" (v{cur_meta['version']})" if cur_meta else " - none (new document)"
            left.markdown(f"**Current published**{cur_label}")
            left.code(old_txt or "(no published version)", language="markdown", wrap_lines=True)
            right.markdown(f"**Proposed draft (v{dr['version']})**")
            right.code(new_txt, language="markdown", wrap_lines=True)
            if old_txt:
                diff = "\n".join(difflib.unified_diff(old_txt.splitlines(), new_txt.splitlines(),
                                                      "published", "draft", lineterm="", n=1))
                with st.expander("Changes only (diff)", expanded=True):
                    st.code(diff or "No text differences.", language="diff")
            note = st.text_input("Review note", key=f"note_{dr['doc_id']}")
            a, r, _ = st.columns([1, 1, 3])
            for label, decision, kind, col in (("Approve & publish", "approved", "primary", a),
                                               ("Reject", "rejected", "secondary", r)):
                if col.button(label, key=f"{decision}_{dr['doc_id']}", type=kind, width="stretch"):
                    try:
                        res = docs_admin.review_document(dr["doc_id"], {"decision": decision,
                                                                        "reviewer": common.user(), "note": note})
                        st.toast(f"{dr['doc_key']} v{dr['version']}: {res['status']}", icon="✅")
                        st.session_state["flash"] = f"{dr['doc_key']} v{dr['version']} {res['status']}."
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))


common.page_header("Documents", "Approved procedures, manuals and quality standards." if not mgr
                   else "Browse documents, submit updates and approve drafts.")
if st.session_state.get("flash"):
    st.success(st.session_state.pop("flash"))

if mgr:
    tab1, tab2, tab3 = st.tabs(["Browse", "Pending approvals", "New / update document"])
    with tab1:
        browse()
    with tab2:
        pending()
    with tab3:
        new_doc_form()
else:
    browse()
