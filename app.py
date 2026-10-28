import os

import streamlit as st
from dotenv import load_dotenv
from backend import HybridRAGBackend

st.set_page_config(
    page_title="Technical Documentation Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp { background: radial-gradient(ellipse at 85% 0%, #e9e2ff 0%, transparent 36%), radial-gradient(ellipse at 5% 85%, #ddf9f1 0%, transparent 35%), #f7f8fd; color: #252642; font-family: 'DM Sans', sans-serif; }
[data-testid="stSidebar"] { background: #171735; border-right: 0; }
[data-testid="stSidebar"] * { color: #eeeeff; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] p { color: #b9badd; }
.block-container { max-width: 1050px; padding-top: 2.4rem; padding-bottom: 5rem; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.035em; }
.hero { padding: 2rem 2.2rem; border-radius: 24px; background: linear-gradient(120deg, #30246c 0%, #6947c7 58%, #c05baa 100%); color: white; box-shadow: 0 14px 40px #5e48aa30; margin-bottom: 1.5rem; }
.hero .eyebrow { font-size: .72rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: #ded1ff; }
.hero h1 { color: white; font-size: clamp(1.8rem, 4vw, 2.8rem); line-height: 1.1; margin: .65rem 0; }
.hero p { color: #f0eaff; max-width: 620px; margin: 0; font-size: 1rem; line-height: 1.6; }
.pill { display: inline-block; margin-top: 1.2rem; padding: .4rem .7rem; border: 1px solid #ffffff50; background: #ffffff18; border-radius: 999px; font-size: .75rem; font-weight: 700; }
.sidebar-brand { font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 700; color: white; margin: .5rem 0 .2rem; }
.sidebar-label { color: #a8a7d2; font-size: .7rem; letter-spacing: .14em; font-weight: 700; text-transform: uppercase; margin-top: 2rem; }
.sidebar-card { border: 1px solid #ffffff20; background: #ffffff0c; border-radius: 16px; padding: 1rem; margin-top: .8rem; font-size: .87rem; line-height: 1.6; }
.section-label { font-size: .74rem; font-weight: 700; color: #777993; letter-spacing: .12em; text-transform: uppercase; margin: 1.4rem 0 .4rem; }
[data-testid="stChatMessage"] { border: 1px solid #e8e8f4; border-radius: 18px; background: #ffffffd9; margin: .75rem 0; box-shadow: 0 5px 18px #29245208; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { line-height: 1.7; }
[data-testid="stChatInput"] textarea { border-radius: 15px; }
.stButton > button { border-radius: 14px; border: 1px solid #e0ddf4; background: #fff; color: #443879; font-weight: 600; min-height: 3.5rem; box-shadow: 0 4px 14px #40326b0a; }
.stButton > button:hover { border-color: #8b6bea; color: #6443c1; background: #f9f6ff; }
[data-testid="stSidebar"] .stButton > button { background: #ffffff12; border: 1px solid #ffffff3a; color: white; }
[data-testid="stSidebar"] .stButton > button:hover { background: #ffffff25; border-color: #c5b4ff; }
[data-testid="stExpander"] { border: 1px solid #e9e6f5; border-radius: 12px; }
@media (max-width: 640px) { .block-container { padding-top: 1rem; } .hero { padding: 1.5rem; } }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="sidebar-brand">✦ &nbsp;Doc<span style="color:#bca9ff">verse</span></div>', unsafe_allow_html=True)
    st.caption("Your architecture knowledge companion")
    if st.button("＋  New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown('<div class="sidebar-label">Powered by</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-card">✧ &nbsp; Hybrid retrieval<br>◈ &nbsp; Vector search + knowledge graph<br>⌁ &nbsp; Traceable metadata</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">Knowledge base</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-card">🎧 &nbsp; Spotify web app architecture<br><small>Ask about the documentation and how its components fit together.</small></div>', unsafe_allow_html=True)
    st.caption("Built for curious minds & clear answers.")

st.markdown("""
<div class="hero">
  <div class="eyebrow">✦ &nbsp; Your documentation, decoded</div>
  <h1>Big questions.<br>Clearer answers.</h1>
  <p>Explore architecture, microservices and tech stacks with an assistant that connects the dots across your technical documentation.</p>
  <span class="pill">✧ &nbsp; HYBRID RAG ASSISTANT</span>
</div>
""", unsafe_allow_html=True)

if "backend" not in st.session_state:
    with st.spinner("Preparing your knowledge base..."):
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                st.error("OPENAI_API_KEY is missing from the .env file. Please check your configuration.")
                st.stop()
            backend = HybridRAGBackend(pdf_path="spotify_web_app_architecture.pdf", api_key=api_key)
            backend.initialize_pipeline()
            st.session_state["backend"] = backend
        except Exception as exc:
            st.error(f"Error during initialization: {exc}")
            st.stop()

rag_backend = st.session_state["backend"]


def show_message(message):
    avatar = "✨" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if "metadata" in message:
            with st.expander("🔍  Explore retrieval details"):
                st.json(message["metadata"])


query = None
if not st.session_state.messages:
    st.markdown('<div class="section-label">A little inspiration</div>', unsafe_allow_html=True)
    st.markdown("**Not sure where to start?** Try one of these questions:")
    examples = [
        "How is the application architecture structured?",
        "What microservices are used in the system?",
        "What technologies make up the tech stack?",
    ]
    columns = st.columns(3)
    for column, example in zip(columns, examples):
        with column:
            if st.button(example, use_container_width=True):
                query = example
else:
    st.markdown('<div class="section-label">Your conversation</div>', unsafe_allow_html=True)
    for message in st.session_state.messages:
        show_message(message)

chat_query = st.chat_input("Ask anything about your technical documentation...")
query = chat_query or query
if query:
    user_message = {"role": "user", "content": query}
    st.session_state.messages.append(user_message)
    show_message(user_message)
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Connecting the dots across your documentation..."):
            try:
                response_data = rag_backend.generate_answer(query)
                answer = response_data["answer"]
                metadata = response_data["metadata"]
                st.markdown(answer)
                with st.expander("🔍  Explore retrieval details"):
                    st.json(metadata)
                st.session_state.messages.append({"role": "assistant", "content": answer, "metadata": metadata})
            except Exception as exc:
                st.error(f"Sorry, I couldn't answer that question: {exc}")
