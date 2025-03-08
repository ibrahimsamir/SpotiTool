import os
import json
import time
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables
load_dotenv()

# Beatport Credentials
BEATPORT_USERNAME = os.getenv("BEATPORT_USERNAME")
BEATPORT_PASSWORD = os.getenv("BEATPORT_PASSWORD")

if not BEATPORT_USERNAME or not BEATPORT_PASSWORD:
    raise ValueError("Beatport username or password not set in .env file!")

# Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public playlist-modify-private"
    ),
    requests_timeout=30,  # Increase timeout to 30 seconds
    retries=5  # Retry failed requests up to 5 times
    )

# Fetch the current Spotify user ID
user_info = sp.current_user()
SPOTIFY_USERNAME = user_info["id"]
print(f"Authenticated as: {SPOTIFY_USERNAME}")

# Load last scan date or use a default
LAST_SCAN_FILE = "last_scan.json"
DEFAULT_MAX_DATE = "2025-03-07"

if os.path.exists(LAST_SCAN_FILE):
    with open(LAST_SCAN_FILE, "r") as f:
        last_scan_date = json.load(f).get("last_scan_date")
else:
    last_scan_date = DEFAULT_MAX_DATE

# Configure Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# **1. Log in to Beatport**
driver.get("https://www.beatport.com/account/login")
time.sleep(3)

email_input = driver.find_element(By.NAME, "username")
password_input = driver.find_element(By.NAME, "password")
email_input.send_keys(BEATPORT_USERNAME)
password_input.send_keys(BEATPORT_PASSWORD, Keys.RETURN)

time.sleep(5)

# **2. Scrape "My Beatport"**
track_data = []
page = 1
stop_scraping = False

while not stop_scraping:
    driver.get(f"https://www.beatport.com/my-beatport?page={page}&per_page=150")
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    tracks = soup.find_all("div", {"data-testid": "tracks-table-row"})

    if not tracks:
        break

    for track in tracks:
        loop_start = time.time()

        track_a = track.select_one("a[href*='/track/']")
        track_name = track_a.text.strip() if track_a else "Unknown Track"
        track_link = f"https://www.beatport.com{track_a['href']}" if track_a else "N/A"

        release_date_element = track.find("div", class_=lambda x: x and "cell date" in x)
        release_date = release_date_element.text.strip() if release_date_element else "Unknown Date"

        if last_scan_date and release_date < last_scan_date:
            stop_scraping = True
            break

        # **Fix 1: Remove 'Original Mix' and 'Extended Version'**
        track_name = re.sub(r"\s*\(?(Original Mix|Extended Version)\)?", "", track_name, flags=re.IGNORECASE).strip()

        # **Fix 2: Ensure remixes aren't duplicated**
        extra_span = track.find("span", class_=lambda x: x and "ReleaseName" in x)
        if extra_span:
            extra_text = extra_span.text.strip()

            if "Remix" in extra_text or "Instrumental" in extra_text:
                if extra_text.lower() not in track_name.lower():
                    track_name += f" ({extra_text})"

        # **Fix 3: Prevent Duplicate Track Names**
        if not any(t["Track"] == track_name for t in track_data):
            artist_a = track.select_one("a[href*='/artist/']")
            artist_name = artist_a.text.strip() if artist_a else "Unknown Artist"
            artist_link = f"https://www.beatport.com{artist_a['href']}" if artist_a else "N/A"

            track_data.append({
                "Track": track_name,
                "Artist": artist_name,
                "Track Link": track_link,
                "Artist Link": artist_link,
                "Release Date": release_date
            })

        loop_end = time.time()
        print(f"Processed track in {loop_end - loop_start:.4f} seconds")

    page += 1

driver.quit()

# **3. Save Last Scan Date**
if track_data:
    latest_date = max(track["Release Date"] for track in track_data if track["Release Date"] != "Unknown Date")
    with open(LAST_SCAN_FILE, "w") as f:
        json.dump({"last_scan_date": latest_date}, f)

# **4. Create Playlist in Spotify**
playlist_date = time.strftime("%y%m%d")  # YYMMDD format
playlist_name = f"{playlist_date}_Releases"
playlist_desc = "Weekly Beatport New Releases"

# Check if the playlist already exists
existing_playlists = sp.user_playlists(SPOTIFY_USERNAME)
playlist_id = None

for p in existing_playlists["items"]:
    if p["name"] == playlist_name:
        playlist_id = p["id"]
        print(f"✅ Using existing playlist: {playlist_name}")
        break

# Create a new playlist if it doesn't exist
if not playlist_id:
    playlist = sp.user_playlist_create(
        user=SPOTIFY_USERNAME,
        name=playlist_name,
        public=True,
        description=playlist_desc
    )
    playlist_id = playlist["id"]
    print(f"✅ New playlist created: {playlist['external_urls']['spotify']}")

# **5. Add Tracks to Spotify Playlist**
spotify_tracks = []

for track in track_data:
    query = f"{track['Track']} {track['Artist']}"
    results = sp.search(q=query, type="track", limit=1)

    if results["tracks"]["items"]:
        track_uri = results["tracks"]["items"][0]["uri"]
        spotify_tracks.append(track_uri)
    else:
        print(f"⚠️ Track not found on Spotify: {track['Track']} by {track['Artist']}")

# Add tracks to the playlist in batches of 100
BATCH_SIZE = 100

if spotify_tracks:
    for i in range(0, len(spotify_tracks), BATCH_SIZE):
        batch = spotify_tracks[i:i + BATCH_SIZE]
        sp.playlist_add_items(playlist_id, batch)
        print(f"✅ Added {len(batch)} tracks to {playlist_name} ({i + len(batch)}/{len(spotify_tracks)})")

    print(f"🎵 Successfully added {len(spotify_tracks)} tracks to {playlist_name}")
else:
    print("⚠️ No matching tracks found on Spotify.")

# **6. Output Results**
for t in track_data:
    print(f"{t['Track']} by {t['Artist']} (Released: {t['Release Date']}) -> {t['Track Link']}")