# CGC Admin Panel — Setup Guide

A password-protected web dashboard for Glenn + Jude to update the live website from any browser — no code required.

## What it does

| Action | Result |
|---|---|
| **Status** | See current site mode, all stats, which chapters are unlocked |
| **Chapter Unlock** | Tap any chapter button — map marker turns gold on the live site |
| **Update Stats** | Set lbs removed, miles cleaned, donations, USD donated |
| **Add Milestone** | Add a cleanup milestone to the Impact section |
| **Go Live** | Flip the site from pre-launch to live mode |

Changes go live on the website within ~2 minutes (GitHub Pages cache).

---

## Setup (one time, ~15 minutes)

### Step 1 — GitHub personal access token

1. Go to **github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click **Generate new token**
3. Repository access: select only `glenngallacher1-lab/captain-guido`
4. Permissions: **Contents → Read and write**
5. Copy the token (starts with `github_pat_...`)

### Step 2 — Deploy the Cloudflare Worker

The Worker is the secure backend — it holds your GitHub token and validates the password.

1. Go to **cloudflare.com** → sign up free
2. Dashboard → **Workers & Pages → Create → Worker**
3. Name it `cgc-admin`
4. Click **Edit code** → paste the contents of `worker.js` → **Deploy**
5. Go to **Settings → Variables** and add:

| Variable | Value |
|---|---|
| `ADMIN_PASSWORD` | A strong shared password (e.g. `hashwind2026`) |
| `GITHUB_TOKEN` | The token from Step 1 |
| `GITHUB_REPO` | `glenngallacher1-lab/captain-guido` |

6. Copy your Worker URL — looks like `https://cgc-admin.yourname.workers.dev`

### Step 3 — Open the admin panel

- Open `admin-panel/index.html` directly in a browser (double-click the file, or host it on GitHub Pages)
- Enter your Worker URL and password
- Done — bookmark it

**Share with Jude:**
Send him the `index.html` file + the Worker URL + the password.
He opens the file in his browser and logs in the same way.

---

## Hosting the panel on GitHub Pages (optional)

If you want a permanent URL instead of opening a local file:

1. Move `admin-panel/index.html` to the root of the repo as `admin.html`
2. Access it at `glenngallacher1-lab.github.io/captain-guido/admin.html`
3. The password gate protects it — no one can do anything without the password

---

## Security notes

- The GitHub token is stored **only in Cloudflare** — never in the HTML file
- The password is validated server-side on every request
- The admin panel HTML itself contains no secrets
- Cloudflare Workers free tier: 100,000 requests/day — more than enough
