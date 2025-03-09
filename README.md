# SpotiTool

SpotiTool is a Python automation script that scrapes new releases from your "My Beatport" page and creates a Spotify playlist with the latest tracks every week.

## Features
- Scrapes new releases from Beatport automatically
- Creates a new Spotify playlist every week with the latest tracks
- Prevents duplicates from being added to the playlist
- Runs on GitHub Actions for scheduled automation

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/SpotiTool.git
cd SpotiTool
```

### 2. Install Dependencies
Ensure you have Python 3.10+ installed. Then run:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add the following:
```ini
# Beatport Credentials
BEATPORT_USERNAME=your_beatport_email
BEATPORT_PASSWORD=your_beatport_password

# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:9090
SPOTIFY_REFRESH_TOKEN=your_spotify_refresh_token
```

### 4. Get Spotify Refresh Token
Before running the script, obtain your refresh token by running:
```bash
python GetRefreshToken.py
```
Follow the instructions to authorize the app and copy the token into `.env`.

### 5. Run the Script Locally
```bash
python SpotiTool.py
```

## Automating with GitHub Actions
This script is designed to run automatically via GitHub Actions.

### 1. Add Secrets to GitHub
Go to **Repo → Settings → Secrets and variables → Actions → New Repository Secret** and add:
- `BEATPORT_USERNAME`
- `BEATPORT_PASSWORD`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REFRESH_TOKEN`

### 2. Enable the GitHub Actions Workflow
Ensure that the `.github/workflows/main.yml` file is configured correctly. The script will run at the scheduled time and update your Spotify playlist.

## Troubleshooting
- If you see `Invalid refresh token`, regenerate the refresh token and update `.env`.
- If Spotify results are inaccurate, improve the track-matching logic.
- If the script is stuck during OAuth, clear `.spotify_cache` and retry.

## Future Improvements
- Better track matching using fuzzy search
- Email notifications for every workflow run
- Improved logging and monitoring

## License
This project is open-source and available under the MIT License.

