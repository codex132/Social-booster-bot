import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import db
import tiktok_boost
import youtube_boost
import instagram_boost

# ── env ───────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ["BOT_TOKEN"]
ADMIN_ID    = int(os.environ.get("ADMIN_ID", "0"))
IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")
IG_TARGET   = os.environ.get("IG_TARGET", "")      # whose followers we'll follow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# ── FSM states ────────────────────────────────────────────────────────────────

class TikTok(StatesGroup):
    url     = State()
    service = State()
    loops   = State()

class YouTube(StatesGroup):
    url     = State()
    threads = State()
    minutes = State()

class Instagram(StatesGroup):
    count = State()

# ── keyboards ─────────────────────────────────────────────────────────────────

MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎵 TikTok Boost")],
        [KeyboardButton(text="▶️ YouTube Views")],
        [KeyboardButton(text="📸 Instagram Followers")],
    ],
    resize_keyboard=True,
)

TIKTOK_SERVICE_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="followers"), KeyboardButton(text="views")],
        [KeyboardButton(text="likes"),     KeyboardButton(text="shares")],
        [KeyboardButton(text="favorites"), KeyboardButton(text="comment_likes")],
    ],
    resize_keyboard=True,
)

# ── helpers ───────────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    for ch in r"_*`[":
        s = s.replace(ch, f"\\{ch}")
    return s

def is_admin(msg: Message) -> bool:
    return ADMIN_ID != 0 and msg.from_user.id == ADMIN_ID

# ── /start ────────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    db.log_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username or "")
    await msg.answer(
        "🔥 *Social Booster Bot*\n\n"
        "Boost your TikTok, YouTube, and Instagram — completely free.\n\n"
        "Pick a platform below:",
        parse_mode="Markdown",
        reply_markup=MAIN_KB,
    )

# ── admin: /stats ─────────────────────────────────────────────────────────────

@dp.message(Command("stats"))
async def cmd_stats(msg: Message):
    if not is_admin(msg):
        return
    users  = db.count_users()
    boosts = db.count_boosts()
    stats  = db.get_boost_stats()
    lines  = [
        f"👥 *Total users:* {users}",
        f"🚀 *Total boost jobs:* {boosts}",
        "",
        "*Breakdown:*",
    ]
    for platform, service, total in stats:
        lines.append(f"  • {platform} `{service}`: ~{total} sent")
    await msg.answer("\n".join(lines), parse_mode="Markdown")

# ── admin: /users ─────────────────────────────────────────────────────────────

@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if not is_admin(msg):
        return
    rows = db.get_all_users()
    if not rows:
        await msg.answer("No users yet.")
        return
    lines = ["*ID | Name | @Username | Uses*"]
    for uid, name, uname, first, last, uses in rows:
        uname_str = f"@{esc(uname)}" if uname else "—"
        lines.append(f"`{uid}` | {esc(name)} | {uname_str} | {uses}x")
    chunk: list[str] = []
    for line in lines:
        chunk.append(line)
        if len("\n".join(chunk)) > 3500:
            await msg.answer("\n".join(chunk[:-1]), parse_mode="Markdown")
            chunk = [line]
    if chunk:
        await msg.answer("\n".join(chunk), parse_mode="Markdown")

# ── admin: /broadcast ─────────────────────────────────────────────────────────

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if not is_admin(msg):
        return
    text = msg.text.removeprefix("/broadcast").strip()
    if not text:
        await msg.answer("Usage: /broadcast your message here")
        return
    ids   = db.get_all_ids()
    sent  = 0
    failed = 0
    for uid in ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            log.warning(f"Broadcast to {uid} failed: {e}")
            failed += 1
    await msg.answer(f"📣 Broadcast done.\nSent: {sent} | Failed: {failed}")

# ── /cancel ───────────────────────────────────────────────────────────────────

@dp.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Cancelled.", reply_markup=MAIN_KB)

# ══════════════════════════════════════════════════════════════════════════════
# TikTok flow
# ══════════════════════════════════════════════════════════════════════════════

@dp.message(F.text == "🎵 TikTok Boost")
async def tiktok_start(msg: Message, state: FSMContext):
    db.log_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username or "")
    await state.clear()
    await msg.answer(
        "🎵 *TikTok Boost*\n\n"
        "Paste your TikTok URL:\n"
        "• Profile URL for followers (e.g. `https://tiktok.com/@yourname`)\n"
        "• Video URL for views/likes/shares\n\n"
        "Type /cancel to go back.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(TikTok.url)

@dp.message(TikTok.url)
async def tiktok_url(msg: Message, state: FSMContext):
    url = msg.text.strip()
    if "tiktok.com" not in url:
        return await msg.answer("That doesn't look like a TikTok URL. Try again or /cancel.")
    await state.update_data(url=url)
    await msg.answer("Pick which service to boost:", reply_markup=TIKTOK_SERVICE_KB)
    await state.set_state(TikTok.service)

@dp.message(TikTok.service)
async def tiktok_service(msg: Message, state: FSMContext):
    svc = msg.text.strip().lower()
    if svc not in tiktok_boost.SERVICES:
        return await msg.answer(
            f"Pick one: {', '.join(tiktok_boost.SERVICES)}"
        )
    await state.update_data(service=svc)
    await msg.answer(
        "How many loops?\n\n"
        "• 1 loop ≈ *50 engagements*, cooldown ~65 s\n"
        "• Recommend *10* for a quick run (~10 min)\n"
        "• *50* overnight for ~2,500 engagements\n"
        "• *200* all-night for ~10,000\n\n"
        "Send a number:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(TikTok.loops)

@dp.message(TikTok.loops)
async def tiktok_loops(msg: Message, state: FSMContext):
    try:
        loops = int(msg.text.strip())
        if loops < 1:
            raise ValueError
    except ValueError:
        return await msg.answer("Send a positive number.")

    data = await state.get_data()
    await state.clear()

    url = data["url"]
    svc = data["service"]
    uid = msg.from_user.id
    est_time = (loops * 65) // 60 + 1

    await msg.answer(
        f"⚡ *Starting TikTok `{svc}` boost*\n\n"
        f"URL: `{url}`\n"
        f"Loops: {loops}  •  Est. time: ~{est_time} min\n"
        f"Est. delivery: ~{loops * 50} {svc}\n\n"
        "I'll send progress updates each loop.\n"
        "You can start another boost while this runs.",
        parse_mode="Markdown",
        reply_markup=MAIN_KB,
    )

    async def progress(text: str):
        try:
            await bot.send_message(uid, text)
        except Exception:
            pass

    def run():
        return tiktok_boost.boost_tiktok(
            url, service=svc, loops=loops,
            progress_cb=lambda t: asyncio.run_coroutine_threadsafe(progress(t), asyncio.get_event_loop()),
        )

    results = await asyncio.get_event_loop().run_in_executor(None, run)
    db.log_boost(uid, "TikTok", svc, url, results["sent"])

    err_line = f"\n⚠️ {len(results['errors'])} error(s)" if results["errors"] else ""
    await bot.send_message(
        uid,
        f"✅ *TikTok boost done!*\n\n"
        f"Loops completed: {results['loops_done']}/{loops}\n"
        f"Est. {svc} sent: ~{results['sent']}{err_line}",
        parse_mode="Markdown",
    )

# ══════════════════════════════════════════════════════════════════════════════
# YouTube flow
# ══════════════════════════════════════════════════════════════════════════════

@dp.message(F.text == "▶️ YouTube Views")
async def yt_start(msg: Message, state: FSMContext):
    db.log_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username or "")
    await state.clear()
    await msg.answer(
        "▶️ *YouTube Views*\n\n"
        "Paste your YouTube video URL:\n"
        "e.g. `https://youtube.com/watch?v=XXXX`\n\n"
        "/cancel to go back.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(YouTube.url)

@dp.message(YouTube.url)
async def yt_url(msg: Message, state: FSMContext):
    url = msg.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        return await msg.answer("Doesn't look like a YouTube URL. Try again or /cancel.")
    await state.update_data(url=url)
    await msg.answer(
        "How many threads? (parallel browsers)\n\n"
        "• 2 = light, safe\n"
        "• 4 = faster, more CPU\n"
        "• 6 = max recommended without proxies\n\n"
        "Send a number (1–6):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(YouTube.threads)

@dp.message(YouTube.threads)
async def yt_threads(msg: Message, state: FSMContext):
    try:
        t = max(1, min(int(msg.text.strip()), 6))
    except ValueError:
        return await msg.answer("Send a number 1–6.")
    await state.update_data(threads=t)
    await msg.answer(
        f"Run for how many minutes?\n\n"
        f"• {t} threads × 30 min ≈ ~{t * 60} views\n"
        f"• {t} threads × 120 min ≈ ~{t * 240} views\n"
        f"• {t} threads × 480 min ≈ ~{t * 960} views (overnight)\n\n"
        "Send a number:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(YouTube.minutes)

@dp.message(YouTube.minutes)
async def yt_minutes(msg: Message, state: FSMContext):
    try:
        mins = int(msg.text.strip())
        if mins < 1:
            raise ValueError
    except ValueError:
        return await msg.answer("Send a positive number.")

    data = await state.get_data()
    await state.clear()

    url     = data["url"]
    threads = data["threads"]
    uid     = msg.from_user.id
    est     = threads * mins * 2

    await msg.answer(
        f"▶️ *Starting YouTube viewer*\n\n"
        f"URL: `{url}`\n"
        f"Threads: {threads}  •  Duration: {mins} min\n"
        f"Est. views: ~{est}\n\n"
        "Running in background — I'll notify you when done.",
        parse_mode="Markdown",
        reply_markup=MAIN_KB,
    )

    def run():
        return youtube_boost.boost_youtube(url, threads=threads, duration_minutes=mins)

    results = await asyncio.get_event_loop().run_in_executor(None, run)
    db.log_boost(uid, "YouTube", "views", url, results["estimated_views"])

    err_line = f"\n⚠️ {results['errors'][0][:150]}" if results["errors"] else ""
    await bot.send_message(
        uid,
        f"✅ *YouTube boost done!*\n\n"
        f"Est. views sent: ~{results['estimated_views']}\n"
        f"Runtime: {results['runtime_minutes']} min{err_line}\n\n"
        "💡 Run again tonight for more — views stack up.",
        parse_mode="Markdown",
    )

# ══════════════════════════════════════════════════════════════════════════════
# Instagram flow
# ══════════════════════════════════════════════════════════════════════════════

@dp.message(F.text == "📸 Instagram Followers")
async def ig_start(msg: Message, state: FSMContext):
    db.log_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username or "")
    await state.clear()

    if not IG_USERNAME or not IG_PASSWORD:
        await msg.answer(
            "⚠️ Instagram credentials not set.\n\n"
            "Add these to your environment variables:\n"
            "`IG_USERNAME` — your Instagram username\n"
            "`IG_PASSWORD` — your Instagram password\n"
            "`IG_TARGET`  — account whose followers you'll follow\n\n"
            "Then restart the bot.",
            parse_mode="Markdown",
            reply_markup=MAIN_KB,
        )
        return

    await msg.answer(
        f"📸 *Instagram Followers*\n\n"
        f"Your account: `{IG_USERNAME}`\n"
        f"Target: `{IG_TARGET}`\n\n"
        "The bot will follow people from the target's followers list.\n"
        "~25–35% will follow you back within 24 h.\n\n"
        "Safe max per session: 100\n"
        "How many to follow? (1–100):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Instagram.count)

@dp.message(Instagram.count)
async def ig_count(msg: Message, state: FSMContext):
    try:
        count = max(1, min(int(msg.text.strip()), 100))
    except ValueError:
        return await msg.answer("Send a number 1–100.")

    await state.clear()

    uid      = msg.from_user.id
    est_time = (count * 30) // 60 + 1

    await msg.answer(
        f"📸 *Starting Instagram sweep*\n\n"
        f"Following {count} accounts from `{IG_TARGET}`'s followers\n"
        f"Est. time: ~{est_time} min (human-paced to stay safe)\n"
        f"Est. follow-backs: ~{count * 3 // 10}–{count * 35 // 100} within 24 h\n\n"
        "Running… updates will come in.",
        parse_mode="Markdown",
        reply_markup=MAIN_KB,
    )

    async def progress(text: str):
        try:
            await bot.send_message(uid, text)
        except Exception:
            pass

    def run():
        return instagram_boost.boost_instagram(
            IG_USERNAME, IG_PASSWORD, IG_TARGET,
            follow_count=count,
            progress_cb=lambda t: asyncio.run_coroutine_threadsafe(progress(t), asyncio.get_event_loop()),
        )

    results = await asyncio.get_event_loop().run_in_executor(None, run)
    db.log_boost(uid, "Instagram", "followers", f"@{IG_TARGET}", results["followed"])

    err_line = f"\n⚠️ {results['errors'][0]}" if results["errors"] else ""
    await bot.send_message(
        uid,
        f"✅ *Instagram sweep done!*\n\n"
        f"Followed: {results['followed']}\n"
        f"Skipped: {results['skipped']}\n"
        f"Est. follow-backs: ~{results['followed'] * 3 // 10}+ over 24 h{err_line}\n\n"
        "💡 Run again tomorrow — IG limits reset every 24 h.",
        parse_mode="Markdown",
    )

# ── entry ─────────────────────────────────────────────────────────────────────

async def main():
    db.init()
    log.info("Booster bot starting…")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
