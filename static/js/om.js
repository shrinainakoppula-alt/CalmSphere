const timer = document.getElementById("timer");
const startBtn = document.getElementById("startBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resetBtn = document.getElementById("resetBtn");
const durationInput = document.getElementById("durationInput");
const omAudio =
new Audio("/static/sounds/om_chant.mp3");

omAudio.loop = true;

omAudio.volume = 0.4;

function getSelectedSeconds() {
    const minutes = parseInt(durationInput.value, 10);
    return minutes > 0 ? minutes * 60 : 300;
}

let totalSeconds = getSelectedSeconds();
let interval;
let isRunning = false;

durationInput.addEventListener("input", () => {
    if (!isRunning) {
        totalSeconds = getSelectedSeconds();
        updateTimer();
    }
});

function updateTimer() {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    timer.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function setTime(seconds){
    totalSeconds = seconds;
    updateTimer();
}

function startMeditation() {
    if (isRunning) return;
    totalSeconds = getSelectedSeconds();
    updateTimer();
    isRunning = true;
    omAudio.play();
    interval = setInterval(() => {
        totalSeconds -= 1;
        updateTimer();
        if (totalSeconds <= 0) {
            clearInterval(interval);
            isRunning = false;
            totalSeconds = 0;
            updateTimer();
            alert("🌟 Om Meditation Complete");
        }
    }, 1000);
}

function pauseMeditation() {
    if (!isRunning) return;
    isRunning = false;
    omAudio.pause();
    clearInterval(interval);
}

function resetMeditation() {
    clearInterval(interval);
    isRunning = false;
    omAudio.pause();
    omAudio.currentTime = 0;
    totalSeconds = getSelectedSeconds();
    updateTimer();
}

const quotes = [
"Let the divine energy flow within you",
"Silence is the language of the soul",
"Peace begins with a single breath",
"The universe resides within you"
];

startBtn.addEventListener("click", startMeditation);
pauseBtn.addEventListener("click", pauseMeditation);
resetBtn.addEventListener("click", resetMeditation);
updateTimer();
