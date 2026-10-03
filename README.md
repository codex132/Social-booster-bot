# 🔥 Social Booster Bot

A free Telegram bot that boosts your **TikTok**, **YouTube**, and **Instagram** — no payment, no API keys, no limits.

---

## What It Does

| Platform | Service | Method |
|---|---|---|
| TikTok | Followers, Views, Likes, Shares, Favorites, Comment Likes | Automates [zefoy.com](https://zefoy.com) — free, no login |
| YouTube | Views | Runs [MShawon/YouTube-Viewer](https://github.com/MShawon/YouTube-Viewer) headless |
| Instagram | Followers | Follow-back method (follows target's followers → they follow back) |

---

## Bot Commands

| Command | Who | What |
|---|---|---|
| `/start` | everyone | shows the main menu |
| `/cancel` | everyone | cancel current flow |
| `/stats` | admin only | total users + boost breakdown |
| `/users` | admin only | full user list |
| `/broadcast <text>` | admin only | send message to all users |

---

## Deploy on Railway / Render / Koyeb (free tier)

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `ADMIN_ID` | ✅ | Your Telegram numeric user ID (get from [@userinfobot](https://t.me/userinfobot)) |
| `IG_USERNAME` | Only for Instagram | Your Instagram username |
| `IG_PASSWORD` | Only for Instagram | Your Instagram password |
| `IG_TARGET` | Only for Instagram | Account whose followers you'll follow (e.g. `cristiano`) |

### Steps

```
1. Fork this repo
2. Connect to Railway / Render
3. Set environment variables above
4. Deploy — nixpacks.toml handles chromium install automatically
```

---

## Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/social-booster-bot
cd social-booster-bot

pip install -r requirements.txt

export BOT_TOKEN="your_token"
export ADMIN_ID="your_id"
export IG_USERNAME="your_ig"
export IG_PASSWORD="your_pass"
export IG_TARGET="target_account"

python bot.py
```

### Termux (Android)

```bash
pkg update && pkg install python git chromium
pip install -r requirements.txt
python bot.py
```

---

## How to Hit 10k

| Platform | Strategy | Time |
|---|---|---|
| TikTok followers/views | 200 loops overnight = ~10,000 | 1 night |
| YouTube views | 4 threads × 8 h = ~3,800 views/night | 3 nights |
| Instagram followers | 100 follows/day × 30% follow-back = 30 real/day | 30–40 days |

TikTok and YouTube are pure automation — set loops high and let it run overnight.

---

## File Structure

```
social-booster-bot/
├── bot.py              ← Telegram bot (aiogram 3)
├── tiktok_boost.py     ← zefoy.com selenium automator
├── youtube_boost.py    ← YouTube-Viewer wrapper
├── instagram_boost.py  ← Instagram follow-back engine
├── db.py               ← SQLite: users + boost logs
├── requirements.txt
├── nixpacks.toml       ← for Railway / Nixpacks deployment
├── Procfile            ← for Heroku-compatible platforms
└── README.md
```

---

## Notes

- YouTube views can partially drop after 24–48 h without residential proxies. Run longer sessions and loop daily for sticky counts.
- Instagram: keep follows under 100/session and 200/day to avoid temporary action blocks.
- zefoy.com may have services offline occasionally — the bot will tell you which services are live.
- Chromium is installed automatically via `nixpacks.toml` on cloud platforms.
