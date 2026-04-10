#!/usr/bin/env python3
"""
CGC Telegram Bot — controls the Captain Guido Coin website via chat commands.
Reads/writes config.json on GitHub. Changes are live on the site within ~30s.
"""

import os, json, base64, logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# ── Env vars ────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.environ['TELEGRAM_BOT_TOKEN']
GH_TOKEN   = os.environ['GITHUB_TOKEN']
REPO_OWNER = 'captainguidotoken-ops'
REPO_NAME  = 'captain-guido'

# Optional: restrict to specific chat IDs (comma-separated in env var)
# Leave ALLOWED_CHAT_IDS empty to allow any chat (set it once you know your GC id)
_raw = os.environ.get('ALLOWED_CHAT_IDS', '')
ALLOWED = set(int(x.strip()) for x in _raw.split(',') if x.strip())

# ── GitHub helpers ───────────────────────────────────────────────────────────
GH_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/config.json'
GH_GET = {'Authorization': f'Bearer {GH_TOKEN}', 'Accept': 'application/vnd.github+json'}
GH_PUT = {**GH_GET, 'Content-Type': 'application/json'}

async def read_config():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(GH_URL, headers=GH_GET)
        r.raise_for_status()
        d = r.json()
        cfg = json.loads(base64.b64decode(d['content'].replace('\n', '')))
        return cfg, d['sha']

async def write_config(cfg, sha, message):
    body = {
        'message': f'bot: {message}',
        'content': base64.b64encode(json.dumps(cfg, indent=2).encode()).decode(),
        'sha': sha,
    }
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.put(GH_URL, headers=GH_PUT, json=body)
        r.raise_for_status()

# ── Auth guard ───────────────────────────────────────────────────────────────
def allowed(update: Update) -> bool:
    if not ALLOWED:
        return True
    return update.effective_chat.id in ALLOWED

def zpad(n: str) -> str:
    return n.strip().lstrip('0').zfill(2)  # '3' -> '03', '03' -> '03'

# ── Commands ─────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_help(update, ctx)

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    text = (
        '🚢 *CGC Bot — Commands*\n\n'
        '*Site*\n'
        '`/status` — show live site config\n'
        '`/maintenance on|off` — toggle holding page\n\n'
        '*Chapters*\n'
        '`/unlock 3` — unlock chapter 03\n'
        '`/unlock all` — unlock every chapter\n'
        '`/lock 3` — lock chapter 03\n'
        '`/lock all` — lock every chapter\n\n'
        '*Stats \\(hero counters\\)*\n'
        '`/set lbs 8500` — update lbs removed\n'
        '`/set miles 62` — update miles cleaned\n'
        '`/set chapters 12` — update chapter count\n\n'
        '*Social links*\n'
        '`/social twitter https://twitter.com/...`\n'
        '`/social discord https://discord.gg/...`\n'
        '`/social telegram https://t.me/...`\n\n'
        '_Changes go live on the site within ~30 seconds._'
    )
    await update.message.reply_text(text, parse_mode='MarkdownV2')

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    try:
        cfg, _ = await read_config()
        maint    = cfg.get('maintenance', False)
        stats    = cfg.get('stats', {})
        chapters = cfg.get('chapters', [])
        unlocked = [c['num'] for c in chapters if c.get('unlocked')]
        locked   = [c['num'] for c in chapters if not c.get('unlocked')]
        lines = [
            '📊 *CGC — Live Status*\n',
            f"🔴 MAINTENANCE ON" if maint else "🟢 Site is live",
            f"Chapters: `{stats.get('chapters', 0)}`  •  LBS: `{stats.get('lbs', 0):,}`  •  Miles: `{stats.get('miles', 0):,}`",
            f"Unlocked: `{'  '.join(unlocked) if unlocked else 'none'}`",
            f"Locked: `{'  '.join(locked) if locked else 'none'}`",
        ]
        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f'❌ {e}')

async def cmd_unlock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    if not ctx.args:
        await update.message.reply_text('Usage: /unlock <chapter_num|all>  e.g. /unlock 3')
        return
    try:
        cfg, sha = await read_config()
        if ctx.args[0].lower() == 'all':
            for c in cfg['chapters']:
                c['unlocked'] = True
            await write_config(cfg, sha, 'unlock all chapters')
            await update.message.reply_text('✅ All 12 chapters unlocked')
        else:
            num = zpad(ctx.args[0])
            ch  = next((c for c in cfg['chapters'] if c['num'] == num), None)
            if not ch:
                await update.message.reply_text(f'❌ Chapter {num} not found (use 1-12)')
                return
            ch['unlocked'] = True
            await write_config(cfg, sha, f'unlock chapter {num}')
            await update.message.reply_text(f'✅ Chapter {num} unlocked — live in ~30s')
    except Exception as e:
        await update.message.reply_text(f'❌ {e}')

async def cmd_lock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    if not ctx.args:
        await update.message.reply_text('Usage: /lock <chapter_num|all>  e.g. /lock 3')
        return
    try:
        cfg, sha = await read_config()
        if ctx.args[0].lower() == 'all':
            for c in cfg['chapters']:
                c['unlocked'] = False
            await write_config(cfg, sha, 'lock all chapters')
            await update.message.reply_text('✅ All chapters locked')
        else:
            num = zpad(ctx.args[0])
            ch  = next((c for c in cfg['chapters'] if c['num'] == num), None)
            if not ch:
                await update.message.reply_text(f'❌ Chapter {num} not found (use 1-12)')
                return
            ch['unlocked'] = False
            await write_config(cfg, sha, f'lock chapter {num}')
            await update.message.reply_text(f'✅ Chapter {num} locked — live in ~30s')
    except Exception as e:
        await update.message.reply_text(f'❌ {e}')

async def cmd_maintenance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    if not ctx.args or ctx.args[0].lower() not in ('on', 'off'):
        await update.message.reply_text('Usage: /maintenance on  or  /maintenance off')
        return
    on = ctx.args[0].lower() == 'on'
    try:
        cfg, sha = await read_config()
        cfg['maintenance'] = on
        await write_config(cfg, sha, f'maintenance {"on" if on else "off"}')
        status = '🔴 Maintenance ON — visitors see holding page' if on else '🟢 Maintenance OFF — site is live'
        await update.message.reply_text(f'✅ {status}')
    except Exception as e:
        await update.message.reply_text(f'❌ {e}')

async def cmd_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    if len(ctx.args) < 2:
        await update.message.reply_text('Usage: /set <lbs|miles|chapters> <value>\ne.g. /set lbs 8500')
        return
    key = ctx.args[0].lower()
    if key not in ('lbs', 'miles', 'chapters'):
        await update.message.reply_text('❌ Key must be: lbs, miles, or chapters')
        return
    try:
        val = int(ctx.args[1].replace(',', ''))
    except ValueError:
        await update.message.reply_text('❌ Value must be a whole number')
        return
    try:
        cfg, sha = await read_config()
        cfg.setdefault('stats', {})[key] = val
        await write_config(cfg, sha, f'set stats.{key} = {val}')
        await update.message.reply_text(f'✅ {key.upper()} set to {val:,} — live in ~30s')
    except Exception as e:
        await update.message.reply_text(f'❌ {e}')

async def cmd_social(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    if len(ctx.args) < 2:
        await update.message.reply_text(
            'Usage: /social <twitter|discord|telegram> <url>\n'
            'e.g. /social discord https://discord.gg/abc123'
        )
        return
    platform = ctx.args[0].lower()
    url      = ctx.args[1]
    if platform not in ('twitter', 'discord', 'telegram'):
        await update.message.reply_text('❌ Platform must be: twitter, discord, or telegram')
        return
    try:
        cfg, sha = await read_config()
        cfg.setdefault('social', {})[platform] = url
        await write_config(cfg, sha, f'update social.{platform}')
        await update.message.reply_text(f'✅ {platform.capitalize()} link updated — live in ~30s')
    except Exception as e:
        await update.message.reply_text(f'❌ {e}')

# ── Boot ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start',       cmd_start))
    app.add_handler(CommandHandler('help',        cmd_help))
    app.add_handler(CommandHandler('status',      cmd_status))
    app.add_handler(CommandHandler('unlock',      cmd_unlock))
    app.add_handler(CommandHandler('lock',        cmd_lock))
    app.add_handler(CommandHandler('maintenance', cmd_maintenance))
    app.add_handler(CommandHandler('set',         cmd_set))
    app.add_handler(CommandHandler('social',      cmd_social))
    log.info('CGC Bot running (polling mode)')
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
