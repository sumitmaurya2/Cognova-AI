import streamlit as st
import time
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cognova AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

/* ── Root Variables ── */
:root {
    --bg: #f2f6fb;
    --surface: #ffffff;
    --surface-2: #eef4fb;
    --border: rgba(15, 23, 42, 0.08);
    --accent: #4f46e5;
    --accent-2: #0f766e;
    --text: #102a43;
    --text-muted: #52667a;
    --success: #16a34a;
    --warning: #d97706;
    --danger: #dc2626;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: linear-gradient(180deg, #eef5fb 0%, #f7fbff 40%, #f2f6fb 100%) !important;
    overflow-x: hidden;
}

/* Animated background */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        radial-gradient(circle at 15% 15%, rgba(79, 70, 229, 0.08), transparent 22%),
        radial-gradient(circle at 85% 80%, rgba(15, 118, 110, 0.08), transparent 20%);
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.98) !important;
    border-right: 1px solid rgba(15, 23, 42, 0.08) !important;
    box-shadow: 24px 0 72px rgba(15, 23, 42, 0.06);
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}

/* ── Hero Title ── */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 4vw, 3.4rem);
    font-weight: 900;
    line-height: 1;
    margin: 0;
    letter-spacing: -0.04em;
    background: linear-gradient(135deg, #0f172a 0%, var(--accent) 70%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    color: var(--accent-2);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 0.9rem;
    margin-bottom: 0.9rem;
}

.hero-caption {
    max-width: 660px;
    font-size: 1rem;
    color: var(--text-muted);
    line-height: 1.75;
    margin-bottom: 1.4rem;
}

.hero-panel {
    position: relative;
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 32px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
}

.hero-panel::after {
    content: '';
    position: absolute;
    top: -10px;
    right: -10px;
    width: 150px;
    height: 150px;
    background: radial-gradient(circle, rgba(79, 70, 229, 0.12), transparent 45%);
    pointer-events: none;
}

.hero-panel > div {
    position: relative;
    z-index: 1;
}

.hero-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.55rem 1rem;
    border-radius: 999px;
    background: rgba(79, 70, 229, 0.1);
    color: #1f2937;
    font-weight: 600;
    font-size: 0.84rem;
    letter-spacing: 0.03em;
    border: 1px solid rgba(79, 70, 229, 0.16);
}

.hero-pill.alt { background: rgba(15,118,110,0.12); color: #0f4b5b; border-color: rgba(15,118,110,0.16); }

.sidebar-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.95rem;
    line-height: 1.05;
    margin-bottom: 0.35rem;
}

.sidebar-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    color: var(--text-muted);
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 1.25rem;
}

@keyframes glowPulse {
    0%, 100% { opacity: 1; transform: translateY(0); }
    50% { opacity: 0.8; transform: translateY(-1px); }
}

/* ── Cards ── */
.card {
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 24px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    animation: fadeInUp 0.55s ease both;
    box-shadow: 0 16px 34px rgba(15, 23, 42, 0.06);
}

.card:hover {
    transform: translateY(-3px);
    border-color: rgba(79, 70, 229, 0.28);
    box-shadow: 0 20px 42px rgba(15, 23, 42, 0.1);
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes bubbleFade {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

.chat-bubble {
    animation: bubbleFade 0.28s ease both;
}

.badge {
    display: inline-block;
    padding: 0.28rem 0.75rem;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(79, 70, 229, 0.08);
    color: var(--accent);
    border: 1px solid rgba(79, 70, 229, 0.12);
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.75rem 1.6rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    text-transform: uppercase !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 18px 24px rgba(79, 70, 229, 0.16) !important;
}

.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, rgba(79,70,229,0.95), rgba(15,118,110,0.9));
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-content {
    font-size: 0.875rem;
    line-height: 1.7;
    color: var(--text);
}

/* ── Accent Badge ── */
.badge {
    display: inline-block;
    padding: 0.28rem 0.75rem;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(92, 110, 248, 0.1);
    color: var(--accent);
    border: 1px solid rgba(92, 110, 248, 0.16);
}

.badge-purple { background: rgba(92,110,248,0.12); color: #4338ca; border: 1px solid rgba(92,110,248,0.18); }
.badge-cyan   { background: rgba(18,178,221,0.12); color: #0f766e; border: 1px solid rgba(18,178,221,0.18); }
.badge-green  { background: rgba(22,163,74,0.12); color: #166534; border: 1px solid rgba(22,163,74,0.18); }

/* ── Input & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(247, 249, 255, 0.98) !important;
    border: 1px solid rgba(15, 23, 42, 0.12) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.12) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.7rem 1.6rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    text-transform: uppercase !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 14px 32px rgba(92, 110, 248, 0.22) !important;
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
}

/* ── Progress / Status ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
    background: rgba(255,255,255,0.92);
    border-radius: 999px;
    margin: 0.5rem 0;
    border: 1px solid rgba(216,222,233,0.85);
    font-size: 0.82rem;
    box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
}

.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-active   { background: var(--accent-glow); box-shadow: 0 0 8px var(--accent-glow); animation: pulse 1.5s infinite; }
.dot-done     { background: var(--success); }
.dot-pending  { background: var(--border); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* ── Chat ── */
.chat-container {
    background: rgba(255,255,255,0.96);
    border: 1px solid rgba(216,222,233,0.95);
    border-radius: 18px;
    padding: 1.5rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.chat-msg {
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.chat-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

.chat-bubble {
    display: inline-block;
    padding: 0.6rem 1rem;
    border-radius: 10px;
    font-size: 0.85rem;
    line-height: 1.6;
    max-width: 90%;
}

.user-label  { color: var(--accent); }
.bot-label   { color: var(--accent-2); }

.user-bubble { background: rgba(92,110,248,0.12); border: 1px solid rgba(92,110,248,0.22); align-self: flex-end; }
.bot-bubble  { background: rgba(18,178,221,0.12);  border: 1px solid rgba(18,178,221,0.2);   align-self: flex-start; }

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Transcript box ── */
.transcript-box {
    background: rgba(244,246,251,0.95);
    border: 1px solid rgba(216,222,233,0.95);
    border-radius: 18px;
    padding: 1.4rem;
    font-size: 0.86rem;
    line-height: 1.8;
    max-height: 320px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
    box-shadow: inset 0 1px 1px rgba(15, 23, 42, 0.03);
}

/* ── Stale Streamlit elements ── */
.stProgress > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-muted) !important; font-size: 0.82rem !important; }

.stTextInput > div > div > input::placeholder {
    color: rgba(91,103,113,0.55) !important;
}

/* scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface-2); }
::-webkit-scrollbar-thumb { background: rgba(92,110,248,0.25); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(92,110,248,0.36); }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🤖 Cognova AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Meeting intelligence for your teams</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Input</span>', unsafe_allow_html=True)
    source = st.text_input("YouTube URL or File Path", placeholder="https://youtube.com/watch?v=... or /path/to/file.mp4")

    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    run_btn = st.button("⚡  Analyse", use_container_width=True)

    if st.session_state.pipeline_done:
        st.markdown("---")
        st.markdown('<span class="badge badge-green">Pipeline Status</span>', unsafe_allow_html=True)
        for step, icon, label in [
            ("audio",      "🔊", "Audio Processing"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Extraction"),
            ("rag",        "🧠", "RAG Engine"),
        ]:
            render_step_bar(label, step, icon)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-panel">
  <div>
    <div class="hero-title">Cognova AI</div>
    <div class="hero-sub">Transcribe · Summarise · Chat with your meetings</div>
    <div class="hero-caption">A calm, modern workspace for meeting video intelligence. Extract insights, action items, and decisions with minimal effort and maximum clarity.</div>
    <div class="hero-pill-row">
      <span class="hero-pill">AI Summary</span>
      <span class="hero-pill alt">Smart Transcript</span>
      <span class="hero-pill">Insight Cards</span>
      <span class="hero-pill alt">RAG Q&A</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("Please enter a YouTube URL or file path.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        try:
            with progress_placeholder.container():
                st.info("⚙️ Pipeline running — see sidebar for live status…")

            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"❌ Error: {e}")

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title banner
    st.markdown(f"""
    <div class="card">
        <div class="card-title">📌 Session Title</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;color:var(--text)">
            {r['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Top row: summary + transcript
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">📋 Summary</div>
            <div class="card-content">{r['summary']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    # Second row: action items | decisions | questions
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">✅ Action Items</div>
            <div class="card-content">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">🔑 Key Decisions</div>
            <div class="card-content">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">❓ Open Questions</div>
            <div class="card-content">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:1rem">💬 Chat with your Meeting</div>', unsafe_allow_html=True)

    # Chat history display
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{msg['content']}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">🤖 Cognova</span>
                    <div class="chat-bubble bot-bubble">{msg['content']}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript</div>
        </div>""", unsafe_allow_html=True)

    # Chat input
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed")
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Empty state
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5rem 2rem;text-align:center">
        <div style="font-size:4rem;margin-bottom:1rem">🎬</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.5rem">
            Ready to Analyse
        </div>
        <div style="color:var(--text-muted);font-size:0.85rem;max-width:380px;line-height:1.7">
            Paste a YouTube URL or local file path in the sidebar, choose your language, and hit <strong>Analyse</strong> to get started.
        </div>
        <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-purple">Transcription</span>
            <span class="badge badge-cyan">Summarisation</span>
            <span class="badge badge-green">RAG Chat</span>
        </div>
    </div>""", unsafe_allow_html=True)