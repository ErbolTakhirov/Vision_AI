const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const video = document.getElementById('camera-feed');
const canvas = document.getElementById('hidden-canvas');
const statusDisplay = document.getElementById('status-display');
const navToggle = document.getElementById('nav-mode-toggle');
const micBtn = document.getElementById('mic-btn');
const analyzeBtn = document.getElementById('analyze-btn');

// UI State
let isAnalyzing = false;
let isSpeaking = false;
let isListening = false;
let isNavigatorMode = false;
let navigatorInterval = null;

// Audio Context for Beeps
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function beep(freq = 440, duration = 100, type = 'sine') {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.00001, audioCtx.currentTime + duration / 1000);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration / 1000);
}

function playSuccessBeep() { beep(880, 100); }
function playErrorBeep() { beep(150, 300, 'sawtooth'); }
function playSnapshotBeep() { beep(1200, 50); }

// Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
let wakeWordMode = true;

function setupSpeechRecognition() {
    if (!SpeechRecognition) return;
    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.interimResults = true;
    recognition.continuous = true;

    recognition.onstart = () => {
        isListening = true;
        if (!isNavigatorMode) updateStatus("Слушаю... Скажите 'Эй Вижн'");
    };

    recognition.onerror = (event) => {
        if (!isNavigatorMode) setTimeout(startRecognition, 1000);
    };

    recognition.onend = () => {
        isListening = false;
        if (!isAnalyzing && !isSpeaking && !isNavigatorMode) {
            setTimeout(startRecognition, 1000);
        }
    };

    recognition.onresult = (event) => {
        if (isNavigatorMode) return; // Ignore voice in navigator mode

        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            }
        }
        if (finalTranscript) processVoiceCommand(finalTranscript.toLowerCase());
    };
}

function startRecognition() {
    if (isListening || isAnalyzing || isSpeaking || isNavigatorMode) return;
    try { recognition.start(); } catch (e) { }
}

function stopRecognition() {
    try { recognition.stop(); } catch (e) { }
}

function processVoiceCommand(text) {
    const triggers = ['вижн', 'vision', 'вижен', 'вижу', 'вежн'];
    const hasTrigger = triggers.some(t => text.includes(t));

    if (wakeWordMode && hasTrigger) {
        wakeWordMode = false;
        tg.HapticFeedback.impactOccurred('heavy');
        playSuccessBeep();
        performAnalysis(text);
    }
}

// Analysis Logic
async function performAnalysis(text) {
    if (isAnalyzing) return;
    isAnalyzing = true;
    wakeWordMode = false;
    stopRecognition();

    updateStatus("Анализирую...");
    if (analyzeBtn) analyzeBtn.classList.add('pulse');
    playSnapshotBeep();

    try {
        const imageBlob = await getSnapshotBlob();
        const userId = tg.initDataUnsafe?.user?.id || 'anonymous_web';

        await sendData(imageBlob, null, text, userId, 'chat');

    } catch (e) {
        console.error("Analysis failed", e);
        playErrorBeep();
        finishCycle();
    }
}

// Navigator Logic
function toggleNavigator(enabled) {
    isNavigatorMode = enabled;
    if (enabled) {
        stopRecognition();
        updateStatus("Навигатор включен");
        playSuccessBeep();
        navigatorInterval = setInterval(runNavigatorStep, 3500); // Every 3.5s
    } else {
        clearInterval(navigatorInterval);
        updateStatus("Навигатор выключен");
        playSuccessBeep();
        startRecognition();
    }
}

async function runNavigatorStep() {
    if (isSpeaking) return; // Don't interrupt speaking

    try {
        // playSnapshotBeep(); // Optional, might be annoying
        const imageBlob = await getSnapshotBlob();
        const userId = tg.initDataUnsafe?.user?.id || 'anonymous_web';

        // Send with mode='navigator'
        const formData = new FormData();
        formData.append('image', imageBlob, 'frame.jpg');
        formData.append('user_id', userId);
        formData.append('mode', 'navigator');

        const response = await fetch('/api/smart-analyze/', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.message && data.message.trim().length > 0) {
            tg.HapticFeedback.notificationOccurred('success');
            speakSystem(data.message);
        }
    } catch (e) {
        console.error("Nav error", e);
    }
}

function speakSystem(text) {
    // Quick browser TTS for navigator (faster than server often) or use server if reliable
    // Let's use browser for Navigator to save server/traffic
    if ('speechSynthesis' in window) {
        isSpeaking = true;
        const ut = new SpeechSynthesisUtterance(text);
        ut.lang = 'ru-RU';
        ut.rate = 1.2;
        ut.onend = () => { isSpeaking = false; };
        window.speechSynthesis.speak(ut);
    }
}

// Camera & Init
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
        video.srcObject = stream;
        video.play().catch(console.error);
        setupSpeechRecognition();
        startRecognition();
    } catch (err) {
        statusDisplay.innerText = "Нет камеры";
    }
}

function getSnapshotBlob() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    return new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
}

function playAudioResponse(base64Audio) {
    if (!base64Audio) { finishCycle(); return; }
    isSpeaking = true;
    const audioStr = "data:audio/mp3;base64," + base64Audio;
    const audio = new Audio(audioStr);
    audio.onended = () => { finishCycle(); };
    audio.play().catch(e => { finishCycle(); });
}

function finishCycle() {
    isSpeaking = false;
    isAnalyzing = false;
    wakeWordMode = true;
    if (analyzeBtn) analyzeBtn.classList.remove('pulse');
    if (!isNavigatorMode) startRecognition();
    updateStatus("Скажите 'Эй Вижн'...");
}

async function sendData(imageBlob, audioBlob, text, userId, mode) {
    const formData = new FormData();
    if (imageBlob) formData.append('image', imageBlob, 'frame.jpg');
    if (text) formData.append('text', text);
    formData.append('user_id', userId);
    formData.append('mode', mode);

    try {
        const response = await fetch('/api/smart-analyze/', { method: 'POST', body: formData });
        const data = await response.json();
        if (mode === 'chat') {
            if (data.message) updateStatus(data.message.substring(0, 30) + "...");
            playAudioResponse(data.audio);
        }
    } catch (err) {
        throw err;
    }
}

function updateStatus(text) { statusDisplay.innerText = text; }

startCamera();

// Event Listeners
if (navToggle) {
    navToggle.addEventListener('change', (e) => {
        toggleNavigator(e.target.checked);
    });
}
if (analyzeBtn) analyzeBtn.addEventListener('click', () => performAnalysis("Что передо мной?"));
if (micBtn) micBtn.style.display = 'none';
