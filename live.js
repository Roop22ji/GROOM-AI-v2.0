(() => {

    
    const video = document.getElementById("userVideo");
    const statusText = document.getElementById("statusText");
    const thinking = document.getElementById("thinking");
    
    const micBtn = document.getElementById("micBtn");
    const cameraBtn = document.getElementById("cameraBtn");
    const endBtn = document.getElementById("endBtn");
    
    let stream = null;
    let cameraOn = true;
    let micOn = true;
    let recognition = null;
    let busy = false;
    
    let currentAudio = null;
    let speaking = false;

    let autoVisionTimer = null;
    let latestVision = "";
    
    
    function startAutoVision() {

        stopAutoVision();
    
        autoVisionTimer = setInterval(async () => {
    
            if (!cameraOn || busy) {
                return;
            }
    
            const image = frame();
    
            if (!image) {
                return;
            }
    
            try {
    
                const response = await fetch("/live_vision", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        image: image,
                        question: "Observe the camera and remember what you see. Do not give a spoken response."
                    })
                });
    
                const data = await response.json();
    
                if (data.reply) {
                    latestVision = data.reply;
                    console.log("👁️ Auto vision:", latestVision);
                }
    
            } catch (error) {
    
                console.warn("Auto vision:", error);
    
            }
    
        }, 5000);
    }
    
    
    function stopAutoVision() {
    
        if (autoVisionTimer) {
            clearInterval(autoVisionTimer);
            autoVisionTimer = null;
        }
    
    }


    // -------------------------
    // STATUS
    // -------------------------
    
    function status(text) {
        if (statusText) {
            statusText.textContent = text;
        }
    }
    
    
    // -------------------------
    // THINKING
    // -------------------------
    
    function think(value) {
        if (thinking) {
            thinking.classList.toggle("hidden", !value);
        }
    }
    
    
    // -------------------------
    // CAMERA
    // -------------------------
    
    async function startCamera() {
    
        try {
    
            if (!navigator.mediaDevices?.getUserMedia) {
                throw new Error("Camera API unavailable");
            }
    
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: "user",
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: true
            });
    
            video.srcObject = stream;
    
            cameraOn = true;
            micOn = true;
    
            updateButtons();
    
            status("🟢 Live call started");

            startAutoVision();
    
        } catch (error) {
    
            console.error(error);
    
            status("❌ Camera/microphone permission failed");
    
        }
    
    }
    
    
    // -------------------------
    // BUTTON UI
    // -------------------------
    
    function updateButtons() {
    
        if (cameraBtn) {
    
            cameraBtn.classList.toggle("off", !cameraOn);
    
            cameraBtn.innerHTML = cameraOn
                ? "📷<small>Camera</small>"
                : "🚫<small>Camera</small>";
    
        }
    
    
        if (micBtn) {
    
            micBtn.classList.toggle("off", !micOn);
    
            micBtn.innerHTML = micOn
                ? "🎤<small>Mic</small>"
                : "🔇<small>Mic</small>";
    
        }
    
    }
    
    
    // -------------------------
    // CAPTURE CAMERA FRAME
    // -------------------------
    
    function frame() {
    
        if (
            !stream ||
            !cameraOn ||
            video.readyState < 2 ||
            !video.videoWidth
        ) {
            return null;
        }
    
        const canvas = document.createElement("canvas");
    
        const scale = Math.min(
            1,
            960 / video.videoWidth
        );
    
        canvas.width = Math.round(
            video.videoWidth * scale
        );
    
        canvas.height = Math.round(
            video.videoHeight * scale
        );
    
        const ctx = canvas.getContext("2d");
    
        ctx.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );
    
        return canvas.toDataURL(
            "image/jpeg",
            0.65
        );
    
    }
    
    
    // -------------------------
    // ASK GROOM
    // -------------------------
    
    async function askGroom(question) {
    
        if (busy) {
            return;
        }
    
        const image = frame();
    
        if (!image) {
    
            status("⚠️ Camera is not ready");
    
            return;
        }
    
        busy = true;
    
        think(true);
    
        status("👁️ GROOM is looking…");
    
    
        try {
    
            const response = await fetch(
                "/live_vision",
                {
                    method: "POST",
    
                    headers: {
                        "Content-Type": "application/json"
                    },
    
                    body: JSON.stringify({
                        image: image,
                        question: question
                    })
                }
            );
    
    
            const data = await response.json();
    
    
            if (!response.ok || !data.reply) {
    
                throw new Error(
                    data.error || "Vision request failed"
                );
    
            }
    
    
            status("🟢 GROOM answered");
    
            // GROOM speaks the answer
            await speak(data.reply);
    
    
        } catch (error) {
    
            console.error(error);
    
            status("⚠️ GROOM could not answer");
    
        } finally {
    
            busy = false;
    
            think(false);
    
        }
    
    }
    
    
    // -------------------------
    // GROOM VOICE
    // -------------------------
    
    async function speak(text) {
    
        if (!text) {
            return;
        }
    
    
        // Stop previous GROOM audio
        if (currentAudio) {
    
            currentAudio.pause();
    
            currentAudio.currentTime = 0;
    
            currentAudio = null;
    
        }
    
    
        speaking = true;
    
    
        try {
    
            const response = await fetch(
                "/voice",
                {
                    method: "POST",
    
                    headers: {
                        "Content-Type": "application/json"
                    },
    
                    body: JSON.stringify({
                        text: text
                    })
                }
            );
    
    
            if (!response.ok) {
                return;
            }
    
    
            const blob = await response.blob();
    
    
            currentAudio = new Audio(
                URL.createObjectURL(blob)
            );
    
    
            await currentAudio.play().catch(() => {});
    
    
            await new Promise(resolve => {
    
                currentAudio.onended = resolve;
    
                currentAudio.onerror = resolve;
    
            });
    
    
        } catch (error) {
    
            console.warn("voice", error);
    
        } finally {
    
            speaking = false;
    
            currentAudio = null;
    
        }
    
    }
    
    
    // -------------------------
    // STOP GROOM SPEAKING
    // -------------------------
    
    function stopGroomSpeaking() {
    
        if (!currentAudio) {
            return;
        }
    
        currentAudio.pause();
    
        currentAudio.currentTime = 0;
    
        currentAudio = null;
    
        speaking = false;
    
    }
    
    
    // -------------------------
    // CAMERA ON / OFF
    // -------------------------
    
    function toggleCamera() {
    
        if (!stream) {
            return;
        }
    
        cameraOn = !cameraOn;
    
    
        stream
            .getVideoTracks()
            .forEach(track => {
                track.enabled = cameraOn;
            });
    
    
        updateButtons();
    
    
        status(
            cameraOn
                ? "🟢 Camera on"
                : "⏸️ Camera off"
        );
    
    }
    
    
    // -------------------------
    // MICROPHONE ON / OFF
    // -------------------------
    
    function toggleMic() {
    
        if (!stream) {
            return;
        }
    
        micOn = !micOn;
    
    
        stream
            .getAudioTracks()
            .forEach(track => {
                track.enabled = micOn;
            });
    
    
        updateButtons();
    
    
        status(
            micOn
                ? "🎤 Microphone on"
                : "🔇 Microphone muted"
        );
    
    }
    
    
    // -------------------------
    // VOICE RECOGNITION
    // -------------------------
    
    function setupSpeech() {
    
        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;
    
    
        if (!SpeechRecognition) {
    
            console.warn(
                "Speech recognition is not supported."
            );
    
            return;
    
        }
    
    
        recognition = new SpeechRecognition();
    
    
        recognition.lang = "en-IN";
    
        recognition.interimResults = false;
    
        recognition.continuous = false;
    
    
        recognition.onstart = () => {

            // Stop GROOM if he is speaking
            stopGroomSpeaking();
        
            // Show that GROOM is listening
            status("🎤 Listening…");
        
            // Change mic button
            micBtn.innerHTML = "🗣️<small>Speaking</small>";
        
            micBtn.classList.add("speaking");
        };
    
    
        recognition.onresult = event => {
    
            const question =
                event.results[0][0].transcript;
    
    
            // Voice goes directly to GROOM.
            // Nothing is written on screen.
    
            askGroom(question);
    
        };
    
    
        recognition.onerror = event => {
    
            console.warn(
                "speech:",
                event.error
            );
    
            status("⚠️ Could not hear you");
    
        };
    
    
        recognition.onend = () => {

            micBtn.innerHTML = "🎤<small>Mic</small>";
        
            micBtn.classList.remove("speaking");
        
            if (!busy) {
                status("🟢 Live call");
            }
        };
    
    }
    
    
    // -------------------------
    // MIC BUTTON
    // -------------------------
    
    if (micBtn) {
    
        micBtn.onclick = () => {
    
            if (recognition && micOn) {
    
                // Interrupt GROOM immediately
                stopGroomSpeaking();
    
    
                try {
    
                    recognition.start();
    
                    return;
    
                } catch (error) {
    
                    console.warn(
                        "recognition",
                        error
                    );
    
                }
    
            }
    
    
            toggleMic();
    
        };
    
    }
    
    
    // -------------------------
    // CAMERA BUTTON
    // -------------------------
    
    if (cameraBtn) {
    
        cameraBtn.onclick = toggleCamera;
    
    }
    
    
    // -------------------------
    // END CALL
    // -------------------------
    
    function endCall() {
    
        stopGroomSpeaking();
    
        try {
    
            recognition?.stop();
    
        } catch (error) {}
    
    
        if (stream) {
    
            stream
                .getTracks()
                .forEach(track => track.stop());
    
        }
    
    
        stream = null;
    
        if (video) {
    
            video.srcObject = null;
    
        }
    
    
        location.href = "/";
    
    }
    
    
    if (endBtn) {
    
        endBtn.onclick = endCall;
    
    }
    
    
    // -------------------------
    // CLEANUP
    // -------------------------
    
    window.addEventListener(
        "beforeunload",
        () => {
    
            try {
    
                recognition?.stop();
    
            } catch (error) {}
    
    
            stopGroomSpeaking();
    
    
            if (stream) {
    
                stream
                    .getTracks()
                    .forEach(track => track.stop());
    
            }
    
        }
    );
    
    
    // -------------------------
    // START
    // -------------------------
    
    updateButtons();
    
    setupSpeech();
    
    startCamera();
    
    
    })();
    