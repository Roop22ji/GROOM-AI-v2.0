const chat = document.getElementById("chat-box");
const chatBox = document.getElementById("chat-box");
const input = document.getElementById("message");
const sendBtn = document.getElementById("sendBtn");
const imagePreviewContainer =
    document.getElementById("imagePreviewContainer");


const fileInput = document.getElementById("fileInput");



let stopGeneration = false;
let isGenerating = false;

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
            const title = document.querySelector(".panel-title");

            

            if (title) {
                title.innerHTML = "📄 PDF Assistant";
                
            }

            

        };

        reader.readAsDataURL(file);

    }

    if (file.name.toLowerCase().endsWith(".pdf")) {


        

        
    
        const title = document.querySelector(".panel-title");
    
        if (title) {
            title.innerHTML = "📄 PDF Assistant";
        }

        const btn = document.getElementById("summaryBtn");

        

        if (btn) {
            btn.innerHTML = "📄 Summarize PDF";
        }

        document.getElementById("fileBtn").innerHTML = "❓ Ask Questions";

        document.getElementById("codeBtn").innerHTML = "📚 Extract Text";

        
    
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

            isGenerating = false;
        
            sendBtn.disabled = false;
            sendBtn.innerHTML = "➤";
        
            input.placeholder = "Message GROOM AI...";
            input.focus();
        
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
     

    if (isGenerating) {
        return;
    }
    isGenerating = true;

    sendBtn.disabled = true;
    input.placeholder = "⏳ GROOM is replying...";

    const imageToSend = selectedImage;
    const pdfToSend = selectedPDF;

    stopGeneration = false;

    sendBtn.innerHTML = "■";

    const text = input.value.trim();

    if (!text) {

        isGenerating = false;

        input.disabled = false;
        sendBtn.disabled = false;

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

    const head = document.querySelector(".groom-head");

    head.classList.remove("happy");
    head.classList.add("thinking");

    const bubble = document.querySelector(".groom-message");

    if (bubble) {
        bubble.innerHTML = "🤔 Thinking...";
    }

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

        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }
        
        const data = await response.json();
        console.log(data);

        clearInterval(animation);

        thinking.remove();

        await typeBotMessage(data.reply);

        speakGroom(data.reply);

        isGenerating = false;

        sendBtn.disabled = false;
        input.disabled = false;

        input.placeholder = "Message GROOM AI...";

        sendBtn.innerHTML = "➤";

        input.focus();

        const head = document.querySelector(".groom-head");

        head.classList.remove("thinking");
        head.classList.add("happy");

        if (bubble) {

            bubble.innerHTML = "😊 Done!";
        
            setTimeout(() => {
                bubble.innerHTML = "Need anything else?";
            }, 2000);
        
        }

        if (data.images && data.images.length > 0) {

            const html = data.images.map(img => `
                <img src="${img}"
                    class="search-image"
                    onclick="openImage('${img}')">
            `).join("");

            chat.insertAdjacentHTML(
                "beforeend",
                `<div class="message bot-row">
                    <div class="avatar ai-avatar">🚀</div>
                    <div class="bubble bot">${html}</div>
                </div>`
            );

        }

        loadChatList();
    }

    catch (err) {

        isGenerating = false;

        sendBtn.disabled = false;
        input.placeholder = "Message GROOM AI...";
        input.focus();

        clearInterval(animation);
    
        thinking.remove();
    
        console.error("ERROR:", err);
    
        await typeBotMessage("⚠️ " + err.message);
    }

}

async function loadChatList() {

    const response = await fetch("/chat_list");
    const chats = await response.json();

    const chatList = document.getElementById("chatList");
    chatList.innerHTML = "";

    chats.forEach(chatItem => {

        const div = document.createElement("div");
        div.className = "chat-item";

        const title = document.createElement("span");
        title.textContent = chatItem.title;
        title.style.flex = "1";

        title.onclick = () => loadChat(chatItem.id);

        const del = document.createElement("button");
        del.innerHTML = "✕";
        del.className = "delete-btn";

        del.onclick = async (e) => {

            e.stopPropagation();
        
            if (!confirm("Delete this chat?"))
                return;
        
            await fetch("/delete_chat/" + chatItem.id, {
                method: "POST"
            });
        
            // Clear current screen
            chatBox.innerHTML = `
                <div id="welcome" class="welcome">
                    <div class="welcome-logo">🚀</div>
                    <h1>Welcome to GROOM AI</h1>
                    <p>Ask anything. I'm always ready to help.</p>
                </div>
            `;
        
            sessionStorage.removeItem("currentChat");
        
            // wait a little, then reload sidebar
            setTimeout(() => {
                loadChatList();
            }, 300);
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

    sessionStorage.setItem("currentChat", chatId);

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



function openImage(src){

    document.getElementById("viewerImage").src = src;

    document.getElementById("imageViewer").style.display = "flex";

}

function closeImage(){

    document.getElementById("imageViewer").style.display = "none";

}

// ==========================
// GROOM ROBOT ACTIVATION
// ==========================

document.addEventListener("DOMContentLoaded", () => {

    const rocket = document.querySelector(".logo");
    const groom = document.getElementById("groom-helper");
    const panel = document.getElementById("groom-panel");
    const head = document.querySelector(".groom-head");
    const summaryBtn = document.getElementById("summaryBtn");

    // // ==========================
    // // SUMMARIZE PDF BUTTON
    // // ==========================

    // const summaryBtn = document.getElementById("summaryBtn");

    // if (summaryBtn) {

    //     summaryBtn.addEventListener("click", () => {

    //         alert("Summarize button clicked!");

    //     });

    // }

    if (rocket && groom) {

        rocket.addEventListener("click", () => {

            groom.classList.toggle("show");
        
            if (groom.classList.contains("show")) {
                head.classList.remove("thinking");
                head.classList.add("happy");
            }
        
        });

    }

    if (groom && panel) {

        const robot = document.querySelector(".groom-robot");

        robot.addEventListener("click", function(e){

            e.stopPropagation();

            panel.classList.toggle("show");

        });
    

        panel.addEventListener("click", function(e){

            e.stopPropagation();
        
            if (e.target.id === "summaryBtn"){

                input.value = "Summarize this PDF";
            
                panel.classList.remove("show");
            
                sendMessage();
            
                return;
            
            }
        
            else if (e.target.id === "fileBtn"){

                input.value = "Answer my questions about this PDF";
            
                panel.classList.remove("show");
            
                sendMessage();
            
                return;
            
            }

            else if (e.target.id === "codeBtn"){

                input.value = "Extract all text from this PDF";

                panel.classList.remove("show");

                sendMessage();

                return;

            }
        
            else if (e.target.classList.contains("quick-item")){
        
                input.value = e.target.textContent.trim();
        
                panel.classList.remove("show");
        
                sendMessage();
        
            }
        
        });

// ==========================
// QUICK ASK
// ==========================

document.addEventListener("DOMContentLoaded", () => {

    const quickBtn = document.querySelector('[data-action="ask"]');
    const quickMenu = document.getElementById("quickAskMenu");

    if (quickBtn && quickMenu) {

        quickBtn.onclick = function(e) {

            e.stopPropagation();

            quickMenu.classList.toggle("show");

            console.log("Quick Ask Clicked");

        };

    }

});
}

});


// ==========================
// GROOM ROBOT DRAG / GRAB FEATURE
// ==========================

document.addEventListener("DOMContentLoaded", () => {

    const groom = document.getElementById("groom-helper");

    if (!groom) return;

    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;

    function startDrag(e) {

        isDragging = true;

        const rect = groom.getBoundingClientRect();

        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;

        offsetX = clientX - rect.left;
        offsetY = clientY - rect.top;

        groom.style.transition = "none";
    }


    function moveDrag(e) {

        if (!isDragging) return;

        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;


        groom.style.left = (clientX - offsetX) + "px";
        groom.style.top = (clientY - offsetY) + "px";

        groom.style.right = "auto";
        groom.style.bottom = "auto";
    }


    function stopDrag() {

        isDragging = false;

        groom.style.transition =
        "transform .6s ease, opacity .6s ease";

    }


    groom.addEventListener("mousedown", startDrag);
    document.addEventListener("mousemove", moveDrag);
    document.addEventListener("mouseup", stopDrag);


    // Mobile touch
    groom.addEventListener("touchstart", startDrag);
    document.addEventListener("touchmove", moveDrag);
    document.addEventListener("touchend", stopDrag);

});

function groomExpression(expression){

    const head = document.querySelector(".groom-head");

    if(!head) return;

    head.classList.remove(
        "happy",
        "thinking",
        "sleep",
        "angry"
    );

    head.classList.add(expression);
}
// ==========================
// GROOM AI VOICE OUTPUT
// ==========================

function speakGroom(text) {

    if (!("speechSynthesis" in window)) {
        console.log("Speech synthesis not available");
        return;
    }

    const speech = new SpeechSynthesisUtterance(text);

    speech.lang = "en-US";
    speech.rate = 1;
    speech.pitch = 1;


    // Load Android voices
    let voices = window.speechSynthesis.getVoices();

    if (voices.length > 0) {

        let englishVoice = voices.find(v =>
            v.lang.includes("en")
        );

        speech.voice = englishVoice || voices[0];

    }


    speech.onstart = () => {
        startTalking();
    };


    speech.onend = () => {
        stopTalking();
    };


    speech.onerror = (e) => {
        console.log("Speech error:", e);
        stopTalking();
    };


    window.speechSynthesis.cancel();


    setTimeout(() => {
        window.speechSynthesis.speak(speech);
    }, 200);

}

window.speechSynthesis.onvoiceschanged = () => {
    console.log(
        "Voices loaded:",
        window.speechSynthesis.getVoices().length
    );
};

let mouthAnimation;

function startMouth() {

    const mouth = document.querySelector(".groom-mouth");

    if (!mouth) return;

    mouthAnimation = setInterval(() => {

        if (mouth.style.height === "25px") {
            mouth.style.height = "8px";
        } else {
            mouth.style.height = "25px";
        }

    }, 120);

}


function stopMouth() {

    clearInterval(mouthAnimation);

    const mouth = document.querySelector(".groom-mouth");

    if (mouth) {
        mouth.style.height = "8px";
    }

}



function startTalking(){

    const head = document.querySelector(".groom-head");

    if(head){
        head.classList.add("speaking");
    }

}


function stopTalking(){

    const head = document.querySelector(".groom-head");

    if(head){
        head.classList.remove("speaking");
    }

}
