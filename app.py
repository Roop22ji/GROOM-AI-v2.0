from flask import Flask, render_template, request, jsonify, session
import requests
import secrets
from duckduckgo_search import DDGS
import time
import re
import io
from pypdf import PdfReader
import base64
from prompt_builder import build_prompt
import os
import json
import uuid

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]


def web_search(query):

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    data = {
        "q": query
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=10
        )

        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        for item in soup.select(".result")[:5]:

            title = item.select_one(".result__title")

            snippet = item.select_one(".result__snippet")

            link = item.select_one(".result__url")

            results.append(
                f"Title: {title.get_text(' ', strip=True) if title else 'No title'}\n"
                f"Body: {snippet.get_text(' ', strip=True) if snippet else 'No description'}\n"
                f"URL: {link.get_text(' ', strip=True) if link else 'No URL'}"
            )

        return "\n\n".join(results)

    except Exception as e:

        return f"Search Error: {e}"

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

app = Flask(__name__)
app.secret_key = "replace_this_with_a_long_random_secret_string"

@app.before_request
def create_user():

    if "user_id" not in session:
        session["user_id"] = secrets.token_hex(16)

# ==========================
# Conversation Memory
# ==========================

CHAT_FOLDER = "chat_history"
os.makedirs(CHAT_FOLDER, exist_ok=True)


def get_user_folder():

    folder = os.path.join(CHAT_FOLDER, session["user_id"])
    os.makedirs(folder, exist_ok=True)
    return folder


def get_chat_file():

    if "current_chat" not in session:
        session["current_chat"] = str(uuid.uuid4())

    return os.path.join(
        get_user_folder(),
        session["current_chat"] + ".json"
    )

# ==========================
# SAVE CHAT
# ==========================

def save_chat():

    file_path = get_chat_file()

    conversation = session.get("conversation_history", [])

    title = session.get("current_chat_title", "New Chat")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "title": title,
                "messages": conversation,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )



URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={API_KEY}"



@app.route("/")
def home():
    return render_template("index.html")




@app.route("/chat", methods=["POST"])
def chat():

    data = request.json

    user_message = data.get("message", "")
    image = data.get("image")
    pdf = data.get("pdf")

    print("Message:", user_message)

    if image:
        print("✅ Image received")
    else:
        print("❌ No image")

    conversation_history = session.get("conversation_history", [])

    if len(conversation_history) == 0:
        session["current_chat_title"] = user_message[:40]

    conversation_history.append({
        "role": "user",
        "text": user_message,
        "image": image,
        "pdf": pdf
    })

    session["conversation_history"] = conversation_history

    user_message = build_prompt(user_message)
    

    # --------------------------
    # Smart Web Search
    # --------------------------

    web_results = ""

    SEARCH_KEYWORDS = [
    "latest",
    "today",
    "current",
    "news",
    "live",
    "price",
    "weather",
    "score",
    "recent",
    "update",
    "who is",
    "what is",
    "where is",
    "when",
    "2026",
    "2025",
    "yesterday",
    "tomorrow",
    "release",
    "launch",
    "breaking"
]

    web_results = ""

    if any(k in user_message.lower() for k in SEARCH_KEYWORDS):

        print("🌐 Searching the web...")

        web_results = web_search(user_message)

    # Keep only the last 10 messages
    recent_history = conversation_history[-10:]
    last_image = None

    for msg in reversed(recent_history):
        if msg["role"] == "user" and msg.get("image"):
            last_image = msg["image"]
            break

    # If the current message has no image,
    # reuse the most recent uploaded image.
    if not image:
        image = last_image

    conversation_text = ""

    for msg in recent_history:

        if msg["role"] == "user":
            conversation_text += f"User: {msg['text']}\n"
        else:
            conversation_text += f"Assistant: {msg['text']}\n"


    # --------------------------
    # Process Image
    # --------------------------

    image_encoded = None
    mime_type = None

    if image:

        header, image_encoded = image.split(",", 1)

        mime_type = header.split(";")[0].split(":")[1]


    # --------------------------
    # Process PDF
    # --------------------------

    pdf_text = ""

    if pdf:

        header, pdf_encoded = pdf.split(",", 1)

        pdf_bytes = base64.b64decode(pdf_encoded)

        reader = PdfReader(io.BytesIO(pdf_bytes))

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pdf_text += text + "\n"
    



    web_results = ""

    SEARCH_KEYWORDS = [
        "latest",
        "today",
        "current",
        "news",
        "live",
        "price",
        "weather",
        "score",
        "recent",
        "update"
    ]

    if any(word in user_message.lower() for word in SEARCH_KEYWORDS):
        print("🌐 Searching...")
        web_results = web_search(user_message)
        print(web_results)

    # --------------------------
    # Build Prompt
    # --------------------------

    prompt = (
        SYSTEM_PROMPT
        + "\n\nConversation History:\n"
        + conversation_text
    )

    # Add PDF
    if pdf_text:
        prompt += "\n\nPDF Content:\n"
        prompt += pdf_text

    # Add Web Search
    if web_results:

        prompt += """

    IMPORTANT:

    The information below comes from a live web search.

    You MUST use these search results to answer the user's question.

    Do NOT say you don't have internet access.

    If the answer exists in the search results, use it.

    =========================
    LIVE WEB SEARCH RESULTS
    =========================

    """

        prompt += web_results

        prompt += """

    =========================
    END OF SEARCH RESULTS
    =========================

    """

    # User question
    prompt += "\n\nUser: " + user_message

    # Build Gemini parts
    parts = [
        {
            "text": prompt
        }
    ]

    # Add image if available
    if image_encoded:

        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_encoded
            }
        })

    # Build payload
    payload = {
        "contents": [
            {
                "parts": parts
            }
        ]
    }



    import time

    start = time.time()

    try:
        response = requests.post(URL, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return jsonify({
            "reply": "⚠️ GROOM AI is taking longer than expected. Please try again."
        })
    except Exception as e:
        return jsonify({
            "reply": f"⚠️ Error: {e}"
        })

    print("API Response Time:", round(time.time() - start, 2), "seconds")
    if response.status_code == 200:
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]

        # Remove LaTeX formatting
        reply = re.sub(r"\$(.*?)\$", r"\1", reply)

        reply = reply.replace("\\vec{", "")
        reply = reply.replace("\\Delta", "Delta ")
        reply = reply.replace("\\approx", "≈")
        reply = reply.replace("\\text{", "")
        reply = reply.replace("\\frac{", "")
        reply = reply.replace("\\left", "")
        reply = reply.replace("\\right", "")
        reply = reply.replace("{", "")
        reply = reply.replace("}", "")

        print("Sending JSON:", {"reply": reply})

        # Save AI reply
        # Save AI reply
        conversation_history = session.get("conversation_history", [])

        conversation_history.append({
            "role": "assistant",
            "text": reply
        })

        session["conversation_history"] = conversation_history

        save_chat()



        return jsonify({"reply": reply})
    else:
        return jsonify({"reply": response.text})


# ==========================
# GET CHAT LIST
# ==========================

@app.route("/chat_list")
def chat_list():

    user_folder = get_user_folder()

    chats = []

    if not os.path.exists(user_folder):
        return jsonify([])

    for file in os.listdir(user_folder):

        if file.endswith(".json"):

            path = os.path.join(user_folder, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                chats.append({
                    "id": file,
                    "title": data.get("title", "New Chat")
                })

            except:
                chats.append({
                    "id": file,
                    "title": file.replace(".json", "")
                })

    chats.reverse()

    return jsonify(chats)

# ==========================
# LOAD CHAT
# ==========================

@app.route("/load_chat/<chat_id>")
def load_chat(chat_id):

    path = os.path.join(get_user_folder(), chat_id)

    if not os.path.exists(path):
        return jsonify([])

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    session["conversation_history"] = data["messages"]
    session["current_chat"] = chat_id.replace(".json", "")
    session["current_chat_title"] = data.get("title", "New Chat")

    return jsonify(data["messages"])


@app.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat(chat_id):

    path = os.path.join(get_user_folder(), chat_id)

    if os.path.exists(path):
        os.remove(path)

    # If the deleted chat is currently open, reset the session
    if session.get("current_chat") == chat_id.replace(".json", ""):
        session["conversation_history"] = []
        session["current_chat"] = str(uuid.uuid4())
        session["current_chat_title"] = "New Chat"

    return jsonify({"success": True})

# ==========================
# NEW CHAT
# ==========================

@app.route("/new_chat", methods=["POST"])
def new_chat():

    session["conversation_history"] = []
    session["current_chat"] = str(uuid.uuid4())
    session["current_chat_title"] = "New Chat"

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)