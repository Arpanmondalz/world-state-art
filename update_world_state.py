import json
import os
import math
import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import feedparser
import yfinance as yf
import ephem


# --- CONFIG ---
OUTPUT_FILE = "world_data.json"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# --- HELPER: ROBUST REQUESTS ---
def get_session():
    """Creates a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# --- 1. COSMIC (Moon Phase) ---
def get_cosmic_value():
    try:
        # Modern UTC handling
        date = datetime.datetime.now(datetime.timezone.utc)
        moon = ephem.Moon(date)
        return round(moon.phase / 100.0, 4)
    except Exception as e:
        print(f"Cosmic Error: {e}")
        return 0.5

# --- 2. ASCENSION (People in Sky) ---
def get_ascension_value():
    session = get_session()
    try:
        # Astros
        astro_count = 10
        try:
            r = session.get("http://api.open-notify.org/astros.json", timeout=10)
            if r.status_code == 200:
                astro_count = r.json().get('number', 10)
        except: pass

        # Planes
        plane_count = 10000
        try:
            r = session.get("https://opensky-network.org/api/states/all", timeout=20)
            if r.status_code == 200:
                data = r.json()
                if data and data['states']:
                    plane_count = len(data['states'])
        except:
            # Fallback estimation
            h = datetime.datetime.now(datetime.timezone.utc).hour
            plane_count = 9000 + (4000 * math.sin((h - 9) * math.pi / 12))

        print(f"Ascension: Planes={plane_count}, Astros={astro_count}")
        
        # Normalize: Min 4000, Max 16000
        norm = (plane_count - 4000) / 12000
        return max(0.0, min(1.0, norm))

    except Exception as e:
        print(f"Ascension Error: {e}")
        return 0.7

# --- 3. ENTROPY (Market Fear) ---
def get_entropy_value():
    try:
        # VIX
        vix_val = 20.0
        try:
            # Suppress yfinance print spam
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="5d")
            if not hist.empty:
                vix_val = hist['Close'].iloc[-1]
        except: pass

        # BTC
        btc_change = 2.0
        try:
            btc = yf.Ticker("BTC-USD")
            hist = btc.history(period="2d")
            if len(hist) >= 2:
                c1 = hist['Close'].iloc[-1]
                c2 = hist['Close'].iloc[-2]
                btc_change = abs((c1 - c2) / c2) * 100
        except: pass

        print(f"Entropy: VIX={vix_val:.2f}, BTC={btc_change:.2f}%")

        # Normalize
        norm_vix = (vix_val - 10) / 50
        norm_btc = btc_change / 10
        
        val = (norm_vix * 0.7) + (norm_btc * 0.3)
        return max(0.0, min(1.0, val))

    except Exception as e:
        print(f"Entropy Error: {e}")
        return 0.35

# --- 4. SENTIMENT (AI Judge) ---
def get_sentiment_value():
    if not GEMINI_KEY:
        print("Sentiment: No API Key")
        return 0.5
        
    session = get_session()
    try:
        # 1. Fetch Headlines
        headlines = []
        urls = [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best"
        ]
        
        for u in urls:
            try:
                # Use requests to fetch content first for stability
                r = session.get(u, timeout=10)
                if r.status_code == 200:
                    feed = feedparser.parse(r.content)
                    for entry in feed.entries[:3]: # Top 3 from each
                        headlines.append(entry.title)
            except: continue

        if not headlines: 
            print("Sentiment: No headlines found.")
            return 0.5

        # 2. Prepare Gemini Request
        MODEL_ID = "gemini-2.5-flash"
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={GEMINI_KEY}"
        
        headline_text = "; ".join(headlines)
        system_instruction = (
            "You are a global sentiment analyzer. Analyze the collective sentiment of the "
            "provided news headlines on a scale of 0.0 (Apocalyptic/War/Disaster) to "
            "1.0 (Utopian/Peace/Progress). Return a JSON object with a single key 'score' "
            "containing the float value."
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": system_instruction},
                    {"text": f"Here are the news headlines:\n{headline_text}"}
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        # 3. Execute Request
        response = session.post(
            API_URL, 
            headers={"Content-Type": "application/json"}, 
            json=payload,
            timeout=30 # Increased timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # Parse JSON response from Gemini
            data = json.loads(text_response)
            val = float(data.get("score", 0.5))
            
            print(f"Sentiment (Gemini): {val}")
            return max(0.0, min(1.0, val))
        else:
            print(f"Gemini API Error: {response.status_code} - {response.text}")
            return 0.5

    except Exception as e:
        print(f"Sentiment Error: {e}")
        return 0.5

# --- 5. ATMOSPHERE (Math) ---
def get_atmosphere_value():
    base = 422.0
    now = datetime.datetime.now(datetime.timezone.utc)
    
    years = now.year - 2024
    trend = years * 2.4
    
    day = now.timetuple().tm_yday
    osc = 3.5 * math.cos(2 * math.pi * (day - 10) / 365)
    
    curr = base + trend + osc
    print(f"Atmosphere CO2: {curr:.2f}")
    
    return max(0.0, min(1.0, (curr - 415) / 35))

# --- 6. HUMANITY (Math) ---
def get_humanity_value():
    base = 8_045_000_000
    date_base = datetime.datetime(2023, 7, 1, tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    
    secs = (now - date_base).total_seconds()
    curr = base + (secs * 2.2)
    
    return max(0.0, min(1.0, (curr - 8_000_000_000) / 2_000_000_000))

# --- 7. SEASON (Math) ---
def get_season_value():
    day = datetime.datetime.now(datetime.timezone.utc).timetuple().tm_yday
    return (math.cos((day + 10) * 2 * math.pi / 365) + 1) / 2

# --- MAIN ---
if __name__ == "__main__":
    print("--- UPDATE START ---")
    data = {
        "p_season": round(get_season_value(), 4),
        "p_ascension": round(get_ascension_value(), 4),
        "p_entropy": round(get_entropy_value(), 4),
        "p_sentiment": round(get_sentiment_value(), 4),
        "p_cosmic": round(get_cosmic_value(), 4),
        "p_atmosphere": round(get_atmosphere_value(), 4),
        "p_humanity": round(get_humanity_value(), 4),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("--- UPDATE SUCCESS ---")
