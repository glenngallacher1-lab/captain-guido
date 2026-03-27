# Captain Guido Admin Bot — Setup Guide

A Telegram bot that lets Glenn and Jude update the live website
from their phones — no code required.

## What it can do

| Command | What happens |
|---|---|
| `/status` | Shows current site config — launched mode, stats, which chapters are unlocked |
| `/unlock` | Shows a button list of chapters to unlock — tap one, it goes live on the map |
| `/stats` | Guided flow to update lbs removed, miles cleaned, donations, USD donated |
| `/milestone` | Add a cleanup milestone to the Impact section |
| `/launch` | Flips the site from pre-launch to LIVE mode (confirmation required) |

---

## One-time setup (15 minutes)

### Step 1 — Create the Telegram bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Name it: `Captain Guido Admin`
4. Username: something like `captainguidoadmin_bot`
5. BotFather gives you a **token** — copy it

### Step 2 — Get your Telegram user IDs

1. Search Telegram for **@userinfobot**
2. Send it `/start`
3. It replies with your user ID (a number like `123456789`)
4. Jude does the same and sends you his ID

### Step 3 — Create a GitHub personal access token

1. Go to github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click **Generate new token**
3. Repository access: select `glenngallacher1-lab/captain-guido`
4. Permissions: **Contents → Read and write**
5. Copy the token

### Step 4 — Deploy on Railway (free)

1. Go to **railway.app** and sign up (free tier is enough)
2. Click **New Project → Deploy from GitHub repo**
3. Connect this `admin-bot` folder (or push it to its own repo)
4. In Railway dashboard → Variables, add these environment variables:

```
TELEGRAM_BOT_TOKEN   = <from BotFather>
GITHUB_TOKEN         = <from Step 3>
GITHUB_REPO          = glenngallacher1-lab/captain-guido
AUTHORIZED_USERS     = 123456789,987654321   ← Glenn's ID, Jude's ID
```

5. Railway auto-deploys. The bot is live.

### Step 5 — Start the bot

Open Telegram, find your bot by username, send `/start`.
Share the bot username with Jude — he can now use all commands too.

---

## Deployment files

If deploying to Railway, add a `Procfile`:
```
worker: python bot.py
```

---

## Updating the allowed users later

Just update the `AUTHORIZED_USERS` environment variable in Railway
and redeploy. No code changes needed.
