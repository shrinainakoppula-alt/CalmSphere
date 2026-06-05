const steps = [

{
title:"Head",
emoji:"🧠",
instruction:"Notice your forehead and scalp. Release any tension.",
tip:"Relax your jaw and eyebrows.",
id:"head"
},

{
title:"Face",
emoji:"😊",
instruction:"Soften your eyes and facial muscles.",
tip:"Allow your tongue to rest naturally.",
id:"face"
},

{
title:"Neck",
emoji:"🦴",
instruction:"Notice any stiffness in your neck.",
tip:"Let your shoulders fall naturally.",
id:"neck"
},

{
title:"Shoulders",
emoji:"💪",
instruction:"Release tension from your shoulders.",
tip:"Roll them once if comfortable.",
id:"shoulders"
},

{
title:"Chest",
emoji:"🫁",
instruction:"Observe your breathing.",
tip:"Take three slow breaths.",
id:"chest"
},

{
title:"Abdomen",
emoji:"🌀",
instruction:"Feel your stomach rise and fall.",
tip:"Breathe naturally.",
id:"abdomen"
},

{
title:"Legs",
emoji:"🦵",
instruction:"Notice sensations in your legs.",
tip:"Allow them to feel heavy.",
id:"legs"
},

{
title:"Feet",
emoji:"👣",
instruction:"Bring awareness to your feet.",
tip:"Feel the ground beneath them.",
id:"feet"
}

];

let current = 0;
let timerInterval;
let stepInterval;
let totalDuration = 0;
let stepDelayMs = 0;
let meditationStarted = false;
let paused = false;

const introScreen = document.getElementById("introScreen");
const instructionScreen = document.getElementById("instructionScreen");
const countdownScreen = document.getElementById("countdownScreen");
const meditationScreen = document.getElementById("meditationScreen");
const completeScreen = document.getElementById("completeScreen");
const durationInput = document.getElementById("durationInput");

function getDurationSeconds(){
    const minutes = parseInt(durationInput.value, 10);
    return minutes > 0 ? minutes * 60 : 300;
}

function formatTime(total){
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
}

let seconds = getDurationSeconds();

document.getElementById("beginBtn").onclick = () => {
    introScreen.classList.add("hidden");
    instructionScreen.classList.remove("hidden");
};

document.getElementById("startJourneyBtn").onclick = startCountdown;

document.getElementById("pauseBtn").onclick = pauseMeditation;
document.getElementById("resumeBtn").onclick = resumeMeditation;
document.getElementById("restartBtn").onclick = () => {
    location.reload();
};

function startCountdown(){
    instructionScreen.classList.add("hidden");
    countdownScreen.classList.remove("hidden");

    let count = 3;
    const interval = setInterval(() => {
        document.getElementById("countdownNumber").innerText = count;
        count--;

        if(count < 0){
            clearInterval(interval);
            countdownScreen.classList.add("hidden");
            meditationScreen.classList.remove("hidden");
            startMeditation();
        }
    }, 1000);
}

function updateStep(){
    const step = steps[current];
    document.getElementById("emoji").textContent = step.emoji;
    document.getElementById("title").textContent = step.title;
    document.getElementById("instruction").textContent = step.instruction;
    document.getElementById("tip").textContent = step.tip;
    document.getElementById("stepCounter").textContent = `Step ${current + 1} / ${steps.length}`;

    document.querySelectorAll(".body-region").forEach(el => el.classList.remove("active-region"));
    const activeRegion = document.getElementById(step.id);
    if(activeRegion){
        activeRegion.classList.add("active-region");
    }

    document.getElementById("progressBar").style.width = `${((current + 1) / steps.length) * 100}%`;

    if('speechSynthesis' in window){
        speechSynthesis.cancel();
        const speech = new SpeechSynthesisUtterance(step.instruction);
        speech.rate = 0.9;
        speechSynthesis.speak(speech);
    }
}

function startMeditation(){
    if(!meditationStarted){
        totalDuration = getDurationSeconds();
        seconds = totalDuration;
        stepDelayMs = Math.max(1, totalDuration / steps.length) * 1000;
        current = 0;
        meditationStarted = true;
    }

    paused = false;
    document.getElementById("timer").textContent = formatTime(seconds);
    updateStep();
    startTimers();
}

function startTimers(){
    clearInterval(timerInterval);
    clearInterval(stepInterval);

    timerInterval = setInterval(() => {
        seconds--;
        document.getElementById("timer").textContent = formatTime(seconds);
        if(seconds <= 0){
            finishMeditation();
        }
    }, 1000);

    stepInterval = setInterval(() => {
        current++;
        if(current >= steps.length){
            finishMeditation();
            return;
        }
        updateStep();
    }, stepDelayMs);
}

function pauseMeditation(){
    if(paused) return;
    paused = true;
    clearInterval(timerInterval);
    clearInterval(stepInterval);
}

function resumeMeditation(){
    if(!paused) return;
    paused = false;
    document.getElementById("timer").textContent = formatTime(seconds);
    updateStep();
    startTimers();
}

function finishMeditation(){
    clearInterval(stepInterval);
    clearInterval(timerInterval);
    meditationScreen.classList.add("hidden");
    completeScreen.classList.remove("hidden");
}
