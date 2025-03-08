import os
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Load environment variables from .env
load_dotenv()

BEATPORT_USERNAME = os.getenv("BEATPORT_USERNAME")
BEATPORT_PASSWORD = os.getenv("BEATPORT_PASSWORD")

if not BEATPORT_USERNAME or not BEATPORT_PASSWORD:
    raise ValueError("Beatport username or password not set in .env file!")

# Load last scan date, or set the first scan max date to March 7, 2025
LAST_SCAN_FILE = "last_scan.json"
DEFAULT_MAX_DATE = "2025-03-07"

if os.path.exists(LAST_SCAN_FILE):
    with open(LAST_SCAN_FILE, "r") as f:
        last_scan_date = json.load(f).get("last_scan_date")
else:
    last_scan_date = DEFAULT_MAX_DATE  # First scan stops at March 7, 2025

# Configure Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in background
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# **1. Log in to Beatport**
driver.get("https://www.beatport.com/account/login")
time.sleep(3)  # Wait for page load

# Enter credentials
email_input = driver.find_element(By.NAME, "username")
password_input = driver.find_element(By.NAME, "password")

email_input.send_keys(BEATPORT_USERNAME)
password_input.send_keys(BEATPORT_PASSWORD, Keys.RETURN)

time.sleep(5)  # Wait for login

# **2. Navigate through multiple pages in "My Beatport"**
track_data = []
page = 1
stop_scraping = False

while not stop_scraping:
    driver.get(f"https://www.beatport.com/my-beatport?page={page}&per_page=150")
    time.sleep(3)

    # **3. Extract Page Source**
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    tracks = soup.find_all("div", {"data-testid": "tracks-table-row"})

    if not tracks:
        break  # Stop if no more tracks are found

    for track in tracks:
        # Extract track title and link
        track_a = track.select_one("a[href*='/track/']")
        track_name = track_a.text.strip() if track_a else "Unknown Track"
        track_link = f"https://www.beatport.com{track_a['href']}" if track_a else "N/A"

        # Remove "Original Mix" and "Extended Mix"
        track_name = track_name.replace("Original Mix", "").replace("Extended Mix", "").strip()

        # Extract release date
        release_date_element = track.find("div", class_=lambda x: x and "cell date" in x)
        release_date = release_date_element.text.strip() if release_date_element else "Unknown Date"

        # Stop scraping if we reach the last scan date
        if last_scan_date and release_date < last_scan_date:
            stop_scraping = True
            break

        # Check if there's an additional label and append if it contains "Remix" or "Instrumental"
        extra_span = track.find("span", class_=lambda x: x and "ReleaseName" in x)
        if extra_span:
            extra_text = extra_span.text.strip()
            if extra_text in ["Remix", "Instrumental"]:  # Strictly check for Remix or Instrumental
                track_name += f" ({extra_text})"

        # Find the first `<a>` tag linking to an artist (stable selector)
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

    page += 1  # Move to the next page

# Quit the browser after scraping
driver.quit()

# **4. Save the latest scan date**
if track_data:
    latest_date = max(track["Release Date"] for track in track_data if track["Release Date"] != "Unknown Date")
    with open(LAST_SCAN_FILE, "w") as f:
        json.dump({"last_scan_date": latest_date}, f)

# **5. Output Results**
for t in track_data:
    print(f"{t['Track']} by {t['Artist']} (Released: {t['Release Date']}) -> {t['Track Link']}")