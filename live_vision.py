// ============================================================
// GROOM LIVE CAMERA
// Connects to Flask /live_vision
// ============================================================

const camera = document.getElementById("camera");
const canvas = document.getElementById("frameCanvas");

const startLiveBtn = document.getElementById("startLive");
const askLiveBtn = document.getElementById("askLive");
const closeVideoBtn = document.getElementById("closeVideo");

const liveStatus = document.getElementById("liveStatus");
const liveAnswer = document.getElementById("liveAnswer");


// ============================================================
// SETTINGS
// ============================================================

const FRAME_INTERVAL = 1500; // 1.5 seconds
const JPEG_QUALITY = 0.65;

let cameraStream = null;
let liveTimer = null;

let liveRunning = false;
let requestInProgress = false;


// ============================================================
// STATUS
// ============================================================

function setLiveStatus(text) {

    if (liveStatus) {
        liveStatus.textContent = text;
    }

}


// ============================================================
// CAMERA
// ============================================================

async function startCamera() {

    try {

        setLiveStatus("🟡 Requesting camera permission...");

        cameraStream = await navigator.mediaDevices.getUserMedia({

            video: {
                facingMode: "user",
                width: {
                    ideal: 1280
                },
                height: {
                    ideal: 720
                }
            },

            audio: false

        });

        camera.srcObject = cameraStream;

        await camera.play();

        setLiveStatus("🟢 Camera ready");

        console.log("🎥 Camera started");

        return true;

    }

    catch (error) {

        console.error(
            "❌ CAMERA ERROR:",
            error
        );

        setLiveStatus(
            "❌ Camera error: " + error.message
        );

        if (liveAnswer) {

            liveAnswer.textContent =
                "Please allow camera permission and try again.";

        }

        return false;

    }

}


// ============================================================
// CAPTURE FRAME
// ============================================================

function captureFrame() {

    if (!camera) {

        console.error(
            "❌ Camera element not found"
        );

        return null;

    }


    if (
        camera.readyState < 2 ||
        camera.videoWidth === 0 ||
        camera.videoHeight === 0
    ) {

        console.log(
            "⏳ Camera is not ready yet"
        );

        return null;

    }


    const width = camera.videoWidth;
    const height = camera.videoHeight;


    canvas.width = width;
    canvas.height = height;


    const ctx = canvas.getContext("2d");

    ctx.drawImage(
        camera,
        0,
        0,
        width,
        height
    );


    const imageData =
        canvas.toDataURL(
            "image/jpeg",
            JPEG_QUALITY
        );


    return imageData;

}


// ============================================================
// SEND FRAME TO FLASK
// ============================================================

async function sendFrameToGroom(question) {

    if (!liveRunning) {
        return;
    }


    // Don't send another frame while
    // the previous Gemini request is running.

    if (requestInProgress) {

        console.log(
            "⏳ Previous vision request still running"
        );

        return;

    }


    const image = captureFrame();


    if (!image) {
        return;
    }


    requestInProgress = true;


    setLiveStatus(
        "🟡 GROOM is looking..."
    );


    console.log(
        "📷 Sending camera frame to /live_vision"
    );


    try {

        const response = await fetch(
            "/live_vision",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    image: image,

                    question:
                        question ||
                        "What do you see?"

                })

            }
        );


        console.log(
            "🌐 /live_vision status:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "🤖 GROOM vision response:",
            data
        );


        if (
            data.success === false
        ) {

            throw new Error(
                data.reply ||
                data.error ||
                "Vision request failed"
            );

        }


        if (liveAnswer) {

            liveAnswer.textContent =
                data.reply ||
                "I couldn't understand the image.";

        }


        setLiveStatus(
            "🟢 GROOM is watching"
        );


    }

    catch (error) {

        console.error(
            "❌ LIVE VISION ERROR:",
            error
        );


        setLiveStatus(
            "🔴 Vision error"
        );


        if (liveAnswer) {

            liveAnswer.textContent =
                "⚠️ " + error.message;

        }

    }

    finally {

        requestInProgress = false;

    }

}


// ============================================================
// START LIVE VISION
// ============================================================

function startLiveVision() {

    if (liveRunning) {

        console.log(
            "⚠️ Live vision already running"
        );

        return;

    }


    liveRunning = true;


    if (startLiveBtn) {

        startLiveBtn.textContent =
            "⏹ Stop Live";

    }


    setLiveStatus(
        "🟢 Live vision started"
    );


    console.log(
        "🔴 LIVE VISION STARTED"
    );


    // Immediately analyze one frame.

    sendFrameToGroom(
        "What do you see? Describe what is currently in front of the camera."
    );


    // Continue sending frames.

    liveTimer = setInterval(
        () => {

            sendFrameToGroom(
                "Look at the current camera view. What do you see? Mention only important changes or objects."
            );

        },
        FRAME_INTERVAL
    );

}


// ============================================================
// STOP LIVE VISION
// ============================================================

function stopLiveVision() {

    liveRunning = false;


    if (liveTimer) {

        clearInterval(
            liveTimer
        );

        liveTimer = null;

    }


    requestInProgress = false;


    if (startLiveBtn) {

        startLiveBtn.textContent =
            "🎥 Start Live";

    }


    setLiveStatus(
        "⚪ Live vision stopped"
    );


    console.log(
        "⏹ LIVE VISION STOPPED"
    );

}


// ============================================================
// START / STOP BUTTON
// ============================================================

if (startLiveBtn) {

    startLiveBtn.addEventListener(
        "click",
        async function () {

            if (liveRunning) {

                stopLiveVision();

                return;

            }


            if (!cameraStream) {

                const started =
                    await startCamera();


                if (!started) {
                    return;
                }

            }


            startLiveVision();

        }
    );

}


// ============================================================
// ASK GROOM BUTTON
// ============================================================

if (askLiveBtn) {

    askLiveBtn.addEventListener(
        "click",
        async function () {

            if (!cameraStream) {

                const started =
                    await startCamera();


                if (!started) {
                    return;
                }

            }


            const question =
                prompt(
                    "Ask GROOM about what the camera sees:",
                    "What do you see?"
                );


            if (!question) {
                return;
            }


            if (!liveRunning) {

                liveRunning = true;

            }


            await sendFrameToGroom(
                question
            );

        }
    );

}


// ============================================================
// END CALL
// ============================================================

if (closeVideoBtn) {

    closeVideoBtn.addEventListener(
        "click",
        function () {

            console.log(
                "📴 Ending GROOM Live"
            );


            stopLiveVision();


            if (cameraStream) {

                cameraStream
                    .getTracks()
                    .forEach(
                        track => track.stop()
                    );

                cameraStream = null;

            }


            if (camera) {

                camera.srcObject = null;

            }


            setLiveStatus(
                "⚪ Call ended"
            );


            // Return to main chat.

            window.location.href = "/";

        }
    );

}


// ============================================================
// AUTOMATIC CAMERA START
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        console.log(
            "🚀 GROOM Live page loaded"
        );


        if (!navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia) {

            setLiveStatus(
                "❌ Camera not supported"
            );

            return;

        }


        // Start camera automatically.

        await startCamera();

    }
);


// ============================================================
// PAGE EXIT CLEANUP
// ============================================================

window.addEventListener(
    "beforeunload",
    function () {

        stopLiveVision();


        if (cameraStream) {

            cameraStream
                .getTracks()
                .forEach(
                    track => track.stop()
                );

        }

    }
);


// ============================================================
// DEBUG HELPERS
// ============================================================

window.groomLive = {

    start: startLiveVision,

    stop: stopLiveVision,

    capture: captureFrame,

    ask: sendFrameToGroom

};


console.log(
    "✅ GROOM Live JavaScript loaded"
);