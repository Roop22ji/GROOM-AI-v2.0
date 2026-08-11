// ======================================================
// GROOM VISION SYSTEM
// PART 12
// Camera + Vision Framework
// ======================================================


// -----------------------------
// Variables
// -----------------------------

let groomCamera = null;
let cameraStream = null;
let visionActive = false;


// -----------------------------
// Create Camera UI
// -----------------------------

function createVisionPanel(){


    if(document.getElementById("groomVision"))
        return;


    const panel=document.createElement("div");

    panel.id="groomVision";


    panel.innerHTML=`

        <video id="groomCamera"
        autoplay
        playsinline>
        </video>


        <div class="vision-controls">

            <button id="captureVision">
                📸 Capture
            </button>


            <button id="closeVision">
                ❌ Close
            </button>

        </div>

    `;


    document.body.appendChild(panel);



    document
    .getElementById("captureVision")
    .onclick=captureVisionImage;



    document
    .getElementById("closeVision")
    .onclick=stopVision;


}



// -----------------------------
// Start Camera
// -----------------------------

async function startVision(){


    createVisionPanel();


    const video=
    document.getElementById("groomCamera");


    try{


        cameraStream =
        await navigator.mediaDevices.getUserMedia({

            video:true,

            audio:false

        });



        video.srcObject=cameraStream;


        visionActive=true;



        setExpression("excited");


        showGroomMessage(
            "👀 Vision activated"
        );


    }


    catch(error){


        console.error(error);


        showGroomMessage(
        "❌ Camera permission denied"
        );


        setExpression("sad");


    }



}



// -----------------------------
// Stop Camera
// -----------------------------

function stopVision(){


    if(cameraStream){


        cameraStream
        .getTracks()
        .forEach(track=>{

            track.stop();

        });


    }



    const panel=
    document.getElementById(
        "groomVision"
    );


    if(panel)
        panel.remove();



    visionActive=false;



    setExpression("happy");


    showGroomMessage(
        "😊 Vision closed"
    );


}



// -----------------------------
// Capture Image
// -----------------------------

function captureVisionImage(){


    const video=
    document.getElementById(
        "groomCamera"
    );


    if(!video)
        return;



    const canvas=
    document.createElement(
        "canvas"
    );


    canvas.width=
    video.videoWidth;


    canvas.height=
    video.videoHeight;



    const ctx=
    canvas.getContext("2d");



    ctx.drawImage(
        video,
        0,
        0
    );



    const image=
    canvas.toDataURL(
        "image/jpeg"
    );



    showGroomMessage(
        "📸 Image captured"
    );



    // Send image to chat

    selectedImage=image;



    input.value=
    "What do you see in this image?";


    sendMessage();



}



// -----------------------------
// Vision Button
// -----------------------------

window.addEventListener(
"load",
()=>{


    const btn=
    document.createElement(
        "button"
    );


    btn.id="visionBtn";


    btn.innerHTML="👁️";


    btn.title=
    "Open GROOM Vision";


    document.body.appendChild(btn);



    btn.onclick=()=>{


        if(visionActive){

            stopVision();

        }
        else{

            startVision();

        }


    };


});



// -----------------------------
// Basic Face Tracking Hook
// -----------------------------


function detectFacePlaceholder(){


    if(!visionActive)
        return;



    /*
    
    Future:
    
    - MediaPipe Face Detection
    - Face landmarks
    - Eye tracking
    - Emotion detection
    
    */


}



// Check every second

setInterval(
detectFacePlaceholder,
1000
);



console.log(
"✅ GROOM Vision Loaded"
);

// ======================================================
// GROOM AI VISION SYSTEM
// PART 13
// ======================================================


// -------------------------------
// Vision States
// -------------------------------

let groomSeeing = false;


// -------------------------------
// Detect Image Upload
// -------------------------------

const visionFileInput = document.getElementById("fileInput");


if(visionFileInput){

    visionFileInput.addEventListener("change", function(){

        const file = this.files[0];


        if(!file)
            return;


        if(file.type.startsWith("image/")){


            groomSeeing = true;


            setExpression("surprised");


            const bubble =
            document.querySelector(".groom-message");


            if(bubble){

                bubble.innerHTML =
                "👀 I can see your image!";

            }


            setTimeout(()=>{

                setExpression("thinking");


                if(bubble){

                    bubble.innerHTML =
                    "🧠 Analyzing image...";

                }


            },1500);



        }


    });


}



// -------------------------------
// Vision After AI Reply
// -------------------------------


function visionCompleted(){


    if(!groomSeeing)
        return;


    const bubble =
    document.querySelector(".groom-message");


    setExpression("happy");


    if(bubble){

        bubble.innerHTML =
        "😊 I understood the image!";

    }


    setTimeout(()=>{

        if(bubble){

            bubble.innerHTML =
            "Need anything else?";

        }

    },3000);



    groomSeeing=false;


}



// -------------------------------
// Connect with Chat Response
// -------------------------------


const oldTypeBotMessage =
window.typeBotMessage;


if(oldTypeBotMessage){


    window.typeBotMessage =
    async function(text){


        await oldTypeBotMessage(text);


        visionCompleted();


    };


}




// -------------------------------
// Camera Style Vision Feeling
// -------------------------------


setInterval(()=>{


    if(!groomSeeing)
        return;


    const eyes =
    document.querySelectorAll(".eye");


    eyes.forEach(eye=>{


        eye.style.transform =
        "scale(1.2)";


        setTimeout(()=>{


            eye.style.transform =
            "scale(1)";


        },500);



    });



},2000);



// -------------------------------
// Start Message
// -------------------------------


console.log(
"👁️ GROOM Vision System Loaded"
);


// ======================================================
// GROOM AI VISION SYSTEM
// PART 14 - CAMERA VISION MODE
// ======================================================


// -------------------------------
// Camera Variables
// -------------------------------

// let cameraStream = null;
let cameraActive = false;


// -------------------------------
// Create Camera Button
// -------------------------------

function createVisionButton(){

    const panel =
    document.getElementById("groomPanelContent");


    if(!panel)
        return;


    const btn =
    document.createElement("button");


    btn.className="groom-action";

    btn.id="visionCameraBtn";

    btn.innerHTML="📷 Open Camera Vision";


    panel.appendChild(btn);



    btn.onclick=function(){

        if(cameraActive){

            stopCamera();

        }
        else{

            startCamera();

        }

    };


}


document.addEventListener("DOMContentLoaded",()=>{

    createVisionButton();

});



// -------------------------------
// Start Camera
// -------------------------------

async function startCamera(){


    try{


        cameraStream =
        await navigator.mediaDevices.getUserMedia({

            video:true,

            audio:false

        });



        cameraActive=true;


        const video =
        document.createElement("video");


        video.id="groomCamera";

        video.autoplay=true;

        video.playsInline=true;

        video.srcObject=cameraStream;



        video.style.width="100%";

        video.style.borderRadius="15px";



        const panel =
        document.getElementById("groomPanelContent");


        panel.appendChild(video);



        setExpression("surprised");


        const bubble =
        document.querySelector(".groom-message");


        if(bubble){

            bubble.innerHTML =
            "👀 Looking through camera...";

        }



        setTimeout(()=>{

            setExpression("thinking");

        },1500);



    }


    catch(error){


        console.error(
            "Camera Error:",
            error
        );


        const bubble =
        document.querySelector(".groom-message");


        if(bubble){

            bubble.innerHTML =
            "❌ Camera permission denied";

        }


    }


}




// -------------------------------
// Stop Camera
// -------------------------------

function stopCamera(){


    if(cameraStream){


        cameraStream
        .getTracks()
        .forEach(track=>{

            track.stop();

        });


    }



    const video =
    document.getElementById("groomCamera");


    if(video){

        video.remove();

    }



    cameraActive=false;



    setExpression("happy");


    const bubble =
    document.querySelector(".groom-message");


    if(bubble){

        bubble.innerHTML =
        "😊 Camera closed";

    }


}




// -------------------------------
// Capture Camera Image
// -------------------------------


function captureVisionImage(){


    const video =
    document.getElementById("groomCamera");


    if(!video)
        return null;



    const canvas =
    document.createElement("canvas");


    canvas.width =
    video.videoWidth;


    canvas.height =
    video.videoHeight;



    const ctx =
    canvas.getContext("2d");


    ctx.drawImage(
        video,
        0,
        0
    );


    return canvas.toDataURL(
        "image/jpeg"
    );


}



// -------------------------------
// Auto Look Animation
// -------------------------------


setInterval(()=>{


    if(!cameraActive)
        return;



    setExpression("thinking");


    const bubble =
    document.querySelector(".groom-message");


    if(bubble){

        bubble.innerHTML =
        "👁️ Observing...";

    }



},10000);



// -------------------------------
// Loaded
// -------------------------------

console.log(
"📷 GROOM Camera Vision Loaded"
);


// ======================================================
// PART 15 - CAMERA IMAGE AI ANALYSIS
// ======================================================


// -------------------------------
// Ask GROOM About Camera View
// -------------------------------

async function askCameraVision(){


    const image =
    captureVisionImage();


    if(!image){


        const bubble =
        document.querySelector(".groom-message");


        if(bubble){

            bubble.innerHTML =
            "❌ Camera is not active";

        }


        return;

    }



    setExpression("thinking");



    const bubble =
    document.querySelector(".groom-message");


    if(bubble){

        bubble.innerHTML =
        "🧠 Understanding what I see...";

    }



    try{


        const response =
        await fetch("/chat",{


            method:"POST",


            headers:{


                "Content-Type":
                "application/json"


            },


            body:JSON.stringify({


                message:
                "Look at this camera image and describe what you see.",


                image:image


            })


        });



        const data =
        await response.json();



        console.log(
            "Vision Result:",
            data
        );



        if(data.reply){


            setExpression("happy");



            const chat =
            document.getElementById("chat-box");



            if(chat){


                chat.insertAdjacentHTML(
                    "beforeend",

                    `

                    <div class="message bot-row">

                        <div class="avatar ai-avatar">
                            🚀
                        </div>

                        <div class="bubble bot">

                            ${marked.parse(data.reply)}

                        </div>

                    </div>

                    `

                );


            }



            speak(data.reply);



            if(bubble){

                bubble.innerHTML =
                "😊 I can see it!";

            }



        }



    }


    catch(error){


        console.error(
            "Vision Error:",
            error
        );


        setExpression("sad");


        if(bubble){

            bubble.innerHTML =
            "⚠️ Vision failed";

        }


    }



}



// -------------------------------
// Add Analyze Button
// -------------------------------


function addAnalyzeButton(){


    const panel =
    document.getElementById("groomPanelContent");


    if(!panel)
        return;



    const btn =
    document.createElement("button");


    btn.className =
    "groom-action";


    btn.innerHTML =
    "👁️ Analyze Camera";


    btn.id =
    "analyzeCameraBtn";



    panel.appendChild(btn);



    btn.onclick=function(){


        askCameraVision();


    };


}



document.addEventListener(
"DOMContentLoaded",
()=>{


    addAnalyzeButton();


});




// -------------------------------
// Vision Keyboard Shortcut
// Press V
// -------------------------------


document.addEventListener(
"keydown",
(e)=>{


    if(
        e.key.toLowerCase()==="v"
    ){


        if(cameraActive){

            askCameraVision();

        }


    }


});



console.log(
"🧠 GROOM Vision AI Connected"
);

