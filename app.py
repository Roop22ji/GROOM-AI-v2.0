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
import time

from flask_socketio import SocketIO, emit
import websockets


from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pypdf import PdfReader

import edge_tts

from fpdf import FPDF

from prompt_builder import build_prompt
from ai_image_generator import generate_ai_image
from deepgram import DeepgramClient

import os
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

print("Deepgram key loaded:", bool(DEEPGRAM_API_KEY))

# ==========================
# ENVIRONMENT
# ==========================

load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]

print("Gemini key loaded:", bool(GEMINI_API_KEY))

PIXABAY_API_KEY = os.environ["PIXABAY_API_KEY"]


# ==========================
# FLASK
# ==========================

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")

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

# ==========================
# MEMORY SYSTEM
# ==========================

MEMORY_FOLDER = "memory"

os.makedirs(
    MEMORY_FOLDER,
    exist_ok=True
)


def get_memory_file():

    user_id = session.get("user_id")

    if not user_id:
        user_id = secrets.token_hex(16)
        session["user_id"] = user_id


    folder = os.path.join(
        MEMORY_FOLDER,
        user_id
    )

    os.makedirs(
        folder,
        exist_ok=True
    )


    return os.path.join(
        folder,
        "memory.json"
    )



def load_memory():

    file = get_memory_file()


    if os.path.exists(file):

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)


    return {
        "facts": [],
        "preferences": [],
        "projects": []
    }



def save_memory(memory):

    file = get_memory_file()


    with open(
        file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            memory,
            f,
            indent=4
        )

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
# WEB SEARCH API
# ==========================

@app.route("/web_search", methods=["POST"])
def web_search_route():

    try:

        data = request.get_json(silent=True) or {}

        query = data.get("query", "").strip()

        if not query:

            return jsonify({
                "success": False,
                "reply": "Please enter something to search."
            }), 400

        print()
        print("================================")
        print("🌐 WEB SEARCH:", query)
        print("================================")

        # --------------------------------
        # SEARCH INTERNET
        # --------------------------------

        results = web_search(query)

        if not results:

            return jsonify({
                "success": False,
                "reply": "I couldn't find any web results."
            }), 200

        # --------------------------------
        # FORMAT RESULTS FOR GEMINI
        # --------------------------------

        web_text = ""

        for i, result in enumerate(results, 1):

            web_text += f"""
SOURCE {i}

TITLE:
{result["title"]}

DESCRIPTION:
{result["snippet"]}

URL:
{result["url"]}

-------------------------
"""

        # --------------------------------
        # GEMINI PROMPT
        # --------------------------------

        prompt = f"""
You are GROOM AI.

The server performed a live internet search for the user.

USER QUERY:
{query}

SEARCH RESULTS:
{web_text}

Your job is to answer the user's query using the search results.

IMPORTANT RULES:

1. Use the search results as your evidence.

2. If the user asks for "latest", "today", "recent",
   "current", "this week", or similar, prioritize
   results that appear to be recent.

3. For news questions, report the actual headlines
   and facts contained in the search results.

4. Do NOT replace missing information with generic
   suggestions such as:
   "Check Reuters",
   "Check TechCrunch",
   "Check AI Weekly",
   or "You can find more information online."

5. Do NOT say:
   "I don't have real-time browsing."

6. Do NOT say:
   "I cannot browse the internet."

7. Do NOT pretend that you personally visited
   the websites.

8. Do NOT invent headlines, dates, people, companies,
   events, or facts.

9. If the search results genuinely do not contain
   enough information to answer the question,
   explicitly say:
   "The search results did not contain enough
   information to answer this reliably."

10. When possible, organize news as:

   • Headline
   • What happened
   • Why it matters

11. Keep the answer concise but useful.

12. The information below comes from the server's
   live web search.

SEARCH RESULTS:
{web_text}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        # --------------------------------
        # DEBUG: SHOW WHAT WILL BE SENT
        # --------------------------------

        print()
        print("================================")
        print("🌐 RESULTS SENT TO GEMINI")
        print("================================")
        print(web_text)
        print("================================")
        print()

        # --------------------------------
        # GEMINI
        # --------------------------------

        response = requests.post(
            GEMINI_URL,
            json=payload,
            timeout=30
        )

        print(
            "🌐 GEMINI STATUS:",
            response.status_code
        )

        response.raise_for_status()

        result = response.json()

        # --------------------------------
        # GET GEMINI ANSWER
        # --------------------------------

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:

            print(
                "❌ GEMINI SEARCH RESPONSE:",
                result
            )

            return jsonify({
                "success": False,
                "reply": "Gemini did not return an answer."
            })

        reply = (
            candidates[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not reply:

            return jsonify({
                "success": False,
                "reply": "No answer was generated."
            })

        print("✅ WEB ANSWER GENERATED")

        return jsonify({

            "success": True,

            "reply": reply,

            "sources": results

        })

    except Exception as e:

        print(
            "❌ WEB SEARCH ROUTE ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "reply":
                "Web Search Error: " + str(e)

        }), 500




# =====================================================
# WEB SEARCH
# =====================================================

def web_search(query):

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml"
    }

    try:

        print("🌐 SEARCHING DUCKDUCKGO:", query)

        response = requests.post(
            url,
            headers=headers,
            data={
                "q": query
            },
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        # DuckDuckGo result blocks
        for item in soup.select(".result"):

            if len(results) >= 8:
                break

            # -----------------------------
            # TITLE + URL
            # -----------------------------

            link_element = item.select_one(
                "a.result__a"
            )

            if not link_element:
                continue

            title = link_element.get_text(
                " ",
                strip=True
            )

            link = link_element.get(
                "href",
                ""
            )

            # -----------------------------
            # DESCRIPTION
            # -----------------------------

            snippet_element = item.select_one(
                ".result__snippet"
            )

            snippet = (
                snippet_element.get_text(
                    " ",
                    strip=True
                )
                if snippet_element
                else ""
            )

            # Ignore useless results
            if not title or not link:
                continue

            results.append({
                "title": title,
                "snippet": snippet,
                "url": link
            })

        print(
            "🌐 FOUND RESULTS:",
            len(results)
        )

        # Debug the actual results
        for i, result in enumerate(results, 1):

            print(
                f"\nSOURCE {i}"
            )

            print(
                "TITLE:",
                result["title"]
            )

            print(
                "SNIPPET:",
                result["snippet"]
            )

            print(
                "URL:",
                result["url"]
            )

        return results

    except Exception as e:

        print(
            "❌ SEARCH ERROR:",
            str(e)
        )

        return []

# =====================================================
# IMAGE QUERY CLEANER
# =====================================================

def clean_image_query(text):

    text = (text or "").lower().strip()

    remove_words = [
        "show me",
        "show",
        "give me",
        "find me",
        "find",
        "image of",
        "images of",
        "picture of",
        "pictures of",
        "photo of",
        "photos of",
        "image",
        "images",
        "picture",
        "pictures",
        "photo",
        "photos"
    ]

    for word in remove_words:
        text = text.replace(word, "")

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

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


GEMINI_VISION_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-3.5-flash-lite:generateContent"
    f"?key={API_KEY}"
)


def update_memory(user_message):

    memory = load_memory()

    text = user_message.lower()


    # Name detection
    if "my name is" in text:

        name = user_message.split(
            "my name is"
        )[1].strip()

        memory["facts"].append(
            "User name is " + name
        )


    # Project detection
    if "i am building" in text:

        project = user_message.split(
            "i am building"
        )[1].strip()

        memory["projects"].append(
            project
        )


    save_memory(memory)


def ask_gemini_for_memory(user_message):

    prompt = f"""
You are a memory manager.

Read the user's message.

Decide if anything should be remembered.

Remember only useful long-term information:
- name
- preferences
- hobbies
- projects
- important facts

Do NOT remember:
- temporary questions
- random conversations
- greetings

Return ONLY JSON.

Format:

{{
 "save": true,
 "category": "facts",
 "memory": "text to remember"
}}

If nothing important:

{{
 "save": false
}}

USER MESSAGE:

{user_message}
"""


    payload = {
        "contents":[
            {
                "parts":[
                    {
                        "text":prompt
                    }
                ]
            }
        ]
    }


    response = requests.post(
        GEMINI_URL,
        json=payload,
        timeout=20
    )


    result = response.json()


    text = result["candidates"][0]["content"]["parts"][0]["text"]


    text = text.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    ).strip()


    return json.loads(text)


def search_memory(query):

    memory = load_memory()

    results = []

    words = query.lower().split()


    for category in memory:

        for item in memory[category]:

            item_lower = item.lower()

            for word in words:

                if word in item_lower:

                    results.append(
                        item
                    )

                    break


    return results


# ==========================
# CHAT ROUTE
# ==========================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(silent=True) or {}

        user_message = data.get("message", "").strip()
        try:

            memory_result = ask_gemini_for_memory(
                user_message
            )


            if memory_result.get("save"):

                memory = load_memory()


                category = memory_result.get(
                    "category",
                    "facts"
                )


                memory[category].append(
                    memory_result["memory"]
                )


                save_memory(memory)


                print(
                    "🧠 MEMORY SAVED:",
                    memory_result["memory"]
                )


        except Exception as e:

            print(
                "MEMORY ERROR:",
                e
            )

        image = data.get("image")
        pdf = data.get("pdf")
        live_image = data.get("live_image")

        if not user_message:
            return jsonify({
                "reply": "Please enter a message.",
                "images": [],
                "pdf": None,
                "song": False
            }), 400

        print()
        print("================================")
        print("💬 CHAT:", user_message)
        print("================================")

        # =====================================================
        # SONG REQUEST DETECTION
        # =====================================================

        song_request = False

        song_words = [
            "sing",
            "song",
            "make a song",
            "create a song",
            "write a song"
        ]

        if any(
            word in user_message.lower()
            for word in song_words
        ):
            song_request = True

        # =====================================================
        # CHAT SESSION
        # =====================================================

        conversation_history = session.get(
            "conversation_history",
            []
        )

        # Create new chat
        if "current_chat" not in session:

            session["current_chat"] = str(
                uuid.uuid4()
            )

        # First message becomes title
        if len(conversation_history) == 0:

            session["current_chat_title"] = (
                user_message[:40]
            )

        # Save user message
        conversation_history.append({

            "role": "user",

            "text": user_message

        })

        session["conversation_history"] = (
            conversation_history
        )

        session.modified = True

        save_chat()

        # =====================================================
        # RECENT CHAT HISTORY
        # =====================================================

        recent_history = conversation_history[-10:]

        history_text = ""

        for msg in recent_history:

            history_text += (
                msg["role"]
                + ": "
                + msg["text"]
                + "\n"
            )

        # =====================================================
        # AUTOMATIC WEB SEARCH DETECTION
        # =====================================================

        message_lower = user_message.lower()

        web_keywords = [

            # Current / latest
            "latest",
            "recent",
            "currently",
            "current",
            "right now",
            "today",
            "tonight",
            "this week",
            "this month",
            "this year",

            # News
            "news",
            "breaking news",
            "latest news",
            "ai news",
            "tech news",

            # Time-sensitive
            "what happened",
            "what's happening",
            "whats happening",
            "update",
            "updates",

            # Prices
            "price",
            "prices",
            "cost",
            "worth",
            "stock price",
            "crypto price",
            "bitcoin price",
            "ethereum price",

            # Sports
            "score",
            "scores",
            "live score",
            "match today",
            "game today",
            "results today",

            # Weather
            "weather",
            "temperature",
            "forecast",

            # People / companies / products
            "who is the ceo",
            "new version",
            "new update",
            "release date",
            "released",
            "launch",
            "launched",

            # Explicit search requests
            "search the web",
            "search web",
            "search online",
            "look it up",
            "look this up",
            "google this",
            "find online",
            "find on the internet",
            "browse the web",
            "browse internet",
            "check online",
            "check the internet"
        ]

        needs_web_search = any(
            keyword in message_lower
            for keyword in web_keywords
        )

        # Explicit requests always trigger search
        explicit_web_request = any(
            keyword in message_lower
            for keyword in [
                "search the web",
                "search web",
                "search online",
                "look it up",
                "look this up",
                "find online",
                "find on the internet",
                "browse the web",
                "browse internet",
                "check online",
                "check the internet"
            ]
        )

        if explicit_web_request:

            needs_web_search = True

        # =====================================================
        # WEB SEARCH
        # =====================================================

        web_results = []

        if needs_web_search:

            print()
            print("🌐 AUTOMATIC WEB SEARCH")
            print("🌐 QUERY:", user_message)

            try:

                web_results = web_search(
                    user_message
                )

                print(
                    "🌐 WEB RESULTS:",
                    len(web_results)
                )

            except Exception as e:

                print(
                    "❌ WEB SEARCH FAILED:",
                    e
                )

                web_results = []
                

        # ==========================
        # LOAD USER MEMORY
        # ==========================

        user_memory = load_memory()

        memory_text = ""

        if user_memory:

            memory_text = """
        USER MEMORY:

        Facts:
        {facts}

        Preferences:
        {preferences}

        Projects:
        {projects}

        """.format(
                facts="\n".join(user_memory["facts"]),
                preferences="\n".join(user_memory["preferences"]),
                projects="\n".join(user_memory["projects"])
            )

        relevant_memory = search_memory(
            user_message
        )


        memory_text = ""

        if relevant_memory:

            memory_text = """

        Relevant memories about this user:

        """ + "\n".join(relevant_memory)



        identity_rule = """

        GROOM IDENTITY RULE:

        If the user asks:
        "Who developed you?"
        "Who created you?"
        "Who made you?"
        "Who is your developer?"

        You MUST answer:

        "I was developed by Rupinder Kumar."

        Never ask the user's name.
        Never give another name.

        """

        # =====================================================
        # BUILD BASE PROMPT
        # =====================================================

        prompt = (
        SYSTEM_PROMPT
        +
        memory_text
        +
        identity_rule
            +
            """

You are GROOM AI.

IMPORTANT WEB SEARCH RULE:

If LIVE WEB SEARCH RESULTS are provided below,
use them to answer the user's question.

Do NOT say:
"I cannot browse the internet."

Do NOT say:
"I don't have real-time browsing."

Do NOT claim that you personally browsed websites.

The server performed the search and provided
the search results to you.

Only use information supported by the supplied
web search results.

If the results are insufficient,
say that the available search results
were insufficient.

Do not invent current information.

SONG RULE:

If the user asks you to sing or create a song,
create an original song.

Return only the lyrics.

Do not reproduce copyrighted songs.

PDF RULE:

If the user asks for a PDF,
provide the content normally.

The application will create the PDF.

Never say:
"I cannot create PDF."

IMAGE RULE:

Images are handled by the application.

Never say:
"I cannot show images."

LIVE CAMERA RULE:

If a live camera image is attached and the
user asks about what they are showing,
analyze the image and answer based on what
you actually see.

"""
            +
            "\nConversation:\n"
            +
            history_text
            +
            "\nUser:\n"
            +
            user_message
        )

        # =====================================================
        # ADD WEB RESULTS TO PROMPT
        # =====================================================

        if web_results:

            web_text = ""

            for i, result in enumerate(
                web_results,
                1
            ):

                web_text += f"""

SOURCE {i}

TITLE:
{result.get("title", "")}

DESCRIPTION:
{result.get("snippet", "")}

URL:
{result.get("url", "")}

-------------------------
"""

            prompt += """

LIVE WEB SEARCH RESULTS:

""" + web_text

        # =====================================================
        # LIVE CAMERA INSTRUCTION
        # =====================================================

        if live_image:

            print(
                "📷 Live camera image received!"
            )

            prompt += """

LIVE CAMERA IS ACTIVE.

The user has shared a live camera frame.

If the user's question refers to something
they are showing, such as:

"What do you see?"
"What is this?"
"Read this"
"Describe this"
"Solve this"
"Can you identify this?"

analyze the attached camera image.

Do not ignore the image.

"""

        else:

            print(
                "❌ No live camera image."
            )

        # =====================================================
        # PDF PROCESSING
        # =====================================================

        if pdf:

            try:

                header, pdf_data = pdf.split(
                    ",",
                    1
                )

                pdf_bytes = base64.b64decode(
                    pdf_data
                )

                reader = PdfReader(
                    io.BytesIO(pdf_bytes)
                )

                pdf_text = ""

                for page in reader.pages:

                    txt = page.extract_text()

                    if txt:

                        pdf_text += (
                            txt + "\n"
                        )

                prompt += (
                    "\n\nPDF CONTENT:\n"
                    + pdf_text
                )

            except Exception as e:

                print(
                    "❌ PDF ERROR:",
                    e
                )

        # =====================================================
        # GEMINI PARTS
        # =====================================================

        parts = [

            {
                "text": prompt
            }

        ]

        # =====================================================
        # NORMAL IMAGE
        # =====================================================

        if image:

            try:

                header, img_data = image.split(
                    ",",
                    1
                )

                mime = (
                    header
                    .split(";")[0]
                    .split(":")[1]
                )

                parts.append({

                    "inline_data": {

                        "mime_type": mime,

                        "data": img_data

                    }

                })

                print(
                    "✅ Image added to Gemini"
                )

            except Exception as e:

                print(
                    "❌ IMAGE ERROR:",
                    e
                )

        # =====================================================
        # LIVE CAMERA IMAGE
        # =====================================================

        if live_image:

            try:

                header, img_data = (
                    live_image.split(
                        ",",
                        1
                    )
                )

                mime = (
                    header
                    .split(";")[0]
                    .split(":")[1]
                )

                parts.append({

                    "inline_data": {

                        "mime_type": mime,

                        "data": img_data

                    }

                })

                print(
                    "✅ Live image added to Gemini"
                )

            except Exception as e:

                print(
                    "❌ LIVE IMAGE ERROR:",
                    e
                )

        # =====================================================
        # GEMINI PAYLOAD
        # =====================================================

        payload = {

            "contents": [

                {

                    "parts": parts

                }

            ]

        }

        # =====================================================
        # GEMINI REQUEST
        # =====================================================

        try:

            print(
                "🤖 START GEMINI"
            )

            start_time = time.time()

            # IMPORTANT:
            # Removed the old time.sleep(3)

            response = requests.post(

                GEMINI_URL,

                json=payload,

                timeout=30

            )

            print(
                "🤖 GEMINI STATUS:",
                response.status_code
            )

            response.raise_for_status()

            elapsed = (
                time.time()
                - start_time
            )

            print(
                "🤖 GEMINI TIME:",
                round(elapsed, 2),
                "seconds"
            )

        except Exception as e:

            print(
                "❌ GEMINI ERROR:",
                e
            )

            return jsonify({

                "reply":
                    "⚠️ Gemini Error: "
                    + str(e),

                "images": [],

                "pdf": None,

                "song": song_request

            }), 500

        # =====================================================
        # GEMINI RESPONSE
        # =====================================================

        try:

            result = response.json()

            print(
                "🤖 GEMINI RESPONSE RECEIVED"
            )

            candidates = result.get(
                "candidates",
                []
            )

            if not candidates:

                print(
                    "❌ GEMINI RAW:",
                    result
                )

                reply = (
                    "⚠️ Gemini did not "
                    "return an answer."
                )

            else:

                content = candidates[0].get(
                    "content",
                    {}
                )

                response_parts = (
                    content.get(
                        "parts",
                        []
                    )
                )

                if response_parts:

                    reply = response_parts[0].get(
                        "text",
                        ""
                    )

                else:

                    reply = ""

                if not reply:

                    reply = (
                        "⚠️ No answer "
                        "was generated."
                    )

        except Exception as e:

            print(
                "❌ REPLY ERROR:",
                e
            )

            return jsonify({

                "reply":
                    "⚠️ No response "
                    "from Gemini",

                "images": [],

                "pdf": None,

                "song": song_request

            }), 500

        # =====================================================
        # PDF CREATION
        # =====================================================

        pdf_link = None

        pdf_words = [

            "pdf",
            "make pdf",
            "create pdf",
            "send pdf",
            "download pdf"

        ]

        if any(
            word in message_lower
            for word in pdf_words
        ):

            try:

                pdf_link = create_pdf(
                    reply
                )

                print(
                    "📄 PDF CREATED:",
                    pdf_link
                )

            except Exception as e:

                print(
                    "❌ PDF ERROR:",
                    e
                )

        # =====================================================
        # IMAGE SEARCH / AI IMAGE
        # =====================================================

        images = []

        image_words = [
            "image",
            "images",
            "photo",
            "photos",
            "picture",
            "pictures",
            "show me",
            "wallpaper",
            "logo"
        ]

        message_lower = user_message.lower()

        if any(
            word in message_lower
            for word in image_words
        ):

            try:

                query = clean_image_query(
                    user_message
                )

                print("🖼️ IMAGE QUERY:", query)

                # Try AI image generation first
                ai_image = generate_ai_image(
                    query
                )

                if ai_image:

                    images = [
                        ai_image
                    ]

                    print("✅ AI IMAGE GENERATED")

                else:

                    print(
                        "⚠️ AI IMAGE RETURNED NOTHING"
                    )

                    # Fallback to Pixabay
                    images = image_search(
                        query
                    )

            except Exception as e:

                print(
                    "❌ AI IMAGE FAILED:",
                    e
                )

                # Fallback to Pixabay
                try:

                    query = clean_image_query(
                        user_message
                    )

                    images = image_search(
                        query
                    )

                    print(
                        "✅ PIXABAY FALLBACK:",
                        len(images),
                        "images"
                    )

                except Exception as image_error:

                    print(
                        "❌ IMAGE SEARCH ERROR:",
                        image_error
                    )

                    images = []

        # =====================================================
        # SAVE ASSISTANT MESSAGE
        # =====================================================

        conversation_history = session.get(
            "conversation_history",
            []
        )

        conversation_history.append({

            "role": "assistant",

            "text": reply

        })

        session["conversation_history"] = (
            conversation_history
        )

        session.modified = True

        save_chat()

        # =====================================================
        # FINAL RESPONSE
        # =====================================================

        print(
            "✅ FINAL RESPONSE SENT"
        )

        return jsonify({

            "reply": reply,

            "images": images,

            "pdf": pdf_link,

            "song": song_request,

            "web_search": needs_web_search,

            "sources": web_results

        })

    except Exception as e:

        print(
            "❌ CHAT ROUTE ERROR:",
            e
        )

        return jsonify({

            "reply":
                "⚠️ Chat Error: "
                + str(e),

            "images": [],

            "pdf": None,

            "song": False,

            "web_search": False,

            "sources": []

        }), 500


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

    st=time.time()

    # after audio generation

    print("TTS time:", time.time()-st)

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
            text[:800],
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



@app.route("/song_voice", methods=["POST"])
def song_voice():

    try:

        text = request.json.get("text")

        if not text:
            return jsonify({
                "error": "No lyrics"
            }), 400


        async def generate():

            communicate = edge_tts.Communicate(
                text[:800],
                "en-US-AriaNeural"
            )

            audio = io.BytesIO()

            async for chunk in communicate.stream():

                if chunk["type"] == "audio":
                    audio.write(chunk["data"])


            audio.seek(0)

            return audio


        audio = asyncio.run(generate())


        return app.response_class(
            audio.read(),
            mimetype="audio/mpeg"
        )


    except Exception as e:

        print("SONG VOICE ERROR:", str(e))

        return jsonify({
            "error": str(e)
        }), 500


from flask import request, jsonify


from PIL import Image


# @app.route("/live_vision", methods=["POST"])
# def live_vision():

#     image_data = request.json["image"]

#     image_data = image_data.split(",")[1]

#     image_bytes = base64.b64decode(image_data)

#     image = Image.open(io.BytesIO(image_bytes))

#     image.save("live_frame.jpg")   # for testing

#     return jsonify({
#         "reply":"Image received"
#     })




@app.route("/live_vision", methods=["POST"])
def live_vision():

    try:

        data = request.json

        image = data.get("image")
        question = data.get(
            "question",
            "What do you see?"
        )

        print("✅ Vision request received")


        if not image:
            return jsonify({
                "success":False,
                "reply":"No image received"
            })


        image_data = image.split(",")[1]


        payload = {

            "contents":[
                {
                    "parts":[

                        {
                            "text": question
                        },

                        {
                            "inline_data":{
                                "mime_type":"image/jpeg",
                                "data":image_data
                            }
                        }

                    ]
                }
            ]

        }

        response = requests.post(
            GEMINI_VISION_URL,
            json=payload,
            timeout=30
        )

        print(response.status_code)
        print(response.text)

        result = response.json()




        print("GEMINI RAW:", result)



        result = response.json()

        print("STATUS:", response.status_code)
        print("GEMINI RAW:", result)

        if "candidates" in result:
            reply = result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            reply = str(result)


        print("VISION ANSWER:", reply)



        return jsonify({

            "success":True,
            "reply":reply

        })


    except Exception as e:

        print("VISION ERROR:", e)

        return jsonify({

            "success":False,
            "reply":str(e)

        })


@app.route("/speech_to_text", methods=["POST"])
def speech_to_text():

    try:
        audio = request.files.get("audio")

        if not audio:
            return jsonify({
                "success": False,
                "error": "No audio received"
            })


        audio_bytes = audio.read()

        print("Filename:", audio.filename)
        print("Bytes:", len(audio_bytes))


        if len(audio_bytes) < 10000:
            return jsonify({
                "success": False,
                "error": "Audio too short"
            })


        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/webm"
        }


        response = requests.post(
            "https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true",
            headers=headers,
            data=audio_bytes,
            timeout=30
        )


        result = response.json()

        print(result)


        if "results" in result:

            text = result["results"]["channels"][0]["alternatives"][0]["transcript"]

            print("🎤 USER SAID:", text)

            return jsonify({
                "success": True,
                "text": text
            })


        return jsonify({
            "success": False,
            "error": result
        })


    except Exception as e:

        print("DEEPGRAM CRASH:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        })



@app.route("/live")
def live():
    return render_template("live.html")


# ==========================
# NEW GEMINI CAMERA TEST
# ==========================

@app.route("/gemini_call")
def gemini_call():

    return render_template(
        "gemini_call.html"
    )



@app.route("/gemini_camera", methods=["POST"])
def gemini_camera():

    try:

        data = request.json

        image = data.get("image")


        if not image:

            return jsonify({
                "reply":"No image received"
            })


        image_data = image.split(",")[1]


        payload = {

            "contents":[
                {
                    "parts":[

                        {
                            "text":
                            "Describe what you see in this camera image."
                        },

                        {
                            "inline_data":{
                                "mime_type":
                                "image/jpeg",

                                "data":
                                image_data
                            }
                        }

                    ]
                }
            ]

        }


        response = requests.post(

            GEMINI_VISION_URL,

            json=payload,

            timeout=30

        )


        result = response.json()


        print(
            "GEMINI CAMERA:",
            result
        )


        if "candidates" in result:

            reply = (
                result["candidates"][0]
                ["content"]
                ["parts"][0]
                ["text"]
            )

        else:

            reply = str(result)



        return jsonify({

            "reply":reply

        })


    except Exception as e:

        print(
            "CAMERA ERROR:",
            e
        )

        return jsonify({

            "reply":
            str(e)

        })

@app.route("/test_memory")
def test_memory():

    memory = load_memory()

    memory["facts"].append(
        "User is testing Groom memory"
    )

    save_memory(memory)

    return jsonify(memory)







if __name__ == "__main__":
    socketio.run(app, debug=True)

# init_memory()
