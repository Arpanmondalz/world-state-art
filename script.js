// --- DOM ELEMENTS ---
const canvas = document.getElementById('artCanvas');
const ctx = canvas.getContext('2d');

// State Containers
const introState = document.getElementById('introState');
const loadingState = document.getElementById('loadingState');
const artState = document.getElementById('artState');

// Buttons & Labels
const generateBtn = document.getElementById('generateBtn');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');
const timestampDisplay = document.getElementById('timestampDisplay');
const subtitle = document.getElementById('subtitle');

// Config
const CANVAS_WIDTH = 1240;
const CANVAS_HEIGHT = 1754;

// --- POOLS & HELPERS ---
const POOL = {
    dark: ["#2C3E50", "#1A1A2E", "#4A148C", "#1B4F72", "#641E16", "#145A32", "#212F3C", "#512E5F"],
    vibrant: ["#FF5733", "#C70039", "#FFC300", "#900C3F", "#2ECC71", "#E74C3C", "#8E44AD", "#D35400", "#F39C12", "#1ABC9C"],
    light: ["#FDFEFE", "#F4ECF7", "#FEF9E7", "#D5F5E3", "#FAD7A0", "#E8F8F5", "#D2B4DE", "#A9DFBF"]
};

function hexToRgb(hex) {
    let bigint = parseInt(hex.replace("#", ""), 16);
    return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
}

function draftColors(season, sentiment, entropy, seedStr) {
    let selected = [];
    let rng = new Math.seedrandom(seedStr + "_COLOR_DRAFT");
    function pickFrom(arr) { return arr[Math.floor(rng() * arr.length)]; }

    // Logic: Force Contrast
    if (season > 0.6) selected.push(pickFrom(POOL.dark));
    else selected.push(pickFrom(POOL.light));

    selected.push(pickFrom(POOL.vibrant));

    if (season > 0.6) selected.push(pickFrom(POOL.light));
    else selected.push(pickFrom(POOL.dark));

    if (entropy > 0.5) {
        selected.push(pickFrom(POOL.vibrant));
        selected.push(pickFrom(POOL.vibrant));
    } else {
        selected.push(pickFrom(POOL.light));
        selected.push(pickFrom(POOL.dark));
    }
    return selected.map(hexToRgb);
}

// --- STATE MANAGEMENT ---
let currentWorldData = null;
let lastGeneratedImageData = null;

function switchState(stateName) {
    introState.classList.add('hidden');
    loadingState.classList.add('hidden');
    artState.classList.add('hidden');

    if (stateName === 'intro') introState.classList.remove('hidden');
    if (stateName === 'loading') loadingState.classList.remove('hidden');
    if (stateName === 'art') artState.classList.remove('hidden');
}

// --- GENERATION FLOW ---
generateBtn.addEventListener('click', async () => {
    switchState('loading');

    try {
        // 1. Fetch
        const response = await fetch('world_data.json');
        if (!response.ok) throw new Error("Data fetch failed");
        currentWorldData = await response.json();

        // 2. Generate (with slight artificial delay for "Processing" feel)
        await new Promise(r => setTimeout(r, 1200));
        await generateArt(currentWorldData);

        // 3. Show Result & Change Text
        switchState('art');
        subtitle.innerText = "This is not AI generated art!";
        subtitle.style.color = "#f37c5fff"; // Gold accent

    } catch (err) {
        console.error(err);
        alert("Unable to capture world signal. Check console.");
        switchState('intro');
    }
});

resetBtn.addEventListener('click', () => {
    // Clear Canvas
    ctx.clearRect(0,0,CANVAS_WIDTH, CANVAS_HEIGHT);
    switchState('intro');
    
    // Reset Text
    subtitle.innerText = "Capture the current state of the world as a piece of art.";
    subtitle.style.color = "#666"; // Reset color
});

// --- ART LOGIC ---
async function generateArt(data) {
    const seedString = data.timestamp + "_RETRO_V7";
    const myRNG = new Math.seedrandom(seedString); 
    const simplex = new SimplexNoise(myRNG);       

    // Update UI Meta
    const dateObj = new Date(data.timestamp);
    timestampDisplay.innerText = dateObj.toLocaleDateString('en-US', { 
        year: 'numeric', month: 'short', day: '2-digit', 
        hour: '2-digit', minute:'2-digit'
    }).toUpperCase();

    const colors = draftColors(data.p_season, data.p_sentiment, data.p_entropy, seedString);
    const imageData = ctx.createImageData(CANVAS_WIDTH, CANVAS_HEIGHT);
    const pixels = imageData.data;

    const zoom = 0.002 + (data.p_humanity * 0.002); 
    const distortion = 100 + (data.p_entropy * 200); 
    const CHUNK_SIZE = 150; 

    for (let y = 0; y < CANVAS_HEIGHT; y++) {
        for (let x = 0; x < CANVAS_WIDTH; x++) {
            let xWarp = simplex.noise2D(x * zoom, y * zoom);
            let yWarp = simplex.noise2D((x + 1000) * zoom, (y + 1000) * zoom);
            let finalX = x + (xWarp * distortion);
            let finalY = y + (yWarp * distortion);
            let value = (simplex.noise2D(finalX * zoom, finalY * zoom) + 1) / 2;
            
            let grainAmount = 0.1 + (data.p_atmosphere * 0.1);
            let grain = (myRNG() - 0.5) * grainAmount;
            let ditheredValue = value + grain;

            let colIndex;
            if (ditheredValue < 0.30) colIndex = 0;       
            else if (ditheredValue < 0.50) colIndex = 1;  
            else if (ditheredValue < 0.70) colIndex = 2;  
            else if (ditheredValue < 0.85) colIndex = 3;  
            else colIndex = 4;                            

            if (colIndex < 0) colIndex = 0; if (colIndex > 4) colIndex = 4;
            let rgb = colors[colIndex];
            
            let r = rgb[0] + (grain * 30);
            let g = rgb[1] + (grain * 30);
            let b = rgb[2] + (grain * 30);

            const index = (y * CANVAS_WIDTH + x) * 4;
            pixels[index] = r; pixels[index + 1] = g; pixels[index + 2] = b; pixels[index + 3] = 255;
        }

        if (y % CHUNK_SIZE === 0) await new Promise(r => setTimeout(r, 0));
    }

    ctx.putImageData(imageData, 0, 0);
    lastGeneratedImageData = imageData;
}

// --- DOWNLOAD ---
downloadBtn.addEventListener('click', () => {
    if (lastGeneratedImageData) ctx.putImageData(lastGeneratedImageData, 0, 0);

    const dateObj = new Date(currentWorldData.timestamp);
    const fullText = `${dateObj.toDateString().toUpperCase()} | ${dateObj.toLocaleTimeString().toUpperCase()}`;

    ctx.save();
    ctx.font = "bold 28px 'Space Mono', monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.shadowColor = "rgba(0,0,0,0.8)";
    ctx.shadowBlur = 4;
    ctx.shadowOffsetX = 2;
    ctx.shadowOffsetY = 2;
    ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
    ctx.fillText(fullText, CANVAS_WIDTH / 2, CANVAS_HEIGHT - 50);
    ctx.restore();

    const link = document.createElement('a');
    link.download = `world_state_${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
});
