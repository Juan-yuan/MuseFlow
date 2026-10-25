"""
MuseFlow — Streamlit console (Knowledge-Graph visual language).
Run: streamlit run app.py
"""

from __future__ import annotations

import html
import traceback
from typing import Literal

import streamlit as st

from nodes.zhihu_content_check_node import check_zhihu_content_node
from nodes.zhihu_content_generate_node import generate_zhihu_content_node
from nodes.zhihu_image_generate_node import generate_zhihu_image_node
from nodes.zhihu_publish_node_v2 import auto_publish_zhihu_node

Platform = Literal["Zhihu", "Quora"]

BRAND = "MuseFlow"
TAGLINE = "Compose once. Publish with intent — Zhihu or Quora."
USER_ICON = "👤"
AI_ICON = "✦"
INPUT_PLACEHOLDER = "Enter a title or topic to publish…"
EMPTY_HINT = "Pick a channel, try an example, or type your own topic below."
DISCLAIMER = "Zhihu may open a browser window for login or publish confirmation."
EXAMPLE_TOPICS = [
    "How to nourish the lungs with TCM in autumn and winter",
    "Daily spleen-strengthening habits for office workers",
    "Gentle qi-circulation routines for better sleep",
]

st.set_page_config(
    page_title=BRAND,
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #1c2b24;
  --muted: #5c6b63;
  --accent: #2f6b55;
  --accent-soft: #e8f2ed;
  --user-soft: #eef2f0;
  --line: #d7e2db;
  --bg: #f6f8f6;
  --panel: #ffffff;
  --content-max: min(1080px, 92vw);
  --composer-h: 2.75rem;
}

html, body, [class*="css"] {
  font-family: "IBM Plex Sans", sans-serif;
  color: var(--ink);
}

.stApp {
  background:
    radial-gradient(1200px 500px at 10% -10%, #e7f1ea 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #eef4f0 0%, transparent 50%),
    var(--bg);
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }

div[data-testid="stMainBlockContainer"],
.block-container {
  max-width: var(--content-max) !important;
  padding-left: clamp(1rem, 3vw, 2rem) !important;
  padding-right: clamp(1rem, 3vw, 2rem) !important;
  padding-top: 1rem !important;
  padding-bottom: 1.5rem !important;
}

.brand-wrap {
  margin: 0 auto 0.85rem auto;
  text-align: center;
}
.brand-mark {
  font-size: 1.5rem;
  letter-spacing: 0.02em;
  margin-bottom: 0.25rem;
}
.brand-name {
  font-family: "Source Serif 4", Georgia, serif;
  font-weight: 600;
  font-size: clamp(1.55rem, 2.2vw, 1.9rem);
  line-height: 1.2;
  color: var(--ink);
  margin: 0;
}
.brand-tagline {
  margin: 0.45rem auto 0 auto;
  max-width: 40rem;
  color: var(--muted);
  font-size: 0.95rem;
  line-height: 1.5;
}
.status-row {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 0.7rem;
  padding: 0.28rem 0.7rem;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--panel);
  font-size: 0.78rem;
  color: var(--muted);
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #b0b8b3;
}
.status-dot.ok { background: #2f6b55; }
.status-dot.bad { background: #a33b2d; }

.empty-hint {
  margin: 0.85rem auto 0.55rem auto;
  text-align: center;
  color: var(--muted);
  font-size: 0.9rem;
}
.disclaimer {
  margin: 0.9rem auto 0 auto;
  text-align: center;
  color: #7a8780;
  font-size: 0.75rem;
}

.channel-row {
  display: flex;
  justify-content: center;
  margin: 0.35rem 0 0.15rem;
}

.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
  margin: 0.7rem 0;
  max-width: min(78%, 720px);
}
.msg-row.user {
  margin-right: auto;
  flex-direction: row;
}
.msg-row.ai {
  margin-left: auto;
  flex-direction: row-reverse;
}
.msg-icon {
  flex: 0 0 2rem;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  background: var(--panel);
  border: 1px solid var(--line);
}
.msg-row.ai .msg-icon {
  background: var(--accent-soft);
  border-color: transparent;
}
.msg-bubble {
  padding: 0.75rem 0.95rem;
  border-radius: 14px;
  line-height: 1.55;
  font-size: 0.95rem;
  word-break: break-word;
}
.msg-row.user .msg-bubble {
  background: var(--user-soft);
  border: 1px solid var(--line);
  border-top-left-radius: 4px;
  color: var(--ink);
}
.msg-row.ai .msg-bubble {
  background: var(--panel);
  border: 1px solid var(--line);
  border-top-right-radius: 4px;
  color: var(--ink);
}

.ask-composer [data-testid="stForm"] {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 14px;
  padding: 0.4rem 0.45rem 0.4rem 0.65rem;
  margin-top: 0.85rem;
}
.ask-composer [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
  align-items: center !important;
  gap: 0.5rem !important;
}
.ask-composer [data-testid="stForm"] [data-testid="column"] {
  display: flex !important;
  align-items: center !important;
}
.ask-composer [data-testid="stForm"] [data-testid="stTextInput"] {
  width: 100%;
}
.ask-composer [data-testid="stForm"] [data-testid="stTextInput"] label { display: none; }
.ask-composer [data-testid="stForm"] [data-testid="stTextInput"] > div,
.ask-composer [data-testid="stForm"] [data-testid="stTextInput"] > div > div {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  height: var(--composer-h) !important;
  min-height: var(--composer-h) !important;
}
.ask-composer [data-testid="stForm"] input {
  font-family: "IBM Plex Sans", sans-serif !important;
  font-size: 0.95rem !important;
  height: var(--composer-h) !important;
  min-height: var(--composer-h) !important;
  max-height: var(--composer-h) !important;
  line-height: var(--composer-h) !important;
  padding: 0 0.35rem !important;
  margin: 0 !important;
  box-sizing: border-box !important;
  color: var(--ink) !important;
}
.ask-composer [data-testid="stForm"] .stButton {
  width: 100%;
  height: var(--composer-h) !important;
  margin: 0 !important;
}
.ask-composer [data-testid="stForm"] .stButton > button {
  width: 100% !important;
  height: var(--composer-h) !important;
  min-height: var(--composer-h) !important;
  max-height: var(--composer-h) !important;
  margin: 0 !important;
  padding: 0 !important;
  background: var(--accent) !important;
  border: 1px solid var(--accent) !important;
  border-radius: 10px !important;
  color: #fff !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  line-height: 1 !important;
  white-space: nowrap !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-sizing: border-box !important;
}
.ask-composer [data-testid="stForm"] .stButton > button:hover {
  background: #275a48 !important;
  border-color: #275a48 !important;
  color: #fff !important;
}

section[data-testid="stSidebar"] {
  background: #f3f6f4;
  border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  font-family: "Source Serif 4", Georgia, serif;
  font-weight: 600;
  color: var(--ink);
}

.stButton > button {
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--ink);
  border-radius: 10px;
  font-weight: 500;
}
.stButton > button:hover {
  border-color: var(--accent);
  color: var(--accent);
}

div[data-testid="stRadio"] div[role="radiogroup"] {
  display: flex;
  gap: 0.35rem;
  justify-content: center;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0.28rem;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] {
  margin: 0 !important;
  padding: 0.4rem 1.1rem !important;
  border-radius: 999px !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] p {
  color: var(--muted) !important;
  font-weight: 600 !important;
  font-size: 0.86rem !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {
  background: var(--accent-soft) !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p {
  color: var(--accent) !important;
}

div[data-testid="stHorizontalBlock"]:has(> :nth-child(3)):not(:has(> :nth-child(4))) {
  align-items: stretch !important;
  gap: 0.65rem !important;
}
div[data-testid="stHorizontalBlock"]:has(> :nth-child(3)):not(:has(> :nth-child(4)))
  > [data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(> :nth-child(3)):not(:has(> :nth-child(4)))
  > [data-testid="stColumn"] {
  display: flex !important;
}
div[data-testid="stHorizontalBlock"]:has(> :nth-child(3)):not(:has(> :nth-child(4))) .stButton {
  width: 100% !important;
  height: 100% !important;
}
div[data-testid="stHorizontalBlock"]:has(> :nth-child(3)):not(:has(> :nth-child(4))) .stButton > button {
  width: 100% !important;
  height: 6.25rem !important;
  min-height: 6.25rem !important;
  max-height: 6.25rem !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  text-align: left !important;
  white-space: normal !important;
  overflow: hidden !important;
  padding: 0.75rem 0.9rem !important;
  background: #e8f2ed !important;
  border: 1px solid transparent !important;
  border-radius: 10px !important;
  color: #1c2b24 !important;
  font-size: 0.86rem !important;
  font-weight: 500 !important;
  line-height: 1.35 !important;
  box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"]:has(> :nth-child(3)):not(:has(> :nth-child(4))) .stButton > button:hover {
  background: #dceae3 !important;
  border-color: #2f6b55 !important;
  color: #1c2b24 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def _init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_topic" not in st.session_state:
        st.session_state.pending_topic = None
    if "platform" not in st.session_state:
        st.session_state.platform = "Zhihu"


def submit_topic(topic: str) -> None:
    st.session_state.pending_topic = topic.strip()


def render_message(role: str, content: str) -> None:
    safe = html.escape(content).replace("\n", "<br>")
    if role == "user":
        st.markdown(
            f'<div class="msg-row user"><div class="msg-icon">{USER_ICON}</div>'
            f'<div class="msg-bubble">{safe}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="msg-row ai"><div class="msg-icon">{AI_ICON}</div>'
            f'<div class="msg-bubble">{safe}</div></div>',
            unsafe_allow_html=True,
        )


def render_ask_composer(form_key: str) -> None:
    st.markdown('<div class="ask-composer">', unsafe_allow_html=True)
    with st.form(form_key, clear_on_submit=True):
        input_col, send_col = st.columns([8, 1.2])
        with input_col:
            topic = st.text_input(
                "Topic",
                placeholder=INPUT_PLACEHOLDER,
                label_visibility="collapsed",
            )
        with send_col:
            sent = st.form_submit_button("Send", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if sent and topic.strip():
        submit_topic(topic)
        st.rerun()


def run_zhihu_pipeline(topic: str, status) -> str:
    state: dict = {"input": topic}

    status.update(label="Writing article…", state="running")
    state.update(generate_zhihu_content_node(state))

    status.update(label="Generating images…", state="running")
    state.update(generate_zhihu_image_node(state))

    status.update(label="Running content check…", state="running")
    state.update(check_zhihu_content_node(state))
    if not state.get("is_can_publish_zhihu_post"):
        return (
            "Content check failed — publish was skipped.\n\n"
            f"Title: {state.get('zhihu_tcm_post_title', '—')}"
        )

    status.update(label="Publishing to Zhihu (browser may open)…", state="running")
    result = auto_publish_zhihu_node(state)
    output = result.get("output", "Zhihu publish finished.")
    return (
        f"{output}\n\n"
        f"Generated title: {state.get('zhihu_tcm_post_title', '—')}\n"
        f"Topics: {state.get('zhihu_tcm_post_site', '—')}"
    )


def run_quora_pipeline(topic: str, status) -> str:
    status.update(label="Quora channel…", state="running")
    return (
        "Quora publishing is selected, but the Quora node is not connected yet.\n\n"
        f"Your topic was recorded: {topic}\n\n"
        "Switch to Zhihu to run the live pipeline, or ask to implement the Quora publisher next."
    )


def main() -> None:
    _init_state()
    is_home = not st.session_state.messages and not st.session_state.pending_topic

    if is_home:
        st.markdown(
            """
<style>
[data-testid="stAppViewContainer"] > .main,
[data-testid="stMain"] {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  min-height: 100vh !important;
}
[data-testid="stMain"] > div { width: 100%; }
div[data-testid="stMainBlockContainer"],
.block-container {
  min-height: calc(100vh - 1rem) !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  padding-top: 0 !important;
  padding-bottom: 10vh !important;
  transform: translateY(-3.5vh);
}
</style>
""",
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.markdown("### Channel")
        st.caption("Use the Zhihu / Quora switch under the title.")
        st.divider()
        if st.button("New chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_topic = None
            st.rerun()
        st.divider()
        st.markdown(
            "**How it works**\n\n"
            "1. Choose Zhihu or Quora\n"
            "2. Enter a title or topic\n"
            "3. MuseFlow writes, checks, and publishes"
        )

    platform_preview = st.session_state.get("platform", "Zhihu")
    channel_ok = platform_preview == "Zhihu"
    status_label = f"{platform_preview} ready" if channel_ok else f"{platform_preview} coming soon"
    status_class = "ok" if channel_ok else "bad"

    st.markdown(
        f"""
<div class="brand-wrap">
  <div class="brand-mark">✦</div>
  <h1 class="brand-name">{html.escape(BRAND)}</h1>
  <p class="brand-tagline">{html.escape(TAGLINE)}</p>
  <div class="status-row"><span class="status-dot {status_class}"></span>{html.escape(status_label)}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="channel-row">', unsafe_allow_html=True)
    platform = st.radio(
        "Platform",
        options=["Zhihu", "Quora"],
        horizontal=True,
        key="platform",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if is_home:
        st.markdown(
            f'<p class="empty-hint">{html.escape(EMPTY_HINT)}</p>',
            unsafe_allow_html=True,
        )
        cols = st.columns(3, gap="small")
        for idx, (col, example) in enumerate(zip(cols, EXAMPLE_TOPICS)):
            with col:
                if st.button(example, key=f"ex_{idx}", use_container_width=True):
                    submit_topic(example)
                    st.rerun()
        render_ask_composer("home_ask")
        st.markdown(
            f'<p class="disclaimer">{html.escape(DISCLAIMER)}</p>',
            unsafe_allow_html=True,
        )
    else:
        for message in st.session_state.messages:
            render_message(message["role"], message["content"])
        render_ask_composer("chat_ask")

    if st.session_state.pending_topic:
        topic = st.session_state.pending_topic
        st.session_state.pending_topic = None
        st.session_state.messages.append({"role": "user", "content": topic})
        render_message("user", topic)

        with st.status(f"Running {platform} pipeline…", expanded=True) as status:
            try:
                if platform == "Zhihu":
                    answer = run_zhihu_pipeline(topic, status)
                else:
                    answer = run_quora_pipeline(topic, status)
                status.update(label="Done", state="complete", expanded=False)
            except Exception as e:
                answer = f"Pipeline failed: {e}\n\n{traceback.format_exc(limit=6)}"
                status.update(label="Failed", state="error", expanded=True)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        render_message("assistant", answer)


if __name__ == "__main__":
    main()
