# 🌍 World State Art

> Capture the pulse of planet Earth as generative art! This is NOT AI generated art, just pure data and math.

A living art generator that transforms real-world global data (flights, markets, news, climate, astronomy) into unique abstract prints. Every 30 minutes, the world changes. So does the art.

**[🎨 Try it Live](https://arpanmondalz.github.io/world-state-art/)**

***

## What Is This?

This project asks: **Can you freeze a moment of Earth's collective state as art?**

Instead of typing prompts into an AI, this system reads the actual world:
- 🛫 How many people are flying right now?
- 📉 How volatile are the markets?
- 📰 What's the sentiment of global news?
- 🌙 Where is the moon in its cycle?
- 🌡️ How much CO2 is in the atmosphere?
- 👥 What's the current population?

It feeds this data into a generative algorithm (Perlin noise + domain warping) to create a one-of-a-kind digital painting. Press the button, and you get a printable snapshot of that exact moment in time.

***

## How It Works

### 1. **Data Collection (Python)**
Every 30 minutes, `update_world_state.py` runs via GitHub Actions and:
- Counts planes in the sky (OpenSky API)
- Measures market volatility (VIX Index via yfinance)
- Analyzes news sentiment (Gemini AI + RSS feeds)
- Calculates moon phase (PyEphem)
- Estimates CO2 levels (Keeling Curve math)
- Tracks population growth (Linear model)

All values are normalized to 0.0–1.0 and saved in `world_data.json`.

### 2. **Art Generation (JavaScript)**
The frontend reads the JSON and:
- Picks colors based on season and sentiment
- Applies Perlin flow fields for organic curves
- Warps geometry based on market entropy
- Adds grain texture based on atmospheric CO2
- Renders a high-res (4960x7016px) downloadable image

***

## Run Locally

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Arpanmondalz/world-state-art.git
   cd world-state-art
   ```

2. **Generate data (optional):**
   ```bash
   pip install -r requirements.txt
   export GEMINI_API_KEY="your-key-here"
   python update_world_state.py
   ```

3. **Serve the site:**
   ```bash
   python3 -m http.server 8000
   ```
   Open `http://localhost:8000`

***

## Tech Stack

- **Data:** Python, yfinance, feedparser, PyEphem, Gemini API
- **Art:** Vanilla JavaScript, HTML5 Canvas, Simplex Noise
- **Automation:** GitHub Actions (cron job every 30 min)
- **Hosting:** GitHub Pages

***

## Project Structure

```
├── index.html          # Main page
├── style.css           # Styling
├── script.js           # Generative art engine
├── update_world_state.py  # Data fetching script
├── world_data.json     # Live data (auto-updated)
└── .github/workflows/
    └── update_data.yml # Automation config
```

***

## License

MIT License. Feel free to remix, print, or build on this.

***

## Credits

Built by [Arpan Mondal](https://youtube.com/@makestreme) as an experiment in data-driven art.

*"Art is how we decorate space. Music is how we decorate time. Data is how we decorate reality."*

[1](https://github.com/Arpanmondalz/world-state-art)
