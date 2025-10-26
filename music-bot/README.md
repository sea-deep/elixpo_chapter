Here’s a **cross-platform README** version with Linux/macOS and Windows instructions side by side:

---

# Elixpo Vibe — Discord Music Bot

This folder contains a small Discord music bot that uses **yt-dlp + FFmpeg** to stream audio into voice channels and provides slash commands and UI buttons for basic playback control.

## Contents

* `elixpo-vibe.py` — Main bot implementation (slash commands, player, controls)
* `register_commands.py` — Helper script to register/refresh slash commands during development
* `.env.example` — Example environment variables
* `requirements.txt` — Python dependencies

## Prerequisites

* Python 3.9+ (3.10 or 3.11 recommended)
* FFmpeg installed system-wide (required by discord.py to play audio)
* A Discord bot application and token (create one in the [Discord Developer Portal](https://discord.com/developers/applications))

## Quickstart

1. **Clone the repository** and navigate to the `music-bot` folder:

```bash
git clone https://github.com/Circuit-Overtime/elixpo_chapter.git
cd elixpo_chapter/music-bot
```

2. **Create and activate a virtual environment**

| Linux/macOS Terminal                                          | Windows PowerShell                                                                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `python3 -m venv venv`<br>`source venv/bin/activate` | `python -m venv venv`<br>`venv\Scripts\Activate.ps1`|

3. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:

```text
# Rename .env.example to .env and add your bot token
TOKEN=your_discord_bot_token_here
```

5. **Register slash commands**:

```bash
python register_commands.py
```

6. **Run the bot**:

```bash
python elixpo-vibe.py
```

## Notes and Tips

* Ensure the bot has these OAuth2 scopes when invited: `bot` and `applications.commands`.
* Enable "Message Content Intent" in the Discord Developer Portal.
* Minimum permissions for the invite: Connect, Speak, Send Messages, Embed Links, Use Slash Commands.

## Troubleshooting

* **FFmpeg missing errors**: Ensure `ffmpeg` is installed and in PATH (`which ffmpeg` on Linux/macOS, `where ffmpeg` on Windows).
* **yt-dlp errors**: Keep it up to date: `pip install -U yt-dlp`.
* **Permissions issues**: Check bot role & permissions in your guild and voice channel.
* **Rate-limiting / slash command delays**: Global commands can take time; use `register_commands.py` or guild-scoped registration during development.
