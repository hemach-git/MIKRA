import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # noqa: E702

import streamlit as st

from app.ui import common

st.set_page_config(page_title="MIKRA", page_icon=":material/precision_manufacturing:", layout="wide")
common.init()
common.sidebar_identity()

pages = [
    st.Page("pages/ask.py", title="Ask", icon=":material/forum:", default=True),
    st.Page("pages/documents.py", title="Documents", icon=":material/description:"),
]
if common.is_manager():
    pages += [
        st.Page("pages/review_queue.py", title="Review queue", icon=":material/flag:"),
        st.Page("pages/analytics.py", title="Analytics", icon=":material/monitoring:"),
        st.Page("pages/diagnostics.py", title="Diagnostics", icon=":material/health_and_safety:"),
    ]

st.navigation(pages).run()
