const introAudio = new Audio("/static/sounds/intro.wav");

const breatheInAudio = new Audio("/static/sounds/breathe_in.wav");

const holdAudio = new Audio("/static/sounds/hold.wav");

const breatheOutAudio = new Audio("/static/sounds/breathe_out.wav");

const completeAudio = new Audio("/static/sounds/complete.wav");

const rainAudio = new Audio("/static/sounds/rain.mp3");

const completionModal =
    document.getElementById("completionModal");

    const progressCircle =
document.querySelector(".progress-circle");

rainAudio.loop = true;
rainAudio.volume = 1;

const particleContainer = document.getElementById("particles");

for(let i = 0; i < 80; i++){

    const particle = document.createElement("div");

    particle.classList.add("particle");

    const size = Math.random() * 6 + 2;

    particle.style.width = size + "px";
    particle.style.height = size + "px";

    particle.style.left = Math.random() * 100 + "%";

    particle.style.animationDuration =
        (10 + Math.random() * 20) + "s";

    particle.style.animationDelay =
        Math.random() * 10 + "s";

    particleContainer.appendChild(particle);
}
const phaseText = document.getElementById("phase");
const orb = document.getElementById("orb");
const timerDisplay = document.getElementById("timer");
const durationInput = document.getElementById("durationInput");

const startBtn = document.getElementById("startBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resetBtn = document.getElementById("resetBtn");

let breathingTimeout;
let countdownInterval;

let isRunning = false;
let isPaused = false;
let pausedPhase = null;

function getSelectedSeconds(){
    const minutes = parseInt(durationInput.value, 10);
    return minutes > 0 ? minutes * 60 : 300;
}

let selectedDuration = getSelectedSeconds();
let totalSeconds = selectedDuration;

durationInput.addEventListener("input", () => {
    if (!isRunning) {
        selectedDuration = getSelectedSeconds();
        totalSeconds = selectedDuration;
        updateTimer();
        updateProgress();
    }
});

function closeCompletionModal(){

    completionModal.style.display = "none";
}

const phases = [
    {
        display: "Breathe In",
        voice: "Take a deep breath in",
        duration: 5000,
        expand: true
    },
    {
        display: "Hold",
        voice: "Hold your breath",
        duration: 4000,
        expand: true
    },
    {
        display: "Breathe Out",
        voice: "Slowly breathe out",
        duration: 7000,
        expand: false
    }
];

let currentPhase = 0;

function updateTimer() {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    timerDisplay.textContent =
        `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function runPhase() {

    if (!isRunning) return;

    const phase = phases[currentPhase];

    phaseText.textContent = phase.display;

    if (phase.display === "Breathe In") {
        breatheInAudio.currentTime = 0;
        breatheInAudio.play();
    }

    if (phase.display === "Hold") {
        holdAudio.currentTime = 0;
        holdAudio.play();
    }

    if (phase.display === "Breathe Out") {
        breatheOutAudio.currentTime = 0;
        breatheOutAudio.play();
    }

    if (phase.expand) {
        orb.classList.add("expand");
    } else {
        orb.classList.remove("expand");
    }

    breathingTimeout = setTimeout(() => {

        currentPhase = (currentPhase + 1) % phases.length;

        runPhase();

    }, phase.duration);
}

function startMeditation() {
    if (isPaused) {
        isPaused = false;
        isRunning = true;
        rainAudio.play();

        countdownInterval = setInterval(() => {
            totalSeconds--;
            updateTimer();

            if (totalSeconds <= 0) {
                clearInterval(countdownInterval);
                clearTimeout(breathingTimeout);
                isRunning = false;
                phaseText.textContent = "Session Complete 🌟";
                completionModal.style.display = "flex";
                rainAudio.pause();
                rainAudio.currentTime = 0;
                completeAudio.currentTime = 0;
                completeAudio.play();
            }
        }, 1000);

        currentPhase = pausedPhase;
        runPhase();
        return;
    }

    if (isRunning) return;

    selectedDuration = getSelectedSeconds();
    totalSeconds = selectedDuration;
    updateTimer();
    updateProgress();

    isRunning = true;
    phaseText.textContent = "Relax and Focus";
    introAudio.currentTime = 0;
    introAudio.play();

    setTimeout(() => {
        rainAudio.play();
        runPhase();
    }, 10000);

    countdownInterval = setInterval(() => {
        totalSeconds--;
        updateTimer();

        if (totalSeconds <= 0) {
            clearInterval(countdownInterval);
            clearTimeout(breathingTimeout);
            isRunning = false;
            phaseText.textContent = "Session Complete 🌟";
            completeAudio.currentTime = 0;
            completeAudio.play();
        }
    }, 1000);
}

function pauseMeditation() {
    
    isPaused = true;
    isRunning = false;
    rainAudio.pause();

    pausedPhase = currentPhase;

    clearInterval(countdownInterval);
    clearTimeout(breathingTimeout);

    introAudio.pause();
    breatheInAudio.pause();
    holdAudio.pause();
    breatheOutAudio.pause();
}

function resetMeditation() {

    completionModal.style.display = "none";

    isPaused = false;

introAudio.pause();
breatheInAudio.pause();
holdAudio.pause();
breatheOutAudio.pause();

introAudio.currentTime = 0;
breatheInAudio.currentTime = 0;
holdAudio.currentTime = 0;
breatheOutAudio.currentTime = 0;

    isRunning = false;

    clearInterval(countdownInterval);
    clearTimeout(breathingTimeout);

    selectedDuration = getSelectedSeconds();
    totalSeconds = selectedDuration;
    currentPhase = 0;

    updateTimer();
    updateProgress();

    phaseText.textContent = "Ready to Begin";

    orb.classList.remove("expand");
}

function setDuration(seconds){

    if(isRunning) return;

    totalSeconds = seconds;
    selectedDuration = seconds;

    updateTimer();
    updateProgress();
}

function updateProgress(){

    const circumference = 754;

    const progress =
        totalSeconds / selectedDuration;

    progressCircle.style.strokeDashoffset =
        circumference * (1 - progress);
}

window.setDuration = setDuration;
startBtn.addEventListener("click", startMeditation);
pauseBtn.addEventListener("click", pauseMeditation);
resetBtn.addEventListener("click", resetMeditation);

updateTimer();
updateProgress();