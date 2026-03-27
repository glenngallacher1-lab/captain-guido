"""
Captain Guido Admin Bot
=======================
Telegram bot that lets authorised users (Glenn + Jude) update the
live website without touching code.

Commands
--------
/status          — show current site config
/unlock <1-12>   — unlock a chapter on the map
/stats           — guided flow to update impact stats
/launch          — flip the site to live mode (confirmation required)
/milestone       — add a cleanup milestone
/help            — show all commands

Setup: see README.md
"""

import os, re, json, base64, logging
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    ContextTypes, filters,
)

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
GITHUB_TOKEN   = os.environ["GITHUB_TOKEN"]
GITHUB_REPO    = os.environ.get("GITHUB_REPO", "glenngallacher1-lab/captain-guido")
SCRIPT_PATH    = "script.js"

# Comma-separated Telegram user IDs, e.g. "123456789,987654321"
_raw = os.environ.get("AUTHORIZED_USERS", "")
AUTHORIZED = set(int(x.strip()) for x in _raw.split(",") if x.strip())

CHAPTER_NAMES = [
    "Port of Ostia",
    "Signals in Cairo",
    "Arabian Tides",
    "Indian Abyss",
    "Philippine Sea",
    "South Pacific",
    "North Pacific",
    "Bering Sea",
    "North Atlantic",
    "Gulf of America",
    "South Atlantic",
    "Return to Ostia",
]

# ConversationHandler states
(
    STATS_LBS, STATS_MILES, STATS_DONATIONS,
    STATS_USD, STATS_CHAPTERS, STATS_CONFIRM,
    MILESTONE_DATE, MILESTONE_TITLE,
    MILESTONE_LOCATION, MILESTONE_IMPACT,
) = range(10)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# ── GitHub helpers ─────────────────────────────────────────────────────────────
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}
API = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SCRIPT_PATH}"


def gh_get():
    """Return (content_str, sha)."""
    r = requests.get(API, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def gh_put(content: str, sha: str, message: str):
    """Commit updated content back to GitHub."""
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha,
    }
    r = requests.put(API, headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()


# ── Impact data parsers ────────────────────────────────────────────────────────
def parse_impact(content: str) -> dict:
    """Extract current IMPACT_DATA values from script.js."""
    out = {}
    for field, pattern in [
        ("launched",          r"launched:\s*(true|false)"),
        ("chaptersUnlocked",  r"chaptersUnlocked:\s*(\d+)"),
        ("lbsRemoved",        r"lbsRemoved:\s*(\d+)"),
        ("milesCleaned",      r"milesCleaned:\s*(\d+)"),
        ("donationsVerified", r"donationsVerified:\s*(\d+)"),
        ("donationUSD",       r"donationUSD:\s*(\d+)"),
    ]:
        m = re.search(pattern, content)
        if m:
            v = m.group(1)
            out[field] = (v == "true") if field == "launched" else int(v)
    return out


def set_impact_field(content: str, field: str, value) -> str:
    """Replace a single IMPACT_DATA field value."""
    if isinstance(value, bool):
        return re.sub(
            rf"({re.escape(field)}:\s*)(?:true|false)",
            rf"\g<1>{str(value).lower()}",
            content,
        )
    return re.sub(
        rf"({re.escape(field)}:\s*)\d+",
        rf"\g<1>{value}",
        content,
    )


def unlock_chapter(content: str, chapter_num: int) -> str:
    """
    Unlock chapter N (1-indexed) by flipping its unlocked flag.
    Leaves earlier entries untouched.
    """
    # Split at each chapter object opening brace inside the array
    parts = re.split(r'(\{ name: ")', content)
    # parts alternates: [before_first, '{ name: "', entry1_tail, '{ name: "', entry2_tail, ...]
    # entry index = (part_index - 1) // 2  for odd indices
    target_occurrence = chapter_num  # 1-indexed, chapter 1 = first occurrence
    occurrence = 0
    new_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # this is a '{ name: "' separator
            occurrence += 1
            new_parts.append(part)
        elif i > 0:  # entry tail
            if occurrence == target_occurrence:
                part = re.sub(
                    r"(unlocked:\s*)false",
                    r"\g<1>true",
                    part,
                    count=1,
                )
            new_parts.append(part)
        else:
            new_parts.append(part)
    return "".join(new_parts)


def get_chapter_status(content: str) -> list[bool]:
    """Return list of unlocked booleans for all 12 chapters."""
    matches = re.findall(r'\{ name: "[^"]+",.*?unlocked: (true|false)', content)
    return [m == "true" for m in matches]


def add_milestone(content: str, date: str, title: str, location: str, impact: str) -> str:
    """Append a milestone entry to the milestones array."""
    entry = (
        f"\n      {{ date: '{date}', title: '{title}', "
        f"location: '{location}', impact: '{impact}' }}"
    )
    # Insert before the closing ] of the milestones array
    return re.sub(
        r"(milestones:\s*\[)([\s\S]*?)(\s*\])",
        lambda m: m.group(1) + m.group(2).rstrip() + "," + entry + "\n    " + m.group(3).lstrip(),
        content,
        count=1,
    )


# ── Auth guard ────────────────────────────────────────────────────────────────
def authorised(update: Update) -> bool:
    uid = update.effective_user.id
    if uid not in AUTHORIZED:
        return False
    return True


async def deny(update: Update):
    await update.message.reply_text(
        "⛔ You're not authorised to use this bot.\n"
        "Ask Glenn to add your Telegram user ID."
    )


# ── /start & /help ─────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorised(update): return await deny(update)
    await update.message.reply_text(
        "⚓ *Captain Guido Admin Bot*\n\n"
        "Commands:\n"
        "/status — current site config\n"
        "/unlock — unlock a chapter\n"
        "/stats — update impact stats\n"
        "/milestone — add a cleanup milestone\n"
        "/launch — flip site to live mode\n"
        "/help — this message",
        parse_mode="Markdown",
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


# ── /status ───────────────────────────────────────────────────────────────────
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorised(update): return await deny(update)
    await update.message.reply_text("⏳ Fetching current config...")
    try:
        content, _ = gh_get()
        data = parse_impact(content)
        chapters = get_chapter_status(content)

        chapter_lines = ""
        for i, (name, unlocked) in enumerate(zip(CHAPTER_NAMES, chapters), 1):
            icon = "🟢" if unlocked else "⚫"
            chapter_lines += f"  {icon} Ch.{i} — {name}\n"

        lines = [
            f"🌐 *Site mode:* {'🟢 LIVE' if data.get('launched') else '⚫ Pre-launch'}",
            f"📖 Chapters unlocked counter: `{data.get('chaptersUnlocked', 0)}`",
            f"⚖️ lbs removed: `{data.get('lbsRemoved', 0):,}`",
            f"🗺️ Miles cleaned: `{data.get('milesCleaned', 0):,}`",
            f"🤝 Donations verified: `{data.get('donationsVerified', 0)}`",
            f"💵 Donation USD: `${data.get('donationUSD', 0):,}`",
            f"\n*Chapter map markers:*\n{chapter_lines}",
        ]
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


# ── /unlock ───────────────────────────────────────────────────────────────────
async def cmd_unlock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorised(update): return await deny(update)
    args = ctx.args
    if not args or not args[0].isdigit():
        # Show keyboard picker
        buttons = [
            [InlineKeyboardButton(f"Ch.{i} — {CHAPTER_NAMES[i-1]}", callback_data=f"unlock:{i}")]
            for i in range(2, 13)  # Ch.1 is already unlocked
        ]
        await update.message.reply_text(
            "Which chapter do you want to unlock?",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    num = int(args[0])
    if not 1 <= num <= 12:
        await update.message.reply_text("❌ Chapter must be 1–12.")
        return
    await _do_unlock(update, num)


async def _do_unlock(update: Update, num: int):
    name = CHAPTER_NAMES[num - 1]
    await update.message.reply_text(f"🔓 Unlocking Chapter {num}: *{name}*...", parse_mode="Markdown")
    try:
        content, sha = gh_get()
        chapters = get_chapter_status(content)
        if chapters[num - 1]:
            await update.message.reply_text(f"ℹ️ Chapter {num} is already unlocked.")
            return
        new_content = unlock_chapter(content, num)
        # Also bump chaptersUnlocked counter
        current = parse_impact(new_content).get("chaptersUnlocked", 0)
        new_content = set_impact_field(new_content, "chaptersUnlocked", current + 1)
        gh_put(new_content, sha, f"🔓 Unlock Chapter {num}: {name} [admin bot]")
        await update.message.reply_text(
            f"✅ *Chapter {num} — {name} is now LIVE on the map!*\n"
            f"chaptersUnlocked counter → {current + 1}\n\n"
            "GitHub Pages usually updates within 2 minutes.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def callback_unlock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not authorised(update): return
    _, num_str = query.data.split(":")
    num = int(num_str)
    await query.edit_message_text(f"🔓 Unlocking Chapter {num}: {CHAPTER_NAMES[num-1]}...")
    # Reuse logic via fake update with message
    try:
        content, sha = gh_get()
        chapters = get_chapter_status(content)
        if chapters[num - 1]:
            await query.edit_message_text(f"ℹ️ Chapter {num} is already unlocked.")
            return
        new_content = unlock_chapter(content, num)
        current = parse_impact(new_content).get("chaptersUnlocked", 0)
        new_content = set_impact_field(new_content, "chaptersUnlocked", current + 1)
        gh_put(new_content, sha, f"🔓 Unlock Chapter {num}: {CHAPTER_NAMES[num-1]} [admin bot]")
        await query.edit_message_text(
            f"✅ Chapter {num} — {CHAPTER_NAMES[num-1]} is now LIVE!\n"
            f"chaptersUnlocked → {current + 1}\n\n"
            "GitHub Pages updates within ~2 minutes."
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")


# ── /launch ───────────────────────────────────────────────────────────────────
async def cmd_launch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorised(update): return await deny(update)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 YES — GO LIVE", callback_data="launch:confirm"),
        InlineKeyboardButton("❌ Cancel", callback_data="launch:cancel"),
    ]])
    await update.message.reply_text(
        "⚠️ *This will flip the site to LIVE mode.*\n\n"
        "The Impact section will switch from pre-launch to showing real stats. "
        "Make sure your stats are up to date first.\n\nConfirm?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def callback_launch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not authorised(update): return
    action = query.data.split(":")[1]
    if action == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return
    try:
        content, sha = gh_get()
        new_content = set_impact_field(content, "launched", True)
        gh_put(new_content, sha, "🚀 LAUNCH — flip site to live mode [admin bot]")
        await query.edit_message_text(
            "🚀 *SITE IS NOW LIVE!*\n\n"
            "Impact section will show real stats. "
            "GitHub Pages updates within ~2 minutes.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")


# ── /stats (guided conversation) ──────────────────────────────────────────────
async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorised(update): return await deny(update)
    try:
        content, _ = gh_get()
        data = parse_impact(content)
        ctx.user_data["stats_current"] = data
        ctx.user_data["stats_new"] = {}
    except Exception as e:
        await update.message.reply_text(f"❌ Could not fetch current stats: {e}")
        return ConversationHandler.END

    d = ctx.user_data["stats_current"]
    await update.message.reply_text(
        f"📊 *Update Impact Stats*\n\n"
        f"Current: `{d.get('lbsRemoved', 0):,}` lbs removed\n"
        f"Enter new value (or /skip to keep):",
        parse_mode="Markdown",
    )
    return STATS_LBS


async def stats_lbs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt != "/skip":
        if not txt.replace(",", "").isdigit():
            await update.message.reply_text("Enter a number (e.g. 500) or /skip:")
            return STATS_LBS
        ctx.user_data["stats_new"]["lbsRemoved"] = int(txt.replace(",", ""))

    d = ctx.user_data["stats_current"]
    await update.message.reply_text(
        f"Current: `{d.get('milesCleaned', 0):,}` miles cleaned\nEnter new value (or /skip):",
        parse_mode="Markdown",
    )
    return STATS_MILES


async def stats_miles(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt != "/skip":
        if not txt.replace(",", "").isdigit():
            await update.message.reply_text("Enter a number or /skip:")
            return STATS_MILES
        ctx.user_data["stats_new"]["milesCleaned"] = int(txt.replace(",", ""))

    d = ctx.user_data["stats_current"]
    await update.message.reply_text(
        f"Current: `{d.get('donationsVerified', 0)}` donations verified\nEnter new value (or /skip):",
        parse_mode="Markdown",
    )
    return STATS_DONATIONS


async def stats_donations(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt != "/skip":
        if not txt.replace(",", "").isdigit():
            await update.message.reply_text("Enter a number or /skip:")
            return STATS_DONATIONS
        ctx.user_data["stats_new"]["donationsVerified"] = int(txt.replace(",", ""))

    d = ctx.user_data["stats_current"]
    await update.message.reply_text(
        f"Current: `${d.get('donationUSD', 0):,}` donated (USD)\nEnter new value (or /skip):",
        parse_mode="Markdown",
    )
    return STATS_USD


async def stats_usd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt != "/skip":
        txt_clean = txt.lstrip("$").replace(",", "")
        if not txt_clean.isdigit():
            await update.message.reply_text("Enter a dollar amount (e.g. 5000) or /skip:")
            return STATS_USD
        ctx.user_data["stats_new"]["donationUSD"] = int(txt_clean)

    # Build confirm message
    current = ctx.user_data["stats_current"]
    changes = ctx.user_data["stats_new"]
    if not changes:
        await update.message.reply_text("No changes made.")
        return ConversationHandler.END

    lines = ["📋 *Confirm changes:*\n"]
    labels = {
        "lbsRemoved": "lbs removed",
        "milesCleaned": "miles cleaned",
        "donationsVerified": "donations verified",
        "donationUSD": "donation USD",
    }
    for k, label in labels.items():
        if k in changes:
            old = current.get(k, 0)
            new = changes[k]
            lines.append(f"  {label}: `{old:,}` → `{new:,}`")

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirm", callback_data="stats:confirm"),
        InlineKeyboardButton("❌ Cancel", callback_data="stats:cancel"),
    ]])
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return STATS_CONFIRM


async def stats_confirm_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "stats:cancel":
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END
    try:
        content, sha = gh_get()
        for field, value in ctx.user_data["stats_new"].items():
            content = set_impact_field(content, field, value)
        gh_put(content, sha, "📊 Update impact stats [admin bot]")
        await query.edit_message_text(
            "✅ *Stats updated!*\nGitHub Pages will refresh within ~2 minutes.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")
    return ConversationHandler.END


async def stats_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Stats update cancelled.")
    return ConversationHandler.END


# ── /milestone (guided conversation) ─────────────────────────────────────────
async def cmd_milestone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorised(update): return await deny(update)
    await update.message.reply_text(
        "🏆 *Add a Cleanup Milestone*\n\n"
        "Date/period? (e.g. `2026-Q3` or `Jul 2026`)\nOr /cancel to stop:",
        parse_mode="Markdown",
    )
    return MILESTONE_DATE


async def milestone_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ms_date"] = update.message.text.strip()
    await update.message.reply_text("Title? (e.g. `Chapter 1 Unlocked`):")
    return MILESTONE_TITLE


async def milestone_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ms_title"] = update.message.text.strip()
    await update.message.reply_text("Location? (e.g. `Mediterranean Sea, Italy`):")
    return MILESTONE_LOCATION


async def milestone_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ms_location"] = update.message.text.strip()
    await update.message.reply_text("Impact? (e.g. `500 lbs removed`):")
    return MILESTONE_IMPACT


async def milestone_impact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ms_impact"] = update.message.text.strip()
    d = ctx.user_data
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Add it", callback_data="ms:confirm"),
        InlineKeyboardButton("❌ Cancel", callback_data="ms:cancel"),
    ]])
    await update.message.reply_text(
        f"📋 *New milestone:*\n"
        f"  Date: `{d['ms_date']}`\n"
        f"  Title: `{d['ms_title']}`\n"
        f"  Location: `{d['ms_location']}`\n"
        f"  Impact: `{d['ms_impact']}`\n\nConfirm?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return ConversationHandler.END


async def callback_milestone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not authorised(update): return
    if query.data == "ms:cancel":
        await query.edit_message_text("❌ Cancelled.")
        return
    d = ctx.user_data
    try:
        content, sha = gh_get()
        new_content = add_milestone(
            content, d["ms_date"], d["ms_title"], d["ms_location"], d["ms_impact"]
        )
        gh_put(new_content, sha, f"🏆 Add milestone: {d['ms_title']} [admin bot]")
        await query.edit_message_text(
            f"✅ *Milestone added!*\n_{d['ms_title']}_ — {d['ms_location']}\n\n"
            "GitHub Pages will refresh within ~2 minutes.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")


async def conversation_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Stats conversation
    stats_conv = ConversationHandler(
        entry_points=[CommandHandler("stats", cmd_stats)],
        states={
            STATS_LBS:       [MessageHandler(filters.TEXT & ~filters.COMMAND, stats_lbs),
                               CommandHandler("skip", stats_lbs)],
            STATS_MILES:     [MessageHandler(filters.TEXT & ~filters.COMMAND, stats_miles),
                               CommandHandler("skip", stats_miles)],
            STATS_DONATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, stats_donations),
                               CommandHandler("skip", stats_donations)],
            STATS_USD:       [MessageHandler(filters.TEXT & ~filters.COMMAND, stats_usd),
                               CommandHandler("skip", stats_usd)],
            STATS_CONFIRM:   [CallbackQueryHandler(stats_confirm_handler, pattern="^stats:")],
        },
        fallbacks=[CommandHandler("cancel", stats_cancel)],
    )

    # Milestone conversation
    milestone_conv = ConversationHandler(
        entry_points=[CommandHandler("milestone", cmd_milestone)],
        states={
            MILESTONE_DATE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, milestone_date)],
            MILESTONE_TITLE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, milestone_title)],
            MILESTONE_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, milestone_location)],
            MILESTONE_IMPACT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, milestone_impact)],
        },
        fallbacks=[CommandHandler("cancel", conversation_cancel)],
    )

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("unlock",    cmd_unlock))
    app.add_handler(CommandHandler("launch",    cmd_launch))
    app.add_handler(stats_conv)
    app.add_handler(milestone_conv)
    app.add_handler(CallbackQueryHandler(callback_unlock,   pattern="^unlock:"))
    app.add_handler(CallbackQueryHandler(callback_launch,   pattern="^launch:"))
    app.add_handler(CallbackQueryHandler(callback_milestone, pattern="^ms:"))

    log.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
