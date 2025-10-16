import os
from dotenv import load_dotenv
import gradio as gr
import uuid
import requests
import re

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

API_URL = "http://18.142.237.65:8000/agentic/v1/chat/"
TOKENS_URL = "http://18.142.237.65:8000/agentic/v1/chat/tokens"

USERNAME = os.getenv("APP_USERNAME", "admin")
PASSWORD = os.getenv("APP_PASSWORD", "1234")

# 🔐 Load API Key from environment (must match FastAPI backend)
API_KEY = os.getenv("API_KEY", "super-secret-api-key")
API_KEY_HEADER = {"X-API-Key": API_KEY}

# ---------------------------
# Helper Functions
# ---------------------------

def generate_session_id():
    """Generate a unique session ID for each user."""
    return str(uuid.uuid4())

def format_blocks(raw_text: str) -> str:
    """Format streaming assistant messages with tool calls/results."""
    blocks = re.split(r'(\[TOOL CALL\]|\[TOOL RESULT\]|\[ASSISTANT\])', raw_text)
    formatted = ""
    i = 0
    while i < len(blocks):
        block = blocks[i]
        if block in ["[TOOL CALL]", "[TOOL RESULT]", "[ASSISTANT]"]:
            current_block = block
            i += 1
            content = blocks[i] if i < len(blocks) else ""
            i += 1

            if current_block == "[TOOL CALL]":
                formatted += f"### 🔧 Tool Call\n```\n{content.strip()}\n```\n"
            elif current_block == "[TOOL RESULT]":
                formatted += f"### 🧾 Tool Result\n```\n{content.strip()}\n```\n"
            elif current_block == "[ASSISTANT]":
                formatted += f"### 🤖 Assistant\n{content.strip()}\n"
        else:
            i += 1
    return formatted

def stream_from_api(user_input: str, session_id: str):
    """Stream assistant response from API in real-time."""
    headers = {"Accept": "text/plain", **API_KEY_HEADER}
    params = {"user_query": user_input, "session_id": session_id}

    assistant_msg = ""
    with requests.post(API_URL, params=params, stream=True, headers=headers) as response:
        if response.status_code == 401:
            yield "🚫 **Unauthorized** – Invalid API key."
            return
        for chunk in response.iter_content(chunk_size=1024):
            if not chunk:
                continue
            partial = chunk.decode("utf-8")
            assistant_msg += partial
            yield format_blocks(assistant_msg)

def fetch_latest_token(session_id: str):
    """Fetch latest token count from API for this session."""
    try:
        headers = {**API_KEY_HEADER}
        resp = requests.get(TOKENS_URL, params={"session_id": session_id}, headers=headers)
        if resp.status_code == 401:
            return 0
        data = resp.json()
        return int(data.get("tokens", 0))
    except Exception:
        return 0

# ---------------------------
# Gradio Functions
# ---------------------------

def init_session():
    """Initialize session ID and token counters on page load."""
    new_id = generate_session_id()
    return new_id, f"**Session ID:** `{new_id}`", 0, 0  # session_id, display, total_token, latest_token

def send_message(msg, history, session_id, total_token):
    """Append user message to chat history."""
    history.append((msg, ""))
    return history, "", session_id, total_token

def update_chat(history, session_id, total_token):
    """Stream assistant responses and update tokens."""
    if not history:
        return history, total_token, 0

    user_msg = history[-1][0]
    assistant_msg = ""
    # Stream API response
    for partial in stream_from_api(user_msg, session_id):
        assistant_msg = partial
        history[-1] = (user_msg, assistant_msg)
        yield history, total_token, 0  # latest token not known yet

    # Fetch latest token after response
    latest_token = fetch_latest_token(session_id)
    total_token += latest_token
    yield history, total_token, latest_token

def display_tokens(total, latest):
    """Return string to display cumulative and latest tokens."""
    return f"**Total Tokens:** {total} | **Latest Token:** {latest}"

# ---------------------------
# Gradio UI
# ---------------------------

with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Agentic Fraud Chatbot (via API)")

    # Session ID
    session_id_state = gr.State()
    session_display = gr.Markdown("")

    # Tokens
    total_token_state = gr.State()
    latest_token_state = gr.State()
    token_display = gr.Markdown("**Total Tokens:** 0 | **Latest Token:** 0")

    # Chatbot
    chatbot = gr.Chatbot()
    user_input = gr.Textbox(placeholder="Ask me about fraud transactions...")
    send_button = gr.Button("Send")

    # Initialize session on page load
    demo.load(
        fn=init_session,
        inputs=[],
        outputs=[session_id_state, session_display, total_token_state, latest_token_state]
    )

    # Send message and stream response
    send_button.click(
        send_message,
        [user_input, chatbot, session_id_state, total_token_state],
        [chatbot, user_input, session_id_state, total_token_state]
    ).then(
        update_chat,
        [chatbot, session_id_state, total_token_state],
        [chatbot, total_token_state, latest_token_state]
    ).then(
        display_tokens,
        [total_token_state, latest_token_state],
        token_display
    )

demo.launch(
    auth=(USERNAME, PASSWORD),
    server_name="0.0.0.0",
    server_port=7860,
    show_error=True,
    share=False
)
