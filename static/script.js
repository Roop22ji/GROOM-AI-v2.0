const chat = document.getElementById("chat-box");
const input = document.getElementById("message");
const sendBtn = document.getElementById("sendBtn");
const imagePreviewContainer =
    document.getElementById("imagePreviewContainer");

const fileInput = document.getElementById("fileInput");



let stopGeneration = false;

function scrollBottom() {
    chat.scrollTop = chat.scrollHeight;
}

function removeWelcome() {
    const welcome = document.getElementById("welcome");
    if (welcome) {
        welcome.remove();
    }
}

let selectedImage = null;
let selectedPDF = null;

fileInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) return;

    // Clear previous selections
    selectedImage = null;
    selectedPDF = null;

    if (file.type.startsWith("image/")) {

        const reader = new FileReader();

        reader.onload = function (e) {

            selectedImage = e.target.result;

            imagePreviewContainer.innerHTML = `
                <div class="preview-box">
                    🖼️ <strong>${file.name}</strong>
                </div>
            `;

        };

        reader.readAsDataURL(file);

    }

    else if (file.type === "application/pdf") {

        const reader = new FileReader();

        reader.onload = function (e) {

            selectedPDF = e.target.result;

            imagePreviewContainer.innerHTML = `
                <div class="preview-box">
                    📄 <strong>${file.name}</strong>
                </div>
            `;

        };

        reader.readAsDataURL(file);

    }

});

function addUserMessage(text, image = null) {

    let imageHTML = "";

    if (image) {
        imageHTML = `
            <img src="${image}" class="user-image">
        `;
    }

    chat.insertAdjacentHTML("beforeend", `
        <div class="message user-row">
            <div class="bubble user">
                ${imageHTML}
                <div>${text}</div>
            </div>
            <div class="avatar user-avatar">👤</div>
        </div>
    `);

    scrollBottom();
}

function addBotMessage(text) {

    chat.insertAdjacentHTML("beforeend", `
        <div class="message bot-row">
            <div class="avatar ai-avatar">🚀</div>
            <div class="bubble bot">
                ${marked.parse(text)}
            </div>
        </div>
    `);

    scrollBottom();

}

async function typeBotMessage(text) {

    const wrapper = document.createElement("div");

    wrapper.className = "message bot-row";

    wrapper.innerHTML = `
    <div class="avatar ai-avatar">🚀</div>
    <div class="bubble bot"></div>
  `;


    chat.appendChild(wrapper);
    const y = wrapper.offsetTop - 200; // adjust this value

    chat.scrollTo({
        top: y,
        behavior: "smooth"
    });

    const messageTop = wrapper.offsetTop;

    const bubble = wrapper.querySelector(".bubble");

    let words = text.split(" ");

    let current = "";

    for (let i = 0; i < words.length; i++) {

        if (stopGeneration) {

            sendBtn.innerHTML = "➤";
        
            return;
        
        }

        current += words[i] + " ";

        bubble.innerHTML = marked.parse(current);

        scrollBottom();

        // Save the position where this AI message starts
        if (i === words.length - 1) {

            setTimeout(() => {

                chat.scrollTo({
                    top: messageTop,
                    behavior: "smooth"
                });
                sendBtn.innerHTML = "➤";
            }, 300);

}

        await new Promise(resolve => setTimeout(resolve, 30));

    }

}

async function sendMessage() {
     
    const imageToSend = selectedImage;
    const pdfToSend = selectedPDF;

    stopGeneration = false;

    sendBtn.innerHTML = "■";

    const text = input.value.trim();

    if (!text) {
        sendBtn.innerHTML = "➤";
        return;
    }
    

    const rocket = document.getElementById("welcomeRocket");
    const welcome = document.getElementById("welcome");

    if (rocket && welcome) {

        rocket.classList.add("blast");

        setTimeout(() => {
            welcome.classList.add("fade");
        }, 700);

        setTimeout(() => {
            removeWelcome();
        }, 1200);

    } else {

        removeWelcome();

    }
    addUserMessage(text, imageToSend);

    input.value = "";
    fileInput.value = "";
    selectedImage = null;
    imagePreviewContainer.innerHTML = "";

    // Thinking bubble
    const thinking = document.createElement("div");

    thinking.className = "message bot-row";

    thinking.id = "thinking";

    thinking.innerHTML = `
        <div class="avatar ai-avatar">🚀</div>
        <div class="bubble bot">
            <span id="thinking-text">Thinking</span>
        </div>
    `;

    chat.appendChild(thinking);

    scrollBottom();

    let dots = 0;

    const animation = setInterval(() => {

        dots = (dots + 1) % 4;

        const t = document.getElementById("thinking-text");

        if (t) {
            t.innerHTML = "Thinking" + ".".repeat(dots);
        }

    }, 400);

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: text,
                image: imageToSend,
                pdf: pdfToSend
            })
        });

        const data = await response.json();

        clearInterval(animation);

        thinking.remove();

        await typeBotMessage(data.reply);
    }

    catch (err) {

        clearInterval(animation);
    
        thinking.remove();
    
        await typeBotMessage("⚠️ Network error. Please try again.");
    
        console.error(err);
    
    }

}

async function loadChatList() {

    const response = await fetch("/chat_list");
    const chats = await response.json();

    const chatList = document.getElementById("chatList");
    chatList.innerHTML = "";

    chats.forEach(chat => {

        const div = document.createElement("div");
        div.className = "chat-item";

        const title = document.createElement("span");
        title.textContent = chat.title;
        title.style.flex = "1";

        title.onclick = () => loadChat(chat.id);

        const del = document.createElement("button");
        del.innerHTML = "✕";
        del.className = "delete-btn";

        del.onclick = async (e) => {

            e.stopPropagation();

            if (!confirm("Delete this chat?"))
                return;

            await fetch("/delete_chat/" + chat.id, {
                method: "POST"
            });

            loadChatList();
        };

        div.appendChild(title);
        div.appendChild(del);

        chatList.appendChild(div);

    });

}

// ==========================
// LOAD CHAT
// ==========================

async function loadChat(chatId) {

    const response = await fetch("/load_chat/" + chatId);

    const messages = await response.json();

    // Clear current chat
    chat.innerHTML = "";

    // Show messages
    messages.forEach(msg => {

        if (msg.role === "user") {

            addUserMessage(msg.text);

        } else {

            addBotMessage(msg.text);

        }

    });

    scrollBottom();

    // Close sidebar after selecting a chat
    sidebar.classList.remove("show");

}





input.addEventListener("keydown", function (e) {

    if (e.key === "Enter") {

        sendMessage();

    }

});

// ==========================
// Mobile Keyboard Support
// ==========================

const inputArea = document.getElementById("input-area");

function updateKeyboard() {

    if (!window.visualViewport) return;

    const vv = window.visualViewport;
    const keyboardHeight = window.innerHeight - vv.height - vv.offsetTop;

    if (keyboardHeight > 100) {
        chat.scrollTop = chat.scrollHeight;
    } else {
        inputArea.style.bottom = "0px";
    }
}

if (window.visualViewport) {
    visualViewport.addEventListener("resize", updateKeyboard);
    visualViewport.addEventListener("scroll", updateKeyboard);

    input.addEventListener("focus", updateKeyboard);
    input.addEventListener("blur", () => {
        inputArea.style.bottom = "0px";
    });
}

// Load saved chats
loadChatList();

// ==========================
// SIDEBAR TOGGLE
// ==========================

const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");

menuBtn.addEventListener("click", () => {

    sidebar.classList.toggle("show");

});

const backBtn = document.getElementById("backBtn");

backBtn.addEventListener("click", () => {
    sidebar.classList.remove("show");
});

// ==========================
// NEW CHAT
// ==========================

async function newChat() {

    await fetch("/new_chat", {

        method: "POST"

    });

    // Clear chat window
    chat.innerHTML = `
        <div id="welcome" class="welcome">

            <div class="welcome-logo">🚀</div>

            <h1>Welcome to GROOM AI</h1>

            <p>Ask anything. I'm always ready to help.</p>

        </div>
    `;

    input.value = "";

    loadChatList();

    sidebar.classList.remove("show");

}

// ==========================
// SEND / STOP BUTTON
// ==========================

sendBtn.addEventListener("click", () => {

    if (sendBtn.innerHTML === "■") {

        stopGeneration = true;

    } else {

        sendMessage();

    }

});

document.addEventListener("DOMContentLoaded", () => {

    const glow = document.getElementById("cursor-glow");

    if (!glow) {
        console.log("cursor-glow not found");
        return;
    }

    document.addEventListener("mousemove", (e) => {
        glow.style.left = e.clientX + "px";
        glow.style.top = e.clientY + "px";
    });

});
