from flask import Flask, render_template, request, jsonify, session
import os
import json
import uuid
import io
import base64
import re
import asyncio
import requests
import secrets

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pypdf import PdfReader

import edge_tts

from fpdf import FPDF

from prompt_builder import build_prompt
from ai_image_generator import generate_ai_image


# ==========================
# ENVIRONMENT
# ==========================

load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]

PIXABAY_API_KEY = os.environ["PIXABAY_API_KEY"]


# ==========================
# FLASK
# ==========================

app = Flask(__name__)

app.secret_key = "replace_this_with_a_long_random_secret_string"

app.config["SESSION_PERMANENT"] = True

app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 365


# ==========================
# USER ID SYSTEM
# ==========================

@app.before_request
def create_user():

    user_id = request.headers.get("X-User-ID")

    if user_id:
        session["user_id"] = user_id


# ==========================
# CHAT STORAGE
# ==========================

CHAT_FOLDER = "chat_history"

os.makedirs(CHAT_FOLDER, exist_ok=True)



def get_user_folder():

    user_id = session.get("user_id")

    if not user_id:
        user_id = secrets.token_hex(16)
        session["user_id"] = user_id


    folder = os.path.join(
        CHAT_FOLDER,
        user_id
    )


    os.makedirs(
        folder,
        exist_ok=True
    )

    return folder



def get_chat_file():

    if "current_chat" not in session:

        session["current_chat"] = str(
            uuid.uuid4()
        )


    return os.path.join(
        get_user_folder(),
        session["current_chat"] + ".json"
    )



# ==========================
# SAVE CHAT
# ==========================


def save_chat():

    file_path = get_chat_file()


    data = {

        "title":
        session.get(
            "current_chat_title",
            "New Chat"
        ),


        "messages":
        session.get(
            "conversation_history",
            []
        )

    }



    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


    print(
        "CHAT SAVED:",
        file_path
    )



# ==========================
# HOME
# ==========================


@app.route("/")
def home():

    return render_template(
        "index.html"
    )

# ==========================
# PDF CREATOR
# ==========================

def create_pdf(text):

    filename = "groom_ai_file.pdf"

    os.makedirs(
        "static",
        exist_ok=True
    )

    path = os.path.join(
        "static",
        filename
    )


    # Remove unsupported characters
    text = text.replace("\r", "")


    pdf = FPDF()

    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()

    pdf.set_font("Helvetica", size=12)

    for line in text.split("\n"):

        line = line.strip()

        if line:

            pdf.multi_cell(
                w=190,
                h=8,
                text=line
            )

    pdf.output(path)


    return "/" + path



# ==========================
# WEB SEARCH
# ==========================

def web_search(query):

    url = "https://html.duckduckgo.com/html/"


    headers = {

        "User-Agent":
        "Mozilla/5.0"

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


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        results = []


        for item in soup.select(".result")[:5]:


            title = item.select_one(
                ".result__title"
            )


            snippet = item.select_one(
                ".result__snippet"
            )


            results.append(

                f"{title.get_text(' ', strip=True) if title else ''}\n"
                f"{snippet.get_text(' ', strip=True) if snippet else ''}"

            )


        return "\n\n".join(results)


    except Exception as e:

        return "Search Error: " + str(e)




# ==========================
# IMAGE QUERY CLEANER
# ==========================

def clean_image_query(text):

    text = text.lower()


    remove_words = [

        "show me",
        "show",
        "give me",
        "image of",
        "images of",
        "picture of",
        "pictures of",
        "photo of",
        "photos of"

    ]


    for word in remove_words:

        text = text.replace(
            word,
            ""
        )


    return text.strip()




# ==========================
# PIXABAY IMAGE SEARCH
# ==========================

def image_search(query):

    url = "https://pixabay.com/api/"


    params = {

        "key":
        PIXABAY_API_KEY,


        "q":
        query,


        "image_type":
        "photo",


        "per_page":
        4,


        "safesearch":
        "true"

    }



    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )


        data = response.json()


        images = []


        for item in data.get(
            "hits",
            []
        ):

            images.append(
                item["webformatURL"]
            )


        return images


    except Exception:

        return []





# ==========================
# SYSTEM PROMPT
# ==========================

with open(
    "system_prompt.txt",
    "r",
    encoding="utf-8"
) as f:

    SYSTEM_PROMPT = f.read()



# ==========================
# GEMINI API
# ==========================

GEMINI_URL = (

    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-3.5-flash-lite:generateContent"
    f"?key={API_KEY}"

)

# ==========================
# CHAT ROUTE
# ==========================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.json

    user_message = data.get("message", "")
    image = data.get("image")
    pdf = data.get("pdf")

    print("MESSAGE:", user_message)

    conversation_history = session.get("conversation_history", [])

    # Create new chat
    if "current_chat" not in session:
        session["current_chat"] = str(uuid.uuid4())

    # First message becomes title
    if len(conversation_history) == 0:
        session["current_chat_title"] = user_message[:40]

    conversation_history.append({
        "role": "user",
        "text": user_message
    })

    session["conversation_history"] = conversation_history
    session.modified = True
    save_chat()

    # -----------------------------
    # BUILD PROMPT
    # -----------------------------

    recent_history = conversation_history[-10:]

    history_text = ""

    for msg in recent_history:
        history_text += msg["role"] + ": " + msg["text"] + "\n"

    prompt = (
        SYSTEM_PROMPT
        +
        """

You are Groom AI.

PDF RULES:

If user asks for PDF,
give the content normally.

The application will create PDF.

Never say:
"I cannot create PDF."

IMAGE RULES:

Never say:
"I cannot show images."

Images are handled by the application.

"""
        +
        "\nConversation:\n"
        +
        history_text
        +
        "\nUser: "
        +
        user_message
    )

    # -----------------------------
    # PDF PROCESS
    # -----------------------------

    if pdf:

        try:

            header, pdf_data = pdf.split(",", 1)

            pdf_bytes = base64.b64decode(pdf_data)

            reader = PdfReader(io.BytesIO(pdf_bytes))

            pdf_text = ""

            for page in reader.pages:

                txt = page.extract_text()

                if txt:
                    pdf_text += txt

            prompt += "\nPDF CONTENT:\n" + pdf_text

        except Exception as e:

            print("PDF ERROR:", e)

    # -----------------------------
    # CREATE PARTS
    # -----------------------------

    parts = [
        {
            "text": prompt
        }
    ]

    # -----------------------------
    # IMAGE PROCESS
    # -----------------------------

    if image:

        try:

            header, img_data = image.split(",", 1)

            mime = header.split(";")[0].split(":")[1]

            parts.append({

                "inline_data": {

                    "mime_type": mime,

                    "data": img_data

                }

            })

        except Exception as e:

            print("IMAGE ERROR:", e)

    # -----------------------------
    # GEMINI PAYLOAD
    # -----------------------------

    payload = {

        "contents": [

            {

                "parts": parts

            }

        ]

    }

    # -----------------------------
    # GEMINI REQUEST
    # -----------------------------

    try:

        response = requests.post(

            GEMINI_URL,

            json=payload,

            timeout=60

        )

        response.raise_for_status()

    except Exception as e:

        return jsonify({

            "reply": "⚠️ Gemini Error: " + str(e),

            "images": []

        })

    result = response.json()

    print(result)

    # -----------------------------
    # GET REPLY
    # -----------------------------

    try:

        reply = result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:

        print("REPLY ERROR:", e)

        return jsonify({

            "reply": "⚠️ No response from Gemini",

            "images": [],

            "pdf": None

        })

    # -----------------------------
    # PDF CREATION
    # -----------------------------

    pdf_link = None

    pdf_words = [

        "pdf",
        "make pdf",
        "create pdf",
        "send pdf",
        "download pdf"

    ]

    if any(word in user_message.lower() for word in pdf_words):

        try:

            pdf_link = create_pdf(reply)

        except Exception as e:

            print("PDF ERROR:", e)

    # -----------------------------
    # IMAGE SEARCH / AI IMAGE
    # -----------------------------

    images = []

    image_words = [

        "image",
        "images",
        "photo",
        "picture",
        "show me",
        "wallpaper",
        "logo"

    ]

    if any(word in user_message.lower() for word in image_words):

        try:

            query = clean_image_query(user_message)

            ai_image = generate_ai_image(query)

            images = [ai_image]

        except Exception as e:

            print("AI IMAGE FAILED:", e)

            images = image_search(clean_image_query(user_message))

    # -----------------------------
    # SAVE AI MESSAGE
    # -----------------------------

    conversation_history = session.get("conversation_history", [])

    conversation_history.append({

        "role": "assistant",

        "text": reply

    })

    session["conversation_history"] = conversation_history

    save_chat()

    print("FINAL RESPONSE SENT")

    return jsonify({

        "reply": reply,

        "images": images,

        "pdf": pdf_link

    })


# ==========================
# CHAT LIST
# ==========================

@app.route("/chat_list")
def chat_list():

    folder = get_user_folder()

    chats = []

    if not os.path.exists(folder):
        return jsonify([])

    for file in os.listdir(folder):

        if file.endswith(".json"):

            path = os.path.join(folder, file)

            try:

                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                chats.append({
                    "id": file,
                    "title": data.get("title", "New Chat")
                })

            except Exception as e:

                print("CHAT LIST ERROR:", e)

    chats.reverse()

    return jsonify(chats)


# ==========================
# LOAD CHAT
# ==========================

@app.route("/load_chat/<chat_id>")
def load_chat(chat_id):


    path = os.path.join(
        get_user_folder(),
        chat_id
    )


    if not os.path.exists(path):

        return jsonify([])



    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)



        session["conversation_history"] = (
            data.get(
                "messages",
                []
            )
        )


        session["current_chat"] = (
            chat_id.replace(
                ".json",
                ""
            )
        )


        session["current_chat_title"] = (
            data.get(
                "title",
                "New Chat"
            )
        )



        return jsonify(
            data.get(
                "messages",
                []
            )
        )


    except Exception as e:


        print(
            "LOAD ERROR:",
            e
        )


        return jsonify([])

# ==========================
# DELETE CHAT
# ==========================

@app.route(
    "/delete_chat/<chat_id>",
    methods=["POST"]
)

def delete_chat(chat_id):


    path = os.path.join(
        get_user_folder(),
        chat_id
    )


    if os.path.exists(path):

        os.remove(path)



    if session.get(
        "current_chat"
    ) == chat_id.replace(
        ".json",
        ""
    ):


        session["conversation_history"] = []

        session["current_chat"] = str(
            uuid.uuid4()
        )

        session["current_chat_title"] = (
            "New Chat"
        )



    return jsonify({

        "success": True

    })

# ==========================
# NEW CHAT
# ==========================

@app.route(
    "/new_chat",
    methods=["POST"]
)

def new_chat():


    session["conversation_history"] = []


    session["current_chat"] = str(
        uuid.uuid4()
    )


    session["current_chat_title"] = (
        "New Chat"
    )


    return jsonify({

        "success": True

    })

# ==========================
# VOICE
# ==========================

@app.route(
    "/voice",
    methods=["POST"]
)

def voice():

    text = request.json.get(
        "text"
    )


    if not text:

        return jsonify({

            "error":
            "No text"

        })



    async def generate():


        communicate = edge_tts.Communicate(

            text,

            "en-US-AriaNeural"

        )


        audio = io.BytesIO()



        async for chunk in communicate.stream():


            if chunk["type"] == "audio":

                audio.write(
                    chunk["data"]
                )


        audio.seek(0)


        return audio



    audio = asyncio.run(
        generate()
    )



    return app.response_class(

        audio.read(),

        mimetype="audio/mpeg"

    )

if __name__ == "__main__":
    app.run(debug=True)
