import streamlit as st
import re
import json
import os
from datetime import datetime
from OllamaClient import OllamaClient

# --- Page config ---
st.set_page_config(page_title="OCC", layout="centered",page_icon="image/favicon.ico")
st.sidebar.image("image/occ-icon-1.png",width=500)
logocol1,logocol2,logocol3=st.columns([1,2,1])
logocol2.image("image/Kem Palty.png")
# logocol2.title("Kem Palty!!")
st.markdown(
    """
    <style>
    .st-key-regen {
        margin-left:80%;
        color:#999;
    }
    .st-key-cleanup,.st-key-export{
        color:#2badb8!important;
        
    }
    button[data-testid="stBaseButton-secondary"]{
        border:none;background:transparent;
    }
    button[data-testid="stBaseButton-secondary"]:hover{
        background:transparent;
    }
    </style>
    """,
    unsafe_allow_html=True
)
SAVE_DIR = "conversations"
UPLOAD_DIR = "uploads"
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## :material/settings_applications: Ollama Settings")

    # Connection
    with st.expander(":material/cable: Connection", expanded=False):
        base_url = st.text_input("Ollama Base URL", value="http://localhost:11434")
        auto_check = st.checkbox("Auto-check server on load", value=True)
        client = OllamaClient(base_url)
        server_ok = client.check_server() if auto_check else False
        if server_ok:
            st.success("✅ Ollama reachable")
        else:
            st.warning("⚠️ Cannot reach Ollama server")

    # Model & Prompt
    with st.expander(":material/robot_2: Model", expanded=False):
        models = client.list_models() if server_ok else []
        model_choices = [m.get("name") if isinstance(m, dict) else str(m) for m in models]
        selected_model = st.selectbox("Select Model", model_choices) if model_choices else st.text_input("Model (manual)", value="gemma3:1b")

        temperature = st.slider("Temperature", 0.0, 1.0, 0.2, step=0.05)
        max_tokens = st.number_input("Max Tokens", min_value=16, max_value=128000, value=512, step=16)
        stream_output = st.checkbox("Stream Output", value=True)
        system_prompt = st.text_area("System Prompt", value="You are a helpful assistant.", height=100)

        template = st.selectbox(
            "Quick Insert Template",
            ["", "Summarize this text", "Explain like I'm 5", "Translate to French", "Explain this code",
             "Debug this code", "Optimize this code", "Convert to another language", "Generate unit tests",
             "Document this function", "Refactor this code", "Rewrite professionally", "Generate email reply",
             "Write blog post outline", "Create social media post", "Generate business plan summary",
             "Analyze this dataset", "Create presentation outline", "Draft meeting notes", "SWOT analysis",
             "Generate SQL query", "Create Python script for [task]", "Visualize data", "Brainstorm ideas",
             "Write story/poem", "Generate dialogue for scene", "Design UX flow", "Explain error message",
             "Optimize system command", "Suggest CI/CD pipeline"]
        )
        if template:
            st.session_state.template = template

        if st.button("Refresh", help="Refresh Models", icon=":material/refresh:"):
            client.list_models()
            st.rerun()

    # Chat Controls
    btncol1, btncol2 = st.columns([1,1])
    if btncol1.button("Clean", key="cleanup", help='Clean history', icon=":material/delete_forever:"):
        st.session_state.history = []
        st.rerun()
    if btncol2.button("Export",key="export",help='Export conversation', icon=":material/download:"):
        if st.session_state.history:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(SAVE_DIR, f"chat_{ts}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(st.session_state.history, f, indent=2, ensure_ascii=False)
            st.success(f"Exported to {file_path}")
        else:
            st.info("No conversation to export.")

    st.divider()
    st.markdown(
        """
        <div style="text-align: center; color: #888;">
            <p>
                Made with ❤️ by <strong>Rahul Dubey</strong>
            </p>
            <p>
            <a href="https://github.com/d-evil0per/snapflip" target="_blank" style="color: #117a65; text-decoration: none;">
                    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" width="20" style="vertical-align: middle; margin-right: 5px;">
                    GitHub
                </a>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Session state ---
if "history" not in st.session_state:
    st.session_state.history = []
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
if "template" not in st.session_state:
    st.session_state.template = ""

# --- Helper: render assistant messages ---
def render_assistant_message(text: str):
    code_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
    last_end = 0
    for match in code_pattern.finditer(text):
        before = text[last_end:match.start()]
        if before.strip():
            st.markdown(before)
        lang = match.group(1) or "text"
        code = match.group(2)
        st.code(code.strip(), language=lang)
        st.caption(f"Detected language: {lang}")
        last_end = match.end()
    after = text[last_end:]
    if after.strip():
        st.markdown(after)

# --- Display chat history ---
for msg in st.session_state.history:
    with st.chat_message(msg["role"], avatar="👻" if msg["role"]=="assistant" else ":material/face:"):
        if msg.get("content"):
            st.markdown(msg["content"])
        if msg.get("files"):
            for f in msg["files"]:
                if f["type"].startswith("image/"):
                    st.image(f["path"], caption=f["name"])
                else:
                    st.download_button(f"Download {f['name']}", data=open(f["path"], "rb"), file_name=f["name"])

# --- Chat input with file upload ---
chat_value = st.chat_input("Type your message...", key="chat_input", accept_file=True,file_type=["jpg", "jpeg", "png"])

if chat_value:
    user_text = chat_value.text or ""
    uploaded_files = chat_value.files or []

    # Apply template
    if st.session_state.template and user_text:
        user_text = f"{st.session_state.template}: {user_text}"
        st.session_state.template = ""

    entry = {"role": "user", "content": user_text, "files": []}

    # Save files
    for f in uploaded_files:
        save_path = os.path.join(UPLOAD_DIR, f.name)
        with open(save_path, "wb") as out_file:
            out_file.write(f.getbuffer())
        entry["files"].append({"name": f.name, "type": f.type, "path": save_path})

        # Include file info in prompt text
        user_text += f"\n\n[File: {f.name}, type: {f.type}]"

    st.session_state.history.append(entry)
    st.session_state.last_prompt = user_text

    with st.chat_message("user", avatar=":material/face:"):
        st.markdown(entry["content"])
        for f in entry["files"]:
            if f["type"].startswith("image/"):
                st.image(f["path"], caption=f["name"])
            else:
                st.download_button(f"Download {f['name']}", data=open(f["path"], "rb"), file_name=f["name"])

    # Assistant response
    with st.chat_message("assistant", avatar="👻"):
        if stream_output:
            message_placeholder = st.empty()
            collected = ""
            with st.spinner("Generating (streaming)..."):
                try:
                    for chunk in client.generate_stream(selected_model, f"{system_prompt}\n\n{user_text}", temperature, max_tokens):
                        collected += chunk
                        message_placeholder.markdown(collected + "▌")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            message_placeholder.empty()
            with message_placeholder.container():
                render_assistant_message(collected)
            st.session_state.history.append({"role": "assistant", "content": collected})
        else:
            with st.spinner("Generating..."):
                try:
                    resp = client.generate_non_stream(selected_model, f"{system_prompt}\n\n{user_text}", temperature, max_tokens)
                    reply = resp.get("response") or resp.get("text") or str(resp)
                except Exception as e:
                    reply = f"❌ Error: {e}"
            render_assistant_message(reply)
            st.session_state.history.append({"role": "assistant", "content": reply})

# --- Regenerate last response ---
if st.session_state.last_prompt and st.button(":material/autorenew: Regenerate",key="regen", help="Regenerate last response"):
    last_prompt = st.session_state.last_prompt
    st.session_state.history.append({"role": "user", "content": last_prompt})
    with st.chat_message("user", avatar=":material/face:"):
        st.markdown(last_prompt)

    with st.chat_message("assistant", avatar="👻"):
        with st.spinner("Regenerating..."):
            try:
                resp = client.generate_non_stream(selected_model, f"{system_prompt}\n\n{last_prompt}", temperature, max_tokens)
                reply = resp.get("response") or resp.get("text") or str(resp)
            except Exception as e:
                reply = f"❌ Error: {e}"
        render_assistant_message(reply)
        st.session_state.history.append({"role": "assistant", "content": reply})
