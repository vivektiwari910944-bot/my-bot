import os
import sys
import random
import logging
import asyncio
from threading import Thread
import requests
from flask import Flask, render_template_string
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VivekAsyncEngine")

# ==========================================
# 🌐 DYNAMIC CONFIGURATION VARIABLES
# ==========================================
DEFAULT_BG = "https://images.alphacoders.com/132/1328400.jpeg"
bg_image_url = DEFAULT_BG
render_web_url = "https://my-bot-zlmx.onrender.com/"

# ==========================================
# 🌐 FLASK ANIME GLOW WEB MENU SERVER
# ==========================================
web_app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIVEK MULTI-BOT 🦁</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(rgba(10, 15, 30, 0.55), rgba(10, 15, 30, 0.65)), 
                        url('{{ bg_url }}') no-repeat center center fixed;
            background-size: cover;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 880px;
            background: rgba(18, 22, 40, 0.75);
            border: 2px solid #00f0ff;
            box-shadow: 0 0 35px rgba(0, 240, 255, 0.5), inset 0 0 20px rgba(0, 240, 255, 0.2);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(14px);
            text-align: center;
        }
        h1 { font-size: 2.6rem; color: #ff0055; text-shadow: 0 0 15px #ff0055; margin-bottom: 8px; font-weight: 800; }
        .subtitle { font-size: 1.2rem; color: #00ffff; margin-bottom: 20px; text-shadow: 0 0 10px #00ffff; font-weight: 600; }
        .btn-render {
            display: inline-block; margin: 10px 0 25px 0; padding: 14px 32px; font-size: 1.15rem; font-weight: bold;
            color: #ffffff; background: linear-gradient(45deg, #ff0055, #7928ca, #00dfd8);
            background-size: 200% 200%; animation: gradientGlow 3s ease infinite; border: none; border-radius: 30px;
            text-decoration: none; box-shadow: 0 0 20px rgba(0, 223, 216, 0.8); transition: all 0.3s ease;
        }
        @keyframes gradientGlow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .section-title { font-size: 1.35rem; color: #ffd700; border-bottom: 2px solid #ffd700; display: inline-block; margin: 22px 0 15px 0; padding-bottom: 4px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 15px; }
        .card { background: rgba(255, 255, 255, 0.12); border: 1px solid rgba(0, 240, 255, 0.45); padding: 15px; border-radius: 12px; backdrop-filter: blur(8px); }
        .cmd { font-weight: bold; color: #00ffff; font-size: 1.05rem; }
        .desc { font-size: 0.9rem; color: #f1f1f1; margin-top: 5px; }
        .footer { margin-top: 25px; font-size: 1.1rem; color: #ff0055; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>VIVEK MULTI-BOT EQUIPMENT</h1>
        <div class="subtitle">𝘝𝘐𝘝𝘌𝘒 𝘋𝘖𝘔𝘈𝘐𝘕 𝘌𝘹𝘗𝘈𝘕𝘋𝘌𝘋</div>
        <a href="{{ render_url }}" target="_blank" class="btn-render">🌐 OPEN VIVEK RENDER SERVER</a>
        <div class="section-title">🚀 COMMANDS PANEL</div>
        <div class="grid">
            <div class="card"><div class="cmd">/menu</div><div class="desc">Show Menu</div></div>
            <div class="card"><div class="cmd">/hunt &lt;target&gt;</div><div class="desc">Hunt down target</div></div>
            <div class="card"><div class="cmd">/stop</div><div class="desc">Chat-Specific Kill Switch</div></div>
            <div class="card"><div class="cmd">/spam &lt;msg&gt;</div><div class="desc">Start fast spam</div></div>
            <div class="card"><div class="cmd">/nc &lt;name&gt;</div><div class="desc">Name changer loop</div></div>
            <div class="card"><div class="cmd">/gpdp &lt;url&gt;</div><div class="desc">Group DP changer</div></div>
        </div>
        <div class="footer">🟢 DEVELOPER : VIVEK TIWARI 🟢</div>
    </div>
</body>
</html>
"""

@web_app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, bg_url=bg_image_url, render_url=render_web_url)

def keep_alive():
    t = Thread(target=lambda: web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True)
    t.start()
    logger.info("Flask Web Engine server active!")

# ==========================================
# ⚙️ SETUP & CONFIGS
# ==========================================
def run_setup():
    print("\n🔥 VIVEK MULTI-BOT ENGINE — SETUP\n" + "━"*40)
    owner_raw = input("Owner IDs (comma-separated): ").strip()
    tokens = []
    i = 1
    while True:
        tok = input(f"  Bot Token {i} (blank = done): ").strip()
        if not tok:
            if not tokens: continue
            break
        tokens.append(tok)
        i += 1
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"OWNER_IDS={owner_raw}\n")
        for j, t in enumerate(tokens, 1): f.write(f"BOT_TOKEN_{j}={t}\n")
    load_dotenv(override=True)

if not os.environ.get("OWNER_IDS") or not os.environ.get("BOT_TOKEN_1"):
    run_setup()

OWNER_IDS_RAW = os.environ.get("OWNER_IDS", "")
OWNER_IDS = set(int(x.strip()) for x in OWNER_IDS_RAW.split(",") if x.strip().isdigit())

BOT_TOKENS = []
i = 1
while True:
    tok = os.environ.get(f"BOT_TOKEN_{i}")
    if not tok: break
    BOT_TOKENS.append(tok.strip())
    i += 1

COOL_EMOJIS = ["🔥","⚡","👑","💀","🚀","💥","⚔️","🔱","🎯","🩸","💣","🐺","🦅","💎","🏆"]
def cool_emoji(): return random.choice(COOL_EMOJIS)

HUNT_LINES = [
    "Bow down before the almighty master, you absolute non-entity! ⚔️",
    "You really thought you could survive in this arena? Know your place, worm! 💀",
    "Tremble before the absolute authority! You stand zero chance! 🔱",
    "Keep talking, but remember you are just fuel for the empire! 🚀",
    "A slave of destiny trying to fight the emperor? How pitiful! 👑"
]

# Global Storage Maps
spam_tasks = {}
nc_tasks = {}
hunt_tasks = {}
gpdp_tasks = {}

auto_react = {}   # (chat_id, user_id) -> emoji
auto_reply = {}   # (chat_id, user_id) -> text
auto_photo = {}   # (chat_id, user_id) -> photo_url
auto_sticker = {} # (chat_id, user_id) -> sticker_id

delays = {} # chat_id -> float

apps = []

# ==========================================
# 🚀 ASYNC WORKERS (MAXIMUM SPEED LOOPS)
# ==========================================
async def spam_worker(chat_id, text):
    while True:
        delay = delays.get(chat_id, 0.01)
        tasks = [app.bot.send_message(chat_id=chat_id, text=text) for app in apps]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(delay)

async def nc_worker(chat_id, base_name):
    """Multi-Bot Token Rotation to bypass rate limits & maximize speed"""
    bot_index = 0
    while True:
        delay = delays.get(chat_id, 0.01)
        new_title = f"{base_name} {cool_emoji()}"
        
        if apps:
            app = apps[bot_index % len(apps)]
            bot_index += 1
            try:
                await app.bot.set_chat_title(chat_id=chat_id, title=new_title)
            except Exception:
                pass
                
        await asyncio.sleep(delay)

async def hunt_worker(chat_id, target_id):
    line_idx = 0
    while True:
        delay = delays.get(chat_id, 0.3)
        line = HUNT_LINES[line_idx % len(HUNT_LINES)]
        line_idx += 1
        msg = f"<a href='tg://user?id={target_id}'>Target</a> {line}"
        
        tasks = [app.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML') for app in apps]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(delay)

async def gpdp_worker(chat_id, photo_url):
    while True:
        delay = delays.get(chat_id, 2.0)
        try:
            res = requests.get(photo_url, timeout=5)
            if res.status_code == 200:
                for app in apps:
                    try:
                        await app.bot.set_chat_photo(chat_id=chat_id, photo=res.content)
                        break
                    except Exception:
                        continue
        except Exception:
            pass
        await asyncio.sleep(delay)

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        return update.message.reply_to_message.from_user.id
    if context.args and context.args[0].isdigit():
        return int(context.args[0])
    return None

# ==========================================
# 🎮 COMMAND HANDLERS
# ==========================================
async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    menu_text = "__________________________________\n𝘵𝘩𝘦 𝘴𝘭𝘢𝘷𝘦𝘴 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘰𝘯 𝘢𝘤𝘵𝘪𝘰𝘯 𝘓𝘰𝘳𝘥 🩸\n_________________________________"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Vivek's domain 🌐", url=render_web_url)]])
    await update.message.reply_text(menu_text, reply_markup=keyboard)

async def cmd_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args: return
    try:
        val = float(context.args[0])
        delays[update.effective_chat.id] = max(val, 0.01)
        await update.message.reply_text(f"⚡ Speed Flow set to {val}s!")
    except ValueError:
        pass

async def cmd_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    text = " ".join(context.args)
    if not text: return
    cid = update.effective_chat.id
    
    if cid in spam_tasks: spam_tasks[cid].cancel()
    spam_tasks[cid] = asyncio.create_task(spam_worker(cid, text))
    await update.message.reply_text("🚀 HIGH-SPEED SPAM STARTED! 🔥")

async def cmd_nc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    name = " ".join(context.args)
    if not name: return
    cid = update.effective_chat.id

    if cid in nc_tasks: nc_tasks[cid].cancel()
    nc_tasks[cid] = asyncio.create_task(nc_worker(cid, name))
    await update.message.reply_text("⚡ FAST NAME CHANGER STARTED! 🔥")

async def cmd_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    target_id = get_target_user(update, context)
    if not target_id: return
    cid = update.effective_chat.id

    if cid in hunt_tasks: hunt_tasks[cid].cancel()
    hunt_tasks[cid] = asyncio.create_task(hunt_worker(cid, target_id))
    await update.message.reply_text(f"⚔️ CONTINUOUS HUNTING STARTED ON USER: `{target_id}`", parse_mode="Markdown")

async def cmd_gpdp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args: return
    url = context.args[0]
    if not url.startswith("http"): return
    cid = update.effective_chat.id

    if cid in gpdp_tasks: gpdp_tasks[cid].cancel()
    gpdp_tasks[cid] = asyncio.create_task(gpdp_worker(cid, url))
    await update.message.reply_text("🖼️ GROUP DP LOOP STARTED!")

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    cid = update.effective_chat.id

    if cid in spam_tasks: spam_tasks[cid].cancel(); del spam_tasks[cid]
    if cid in nc_tasks: nc_tasks[cid].cancel(); del nc_tasks[cid]
    if cid in hunt_tasks: hunt_tasks[cid].cancel(); del hunt_tasks[cid]
    if cid in gpdp_tasks: gpdp_tasks[cid].cancel(); del gpdp_tasks[cid]

    await update.message.reply_text("🛑 CHAT STOPPED SUCCESSFULLY! ALL LOOPS HALTED HERE! ⚡")

async def cmd_autoreply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    target_id = get_target_user(update, context)
    if not target_id or len(context.args) < 2: return
    text = " ".join(context.args[1:]) if context.args[0].isdigit() else " ".join(context.args)
    
    auto_reply[(update.effective_chat.id, target_id)] = text
    await update.message.reply_text(f"👑 AUTO-REPLY SET FOR `{target_id}`!", parse_mode="Markdown")

async def cmd_autophoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    target_id = get_target_user(update, context)
    if not target_id or len(context.args) < 2: return
    url = context.args[-1]
    
    auto_photo[(update.effective_chat.id, target_id)] = url
    await update.message.reply_text(f"🖼️ AUTO-PHOTO SET FOR `{target_id}`!", parse_mode="Markdown")

async def cmd_autosticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    target_id = get_target_user(update, context)
    if not target_id or len(context.args) < 2: return
    stk_id = context.args[-1]
    
    auto_sticker[(update.effective_chat.id, target_id)] = stk_id
    await update.message.reply_text(f"🎯 AUTO-STICKER SET FOR `{target_id}`!", parse_mode="Markdown")

async def cmd_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    target_id = get_target_user(update, context)
    if not target_id or not context.args: return
    emoji = context.args[-1]

    auto_react[(update.effective_chat.id, target_id)] = emoji
    await update.message.reply_text(f"👑 AUTO-REACT SET FOR `{target_id}`!", parse_mode="Markdown")

async def cmd_stopreply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    cid = update.effective_chat.id
    for store in (auto_reply, auto_photo, auto_sticker, auto_react):
        for k in [k for k in store if k[0] == cid]:
            del store[k]
    await update.message.reply_text("🛑 ALL AUTO REPLIES / REACTIONS STOPPED!")

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    u = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    txt = f"🔍 <b>USER INFO</b>\nName: {u.first_name}\nID: <code>{u.id}</code>\nUsername: @{u.username or 'N/A'}"
    await update.message.reply_text(txt, parse_mode="HTML")

async def cmd_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    cid = update.effective_chat.id
    mid = update.message.message_id
    for i in range(mid, max(mid - 100, 0), -1):
        try: await context.bot.delete_message(chat_id=cid, message_id=i)
        except Exception: pass
    await update.message.reply_text("🗑️ Cleaned messages!")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    cid = update.effective_chat.id
    msg = f"⚡ <b>ENGINE STATUS</b>\nSpam: {cid in spam_tasks}\nNC: {cid in nc_tasks}\nHunt: {cid in hunt_tasks}\nGPDP: {cid in gpdp_tasks}"
    await update.message.reply_text(msg, parse_mode="HTML")

async def handle_message_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user: return
    cid = update.effective_chat.id
    uid = update.message.from_user.id

    # Auto React
    if (cid, uid) in auto_react:
        try: await update.message.set_reaction(auto_react[(cid, uid)])
        except Exception: pass

    # Auto Reply Text
    if (cid, uid) in auto_reply:
        try: await update.message.reply_text(auto_reply[(cid, uid)])
        except Exception: pass

    # Auto Photo
    if (cid, uid) in auto_photo:
        try: await update.message.reply_photo(photo=auto_photo[(cid, uid)])
        except Exception: pass

    # Auto Sticker
    if (cid, uid) in auto_sticker:
        try: await update.message.reply_sticker(sticker=auto_sticker[(cid, uid)])
        except Exception: pass

# ==========================================
# ⚡ MAIN ASYNC STARTER
# ==========================================
async def main():
    keep_alive()
    print("🚀 Initializing Bots...")
    
    for idx, token in enumerate(BOT_TOKENS, 1):
        app = Application.builder().token(token).build()
        
        # Commands
        app.add_handler(CommandHandler(["menu", "vmenu"], cmd_menu))
        app.add_handler(CommandHandler(["flow", "vflow"], cmd_flow))
        app.add_handler(CommandHandler(["spam", "vspam"], cmd_spam))
        app.add_handler(CommandHandler(["nc", "vnc"], cmd_nc))
        app.add_handler(CommandHandler(["hunt", "vhunt"], cmd_hunt))
        app.add_handler(CommandHandler(["gpdp", "vgpdp"], cmd_gpdp))
        app.add_handler(CommandHandler(["stop", "off", "huntoff", "vhuntoff", "spamoff", "vspamoff", "ncoff", "vncoff", "gpdpoff"], cmd_stop))
        
        app.add_handler(CommandHandler("autoreply", cmd_autoreply))
        app.add_handler(CommandHandler("autophoto", cmd_autophoto))
        app.add_handler(CommandHandler("autosticker", cmd_autosticker))
        app.add_handler(CommandHandler("react", cmd_react))
        app.add_handler(CommandHandler("stopreply", cmd_stopreply))
        app.add_handler(CommandHandler("info", cmd_info))
        app.add_handler(CommandHandler("del", cmd_del))
        app.add_handler(CommandHandler("status", cmd_status))

        # Message Listener (Auto replies/reactions ke liye)
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message_features))
        
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        apps.append(app)
        print(f"  └─ ✅ Bot-{idx} fully active!")

    print("\n🔥 ALL BOTS ARE ONLINE AND EXECUTING AT MAXIMUM SPEED!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nEngine stopped.")
