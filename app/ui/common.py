"""Shared UI helpers: session state, sidebar, theme CSS, badges."""
from __future__ import annotations

import html

import streamlit as st

from app.config import model_label
from app.services import workflow

ROLES = {"Floor Supervisor": "supervisor", "Plant Manager": "manager"}
CAT_COLORS = {"safety": "#C62828", "maintenance": "#1565C0", "quality": "#2E7D32"}
CAT_LABELS = {"safety": "Safety", "maintenance": "Maintenance", "quality": "Quality"}

CSS = """
<style>
.block-container {padding-top: 2.2rem; max-width: 1200px;}
.chip {display:inline-block; padding:4px 12px; border-radius:16px; color:#fff; font-weight:600;
       font-size:0.85rem; margin:0 6px 6px 0;}
.chip-muted {background:#64748B;}
.pill {display:inline-block; padding:2px 10px; border-radius:10px; font-size:0.8rem; font-weight:600;}
.synthetic-badge {background:#E8590C; color:#fff; padding:4px 10px; border-radius:6px;
       font-size:0.75rem; font-weight:700; letter-spacing:.04em; text-align:center; margin:4px 0;}
.emergency {background:#B71C1C; color:#fff; padding:16px 20px; border-radius:8px; font-size:1.15rem;
       font-weight:700; margin-bottom:12px; border-left:8px solid #FFEB3B;}
.small-muted {color:#64748B; font-size:0.8rem;}
[data-testid="stMetric"] {background:#fff; border:1px solid #D5DBE3; border-radius:8px; padding:10px 14px;}
</style>
"""


def esc(text: object) -> str:
    return html.escape(str(text))


def chip(label: str, color: str) -> str:
    return f'<span class="chip" style="background:{color}">{esc(label)}</span>'


def pill(label: str, bg: str, fg: str = "#fff") -> str:
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(label)}</span>'


def role() -> str:
    return ROLES[st.session_state.get("role_label", "Floor Supervisor")]


def user() -> str:
    return (st.session_state.get("user_name") or "").strip() or "demo.user"


def is_manager() -> bool:
    return role() == "manager"


@st.cache_resource(show_spinner="Starting MIKRA...")
def _boot() -> bool:
    workflow.ensure_ready()
    return True


def init() -> None:
    """Call at the top of every page: boot backend once, set defaults, inject CSS."""
    _boot()
    st.session_state.setdefault("role_label", "Floor Supervisor")
    st.session_state.setdefault("user_name", "demo.user")
    st.session_state.setdefault("history", [])
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar_identity() -> None:
    with st.sidebar:
        st.markdown("## :orange[MIKRA]")
        st.caption("Manufacturing Intelligent Knowledge Routing Assistant")
        st.selectbox("Role", list(ROLES), key="role_label")
        st.text_input("Your name", key="user_name")
        st.markdown('<div class="synthetic-badge">SYNTHETIC DATA - demo only</div>', unsafe_allow_html=True)
        st.caption(f"Model: `{model_label()}`")


def require_manager() -> None:
    if not is_manager():
        st.warning("This page is for Plant Managers. Switch role in the sidebar.")
        st.stop()


def page_header(title: str, subtitle: str = "") -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
