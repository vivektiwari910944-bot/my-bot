import os, sys, threading, time, random, json, logging, io
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VivekEngine")

STATE_FILE = "vivek_state.json"

# ==========================================
# 🌐 DYNAMIC CONFIGURATION VARIABLES
# ==========================================
DEFAULT_BG = "https://images.alphacoders.com/132/1328400.jpeg"
bg_image_url = DEFAULT_BG

render_web_url = "https://my-bot-zlmx.onrender.com/"

def upload_to_web(bot, file_id):
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        response = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": downloaded_file},
            timeout=15
        )
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        logger.error(f"Upload to Web Error: {e}")
    return None

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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
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
        h1 {
            font-size: 2.6rem;
            color: #ff0055;
            text-shadow: 0 0 15px #ff0055, 0 0 30px #ff0055;
            margin-bottom: 8px;
            font-weight: 800;
            letter-spacing: 1px;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #00ffff;
            margin-bottom: 20px;
            text-shadow: 0 0 10px #00ffff;
            font-weight: 600;
        }
        
        .btn-render {
            display: inline-block;
            margin: 10px 0 25px 0;
            padding: 14px 32px;
            font-size: 1.15rem;
            font-weight: bold;
            color: #ffffff;
            background: linear-gradient(45deg, #ff0055, #7928ca, #00dfd8);
            background-size: 200% 200%;
            animation: gradientGlow 3s ease infinite;
            border: none;
            border-radius: 30px;
            text-decoration: none;
            box-shadow: 0 0 20px rgba(0, 223, 216, 0.8), 0 0 30px rgba(255, 0, 85, 0.6);
            transition: all 0.3s ease;
        }
        .btn-render:hover {
            transform: scale(1.06);
            box-shadow: 0 0 30px rgba(0, 223, 216, 1), 0 0 45px rgba(255, 0, 85, 0.9);
        }
        @keyframes gradientGlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .section-title {
            font-size: 1.35rem;
            color: #ffd700;
            border-bottom: 2px solid #ffd700;
            display: inline-block;
            margin: 22px 0 15px 0;
            padding-bottom: 4px;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
            font-weight: bold;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        .card {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(0, 240, 255, 0.45);
            padding: 15px;
            border-radius: 12px;
            transition: 0.3s ease;
            backdrop-filter: blur(8px);
        }
        .card:hover {
            transform: translateY(-5px);
            border-color: #ff0055;
            box-shadow: 0 0 20px rgba(255, 0, 85, 0.7);
            background: rgba(255, 255, 255, 0.22);
        }
        .cmd {
            font-weight: bold;
            color: #00ffff;
            font-size: 1.05rem;
            text-shadow: 0 0 6px #00ffff;
        }
        .desc {
            font-size: 0.9rem;
            color: #f1f1f1;
            margin-top: 5px;
            font-weight: 500;
        }
        .footer {
            margin-top: 25px;
            font-size: 1.1rem;
            color: #ff0055;
            text-shadow: 0 0 12px #ff0055;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>VIVEK MULTI-BOT EQUIPMENT</h1>
        <div class="subtitle">𝘝𝘐𝘝𝘌𝘒 𝘋𝘖𝘔𝘈𝘐𝘕 𝘌𝘟𝘗𝘈𝘕𝘋𝘌𝘋</div>

        <a href="{{ render_url }}" target="_blank" class="btn-render">🌐 OPEN VIVEK RENDER SERVER</a>

        <div class="section-title">🚀 SPAM, NC & FLOW COMMANDS</div>
        <div class="grid">
            <div class="card"><div class="cmd">vmenu</div><div class="desc">Show Menu with Domain Button</div></div>
            <div class="card"><div class="cmd">vflow &lt;delay&gt;</div><div class="desc">Set Universal Delay (Sec)</div></div>
            <div class="card"><div class="cmd">vwebbg</div><div class="desc">Set Photo as Web Background</div></div>
            <div class="card"><div class="cmd">vweburl &lt;link&gt;</div><div class="desc">Update Render Domain Link</div></div>
            <div class="card"><div class="cmd">vspam &lt;msg&gt;</div><div class="desc">Start fast spam</div></div>
            <div class="card"><div class="cmd">vspamoff</div><div class="desc">Stop active spam</div></div>
            <div class="card"><div class="cmd">vnc &lt;name&gt;</div><div class="desc">Name changer loop</div></div>
            <div class="card"><div class="cmd">vncoff</div><div class="desc">Stop name changer</div></div>
            <div class="card"><div class="cmd">vhunt &lt;target&gt;</div><div class="desc">Hunt down target</div></div>
            <div class="card"><div class="cmd">vhuntoff</div><div class="desc">Stop hunting</div></div>
            <div class="card"><div class="cmd">vgpdp &lt;url&gt;</div><div class="desc">Group DP from URL</div></div>
            <div class="card"><div class="cmd">vgpdpoff</div><div class="desc">Stop DP loop</div></div>
        </div>

        <div class="section-title">👑 AUTO REPLIES & REACTS</div>
        <div class="grid">
            <div class="card"><div class="cmd">vautoreply</div><div class="desc">Set auto text reply</div></div>
            <div class="card"><div class="cmd">vautophoto</div><div class="desc">Set auto photo reply</div></div>
            <div class="card"><div class="cmd">vautosticker</div><div class="desc">Set auto sticker reply</div></div>
            <div class="card"><div class="cmd">vreact &lt;emoji&gt;</div><div class="desc">Auto react to target</div></div>
            <div class="card"><div class="cmd">vstopreact</div><div class="desc">Stop auto react</div></div>
            <div class="card"><div class="cmd">vstopreply</div><div class="desc">Stop all auto replies</div></div>
        </div>

        <div class="section-title">🔍 INFO & MODERATION</div>
        <div class="grid">
            <div class="card"><div class="cmd">vinfo</div><div class="desc">Get user info & DP</div></div>
            <div class="card"><div class="cmd">vdel</div><div class="desc">Delete 100 messages</div></div>
            <div class="card"><div class="cmd">vautodelete</div><div class="desc">Auto delete target</div></div>
            <div class="card"><div class="cmd">vstatus</div><div class="desc">System status check</div></div>
        </div>

        <div class="footer">🟢 DEVELOPER : VIVEK TIWARI 🟢</div>
    </div>
</body>
</html>
"""

@web_app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, bg_url=bg_image_url, render_url=render_web_url)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()
    logger.info("Flask Web Engine server active!")

# ==========================================
# ⚙️ INITIAL SETUP
# ==========================================
def run_setup():
    print("\n🔥 VIVEK MULTI-BOT ENGINE — SETUP\n" + "━"*40)
    while True:
        owner_raw = input("Owner IDs (comma-separated, e.g. 123456,789012): ").strip()
        if owner_raw:
            break
        print("Owner ID required!")
    tokens = []
    print("\nEnter Bot tokens one by one. Press enter on blank line to finish.")
    i = 1
    while True:
        tok = input(f"  Bot Token {i} (blank = done): ").strip()
        if not tok:
            if not tokens:
                print("  At least one token is required!")
                continue
            break
        tokens.append(tok)
        i += 1
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"OWNER_IDS={owner_raw}\n")
        for j, t in enumerate(tokens, 1):
            f.write(f"BOT_TOKEN_{j}={t}\n")
    load_dotenv(override=True)
    print(f"\n✅ Setup complete! {len(tokens)} bot(s) configured.\n")

if not os.environ.get("OWNER_IDS") or not os.environ.get("BOT_TOKEN_1"):
    run_setup()

OWNER_IDS_RAW = os.environ.get("OWNER_IDS", "")
OWNER_IDS = set(int(x.strip()) for x in OWNER_IDS_RAW.split(",") if x.strip().isdigit())

BOT_TOKENS = []
i = 1
while True:
    tok = os.environ.get(f"BOT_TOKEN_{i}")
    if not tok:
        break
    BOT_TOKENS.append(tok.strip())
    i += 1

COOL_EMOJIS = ["🔥","⚡","👑","💀","🚀","💥","⚔️","🔱","🎯","🩸","💣","🐺","🦅","💎","🏆"]

def cool_emoji():
    return random.choice(COOL_EMOJIS)

HUNT_LINES = [
    "Bow down before the almighty master, you absolute non-entity! ⚔️",
    "You really thought you could survive in this arena? Know your place, worm! 💀",
    "Tremble before the absolute authority! You stand zero chance! 🔱",
    "Keep talking, but remember you are just fuel for the empire! 🚀",
    "A slave of destiny trying to fight the emperor? How pitiful! 👑"
]

def normalize_cmd(text: str) -> str:
    text = text.strip()
    if text.startswith("/"):
        text = text[1:]
    elif text.lower().startswith("v"):
        text = text[1:]
    parts = text.split(None, 1)
    if parts and "@" in parts[0]:
        parts[0] = parts[0].split("@")[0]
    return " ".join(parts)

_all_states = {}

def save_all_states():
    data = {}
    for label, state in _all_states.items():
        spam = {str(cid): {"active": state.spam_flags.get(cid, False), "msg": state.spam_msgs.get(cid, ""), "delay": state.spam_delay.get(cid, 0.1)} for cid in state.spam_flags}
        nc = {str(cid): {"active": state.nc_flags.get(cid, False), "name": state.nc_names.get(cid, ""), "delay": state.nc_delay.get(cid, 0.5)} for cid in state.nc_flags}
        hunt = {str(cid): {"active": state.hunt_flags.get(cid, False), "target": state.hunt_targets.get(cid, None), "delay": state.hunt_delay.get(cid, 0.5)} for cid in state.hunt_flags}
        gpdp = {str(cid): {"active": state.gpdp_flags.get(cid, False), "url": state.gpdp_urls.get(cid, ""), "delay": state.gpdp_delay.get(cid, 2.0)} for cid in state.gpdp_flags}
        
        data[label] = {
            "spam": spam, "nc": nc, "hunt": hunt, "gpdp": gpdp,
            "subadmins": list(state.subadmins),
            "auto_delete": {str(cid): list(uids) for cid, uids in state.auto_delete.items()},
            "auto_react": {f"{k[0]}_{k[1]}": v for k, v in state.auto_react.items()},
            "auto_reply": {f"{k[0]}_{k[1]}": v for k, v in state.auto_reply.items()},
            "auto_photo": {f"{k[0]}_{k[1]}": v for k, v in state.auto_photo.items()},
            "auto_sticker": {f"{k[0]}_{k[1]}": v for k, v in state.auto_sticker.items()}
        }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"State save error: {e}")

class BotState:
    def __init__(self):
        self.subadmins = set()
        self.spam_flags = {}
        self.spam_threads = {}
        self.spam_delay = {}
        self.spam_msgs = {}
        
        self.nc_flags = {}
        self.nc_threads = {}
        self.nc_delay = {}
        self.nc_names = {}

        self.hunt_flags = {}
        self.hunt_threads = {}
        self.hunt_targets = {}
        self.hunt_delay = {}

        self.gpdp_flags = {}
        self.gpdp_threads = {}
        self.gpdp_urls = {}
        self.gpdp_delay = {}
        
        self.auto_delete = {}
        self.auto_react = {}
        self.auto_reply = {}
        self.auto_photo = {}
        self.auto_sticker = {}

    def is_admin(self, user_id):
        return user_id in OWNER_IDS or user_id in self.subadmins

def spam_worker(bot, state, chat_id, text):
    while state.spam_flags.get(chat_id, False):
        try:
            bot.send_message(chat_id, text)
        except Exception:
            pass
        time.sleep(state.spam_delay.get(chat_id, 0.1))

def nc_worker(bot, state, chat_id, base_name):
    while state.nc_flags.get(chat_id, False):
        try:
            bot.set_chat_title(chat_id, f"{base_name} {cool_emoji()}")
        except Exception:
            pass
        time.sleep(state.nc_delay.get(chat_id, 0.5))

def hunt_worker(bot, state, chat_id, target_id):
    line_idx = 0
    while state.hunt_flags.get(chat_id, False) and state.hunt_targets.get(chat_id) == target_id:
        try:
            line = HUNT_LINES[line_idx % len(HUNT_LINES)]
            bot.send_message(chat_id, f"<a href='tg://user?id={target_id}'>Target</a> {line}", parse_mode="HTML")
            line_idx += 1
        except Exception:
            pass
        time.sleep(state.hunt_delay.get(chat_id, 0.5))

def gpdp_worker(bot, state, chat_id, photo_url):
    while state.gpdp_flags.get(chat_id, False):
        try:
            res = requests.get(photo_url, timeout=5)
            if res.status_code == 200:
                photo_bytes = io.BytesIO(res.content)
                photo_bytes.name = "gpdp.jpg"
                bot.set_chat_photo(chat_id, photo_bytes)
        except Exception as e:
            logger.warning(f"GPDP Update Error: {e}")
        time.sleep(state.gpdp_delay.get(chat_id, 2.0))

def get_target_user(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    parts = message.text.strip().split(None, 2) if message.text else []
    if len(parts) > 1:
        first_arg = parts[1].split()[0]
        if first_arg.isdigit():
            return int(first_arg)
    return None

def register_handlers(bot: telebot.TeleBot, state: BotState, label: str):

    def admin_only(message):
        uid = message.from_user.id if message.from_user else None
        return uid is not None and state.is_admin(uid)

    def send_and_react(chat_id, text, **kwargs):
        msg = bot.send_message(chat_id, text, **kwargs)
        try:
            bot.set_message_reaction(chat_id, msg.message_id, [telebot.types.ReactionTypeEmoji("🤣")])
        except Exception:
            pass
        return msg

    # ==========================================
    # 👑 WELCOME SLAVE ENTRY HANDLER
    # ==========================================
    @bot.message_handler(content_types=['new_chat_members'])
    def on_bot_joined(message):
        for member in message.new_chat_members:
            if member.id == bot.get_me().id:
                slave_welcome_msg = "We stand in the shadow of vivek Bend your knees! 🦁"
                send_and_react(message.chat.id, slave_welcome_msg)

    # ==========================================
    # 📜 MENU COMMAND HANDLER (VMENU)
    # ==========================================
    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "menu" and admin_only(m))
    def cmd_vmenu(message):
        menu_text = (
            "__________________________________\n"
            "𝘵𝘩𝘦 𝘴𝘭𝘢𝘷𝘦𝘴 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘰𝘯 𝘢𝘤𝘵𝘪𝘰𝘯 𝘓𝘰𝘳𝘥 🩸\n"
            "𝘤𝘰𝘮𝘮𝘢𝘯𝘥 𝘶𝘴 𝘵𝘰 𝘮𝘢𝘬𝘦 𝘦𝘮 𝘣𝘭𝘦𝘦𝘥!\n"
            "_________________________________\n"
            "𝘊𝘩𝘦𝘤𝘬 𝘔𝘦𝘯𝘶 𝘖𝘯 𝘓𝘶𝘹𝘶𝘳𝘪𝘰𝘴 𝘞𝘦𝘣𝘴𝘪𝘵𝘦"
        )
        
        markup = InlineKeyboardMarkup()
        web_button = InlineKeyboardButton(text="Vivek's domain 🌐", url=render_web_url)
        markup.add(web_button)

        msg = bot.send_message(message.chat.id, menu_text, reply_markup=markup)
        try:
            bot.set_message_reaction(message.chat.id, msg.message_id, [telebot.types.ReactionTypeEmoji("🤣")])
        except Exception:
            pass

    # ==========================================
    # 🎨 WEB BACKGROUND & RENDER URL SETTERS
    # ==========================================
    @bot.message_handler(func=lambda m: m.caption and normalize_cmd(m.caption) == "webbg" and admin_only(m), content_types=['photo'])
    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "webbg" and admin_only(m), content_types=['text'])
    def cmd_webbg(message):
        global bg_image_url
        file_id = None
        
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.reply_to_message and message.reply_to_message.photo:
            file_id = message.reply_to_message.photo[-1].file_id
            
        if file_id:
            msg = send_and_react(message.chat.id, "⏳ Uploading Image to Web Server...")
            direct_url = upload_to_web(bot, file_id)
            if direct_url:
                bg_image_url = direct_url
                send_and_react(message.chat.id, f"🎨 <b>WEB MENU BACKGROUND UPDATED!</b>\n\n🔗 <b>Image Link:</b> {direct_url}", parse_mode="HTML")
            else:
                send_and_react(message.chat.id, "❌ Failed to upload image. Please provide a direct Image URL!")
        else:
            parts = normalize_cmd(message.text).split(None, 1) if message.text else []
            if len(parts) > 1 and parts[1].startswith("http"):
                bg_image_url = parts[1].strip()
                send_and_react(message.chat.id, "🎨 <b>Web Menu Background URL Updated!</b>", parse_mode="HTML")
            else:
                send_and_react(message.chat.id, "❌ Reply to a photo with `vwebbg`, send a photo with `vwebbg` caption, or use `vwebbg <image_url>`", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("weburl ") and admin_only(m))
    def cmd_weburl(message):
        global render_web_url
        new_url = normalize_cmd(message.text)[7:].strip()
        if new_url.startswith("http"):
            render_web_url = new_url
            send_and_react(message.chat.id, f"🔗 <b>Render Web URL Updated!</b>\n\nNew URL: <code>{render_web_url}</code>", parse_mode="HTML")
        else:
            send_and_react(message.chat.id, "❌ Please provide a valid Render URL (e.g. `vweburl https://my-bot-zlmx.onrender.com/`)", parse_mode="Markdown")

    # ==========================================
    # ⚡ UNIVERSAL DELAY COMMAND (VFLOW)
    # ==========================================
    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("flow ") and admin_only(m))
    def cmd_vflow(message):
        parts = normalize_cmd(message.text).split()
        if len(parts) < 2:
            send_and_react(message.chat.id, "❌ Usage: `vflow <delay_seconds>`", parse_mode="Markdown")
            return
        try:
            delay = float(parts[1])
            if delay < 0.01:
                delay = 0.01
            cid = message.chat.id
            state.spam_delay[cid] = delay
            state.nc_delay[cid] = delay
            state.hunt_delay[cid] = delay
            state.gpdp_delay[cid] = delay
            save_all_states()
            send_and_react(message.chat.id, f"⚡ <b>Universal Delay Set To {delay} Seconds!</b>", parse_mode="HTML")
        except ValueError:
            send_and_react(message.chat.id, "❌ Please enter a valid number for delay.")

    # ==========================================
    # 🚀 SPAM, NC, HUNT & GROUP DP COMMANDS
    # ==========================================
    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("spam ") and admin_only(m))
    def cmd_spam(message):
        text = normalize_cmd(message.text)[5:].strip()
        if not text:
            send_and_react(message.chat.id, "❌ Please enter a message: `vspam <message>`", parse_mode="Markdown")
            return
        cid = message.chat.id
        state.spam_flags[cid] = True
        state.spam_msgs[cid] = text
        t = Thread(target=spam_worker, args=(bot, state, cid, text), daemon=True)
        state.spam_threads[cid] = t
        t.start()
        save_all_states()
        send_and_react(message.chat.id, "🚀 SPAM STARTED SUCCESSFULLY! 🔥")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "spamoff" and admin_only(m))
    def cmd_spamoff(message):
        cid = message.chat.id
        state.spam_flags[cid] = False
        save_all_states()
        send_and_react(message.chat.id, "🛑 SPAM STOPPED!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("nc ") and admin_only(m))
    def cmd_nc(message):
        name = normalize_cmd(message.text)[3:].strip()
        if not name:
            send_and_react(message.chat.id, "❌ Please enter a name: `vnc <Group Name>`", parse_mode="Markdown")
            return
        cid = message.chat.id
        state.nc_flags[cid] = True
        state.nc_names[cid] = name
        t = Thread(target=nc_worker, args=(bot, state, cid, name), daemon=True)
        state.nc_threads[cid] = t
        t.start()
        save_all_states()
        send_and_react(message.chat.id, "⚡ NAME CHANGER LOOP STARTED!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "ncoff" and admin_only(m))
    def cmd_ncoff(message):
        cid = message.chat.id
        state.nc_flags[cid] = False
        save_all_states()
        send_and_react(message.chat.id, "🛑 NAME CHANGER LOOP STOPPED!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("hunt") and admin_only(m))
    def cmd_hunt(message):
        target_id = get_target_user(message)
        if not target_id:
            send_and_react(message.chat.id, "❌ Reply to a user or provide ID: `vhunt <userID>`", parse_mode="Markdown")
            return
        cid = message.chat.id
        state.hunt_flags[cid] = True
        state.hunt_targets[cid] = target_id
        t = Thread(target=hunt_worker, args=(bot, state, cid, target_id), daemon=True)
        state.hunt_threads[cid] = t
        t.start()
        save_all_states()
        send_and_react(message.chat.id, f"⚔️ HUNTING STARTED ON USER: `{target_id}`", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "huntoff" and admin_only(m))
    def cmd_huntoff(message):
        cid = message.chat.id
        state.hunt_flags[cid] = False
        state.hunt_targets[cid] = None
        save_all_states()
        send_and_react(message.chat.id, "🛑 HUNTING STOPPED!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("gpdp ") and admin_only(m))
    def cmd_gpdp(message):
        url = normalize_cmd(message.text)[5:].strip()
        if not url.startswith("http"):
            send_and_react(message.chat.id, "❌ Please provide a valid Image URL: `vgpdp <URL>`", parse_mode="Markdown")
            return
        cid = message.chat.id
        state.gpdp_flags[cid] = True
        state.gpdp_urls[cid] = url
        t = Thread(target=gpdp_worker, args=(bot, state, cid, url), daemon=True)
        state.gpdp_threads[cid] = t
        t.start()
        save_all_states()
        send_and_react(message.chat.id, "🖼️ GROUP DP AUTO-CHANGER STARTED!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "gpdpoff" and admin_only(m))
    def cmd_gpdpoff(message):
        cid = message.chat.id
        state.gpdp_flags[cid] = False
        save_all_states()
        send_and_react(message.chat.id, "🛑 GROUP DP LOOP STOPPED!")

    # ==========================================
    # 👑 AUTO REPLIES & AUTO REACTS
    # ==========================================
    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("autoreply") and admin_only(m))
    def cmd_autoreply(message):
        target_id = get_target_user(message)
        parts = message.text.strip().split(None, 2)
        if not target_id or len(parts) < 3:
            send_and_react(message.chat.id, "❌ Reply to user or specify ID & text: `vautoreply <userID> <text>`", parse_mode="Markdown")
            return
        text = parts[2] if parts[1].isdigit() else message.text.split(None, 1)[1]
        cid = message.chat.id
        state.auto_reply[(cid, target_id)] = text
        save_all_states()
        send_and_react(message.chat.id, f"👑 AUTO-REPLY SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("autophoto") and admin_only(m))
    def cmd_autophoto(message):
        target_id = get_target_user(message)
        parts = normalize_cmd(message.text).split(None, 2)
        if not target_id or len(parts) < 2:
            send_and_react(message.chat.id, "❌ Reply or specify user & URL: `vautophoto <userID> <photo_url>`", parse_mode="Markdown")
            return
        url = parts[-1]
        cid = message.chat.id
        state.auto_photo[(cid, target_id)] = url
        save_all_states()
        send_and_react(message.chat.id, f"🖼️ AUTO-PHOTO SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("autosticker") and admin_only(m))
    def cmd_autosticker(message):
        target_id = get_target_user(message)
        parts = normalize_cmd(message.text).split(None, 2)
        if not target_id or len(parts) < 2:
            send_and_react(message.chat.id, "❌ Reply or specify user & Sticker ID: `vautosticker <userID> <sticker_file_id>`", parse_mode="Markdown")
            return
        sticker_id = parts[-1]
        cid = message.chat.id
        state.auto_sticker[(cid, target_id)] = sticker_id
        save_all_states()
        send_and_react(message.chat.id, f"🎯 AUTO-STICKER SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("react ") and admin_only(m))
    def cmd_react(message):
        target_id = get_target_user(message)
        parts = normalize_cmd(message.text).split()
        if not target_id or len(parts) < 2:
            send_and_react(message.chat.id, "❌ Please enter an Emoji: `vreact <emoji> <userID>`", parse_mode="Markdown")
            return
        emoji = parts[1]
        cid = message.chat.id
        state.auto_react[(cid, target_id)] = emoji
        save_all_states()
        send_and_react(message.chat.id, f"👑 AUTO-REACT `{emoji}` SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "stopreact" and admin_only(m))
    def cmd_stopreact(message):
        cid = message.chat.id
        keys_to_del = [k for k in state.auto_react if k[0] == cid]
        for k in keys_to_del:
            del state.auto_react[k]
        save_all_states()
        send_and_react(message.chat.id, "🛑 AUTO-REACTS STOPPED!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "stopreply" and admin_only(m))
    def cmd_stopreply(message):
        cid = message.chat.id
        for store in (state.auto_reply, state.auto_photo, state.auto_sticker):
            keys = [k for k in store if k[0] == cid]
            for k in keys:
                del store[k]
        save_all_states()
        send_and_react(message.chat.id, "🛑 ALL AUTO REPLIES STOPPED!")

    # ==========================================
    # 🔍 INFO & MODERATION COMMANDS
    # ==========================================
    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "info" and admin_only(m))
    def cmd_info(message):
        target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        info_text = (
            f"🔍 <b>USER INFORMATION</b>\n\n"
            f"👤 <b>Name:</b> {target_user.first_name} {target_user.last_name or ''}\n"
            f"🆔 <b>User ID:</b> <code>{target_user.id}</code>\n"
            f"🌐 <b>Username:</b> @{target_user.username if target_user.username else 'N/A'}\n"
            f"🤖 <b>Is Bot:</b> {target_user.is_bot}"
        )
        try:
            photos = bot.get_user_profile_photos(target_user.id, limit=1)
            if photos.total_count > 0:
                bot.send_photo(message.chat.id, photos.photos[0][-1].file_id, caption=info_text, parse_mode="HTML")
            else:
                send_and_react(message.chat.id, info_text, parse_mode="HTML")
        except Exception:
            send_and_react(message.chat.id, info_text, parse_mode="HTML")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "del" and admin_only(m))
    def cmd_del(message):
        cid = message.chat.id
        mid = message.message_id
        deleted = 0
        for i in range(mid, max(mid - 100, 0), -1):
            try:
                if bot.delete_message(cid, i):
                    deleted += 1
            except Exception:
                pass
        send_and_react(cid, f"🗑️ Cleaned {deleted} messages!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("autodelete") and admin_only(m))
    def cmd_autodelete(message):
        target_id = get_target_user(message)
        if not target_id:
            send_and_react(message.chat.id, "❌ Reply to user or provide ID: `vautodelete <userID>`", parse_mode="Markdown")
            return
        cid = message.chat.id
        if cid not in state.auto_delete:
            state.auto_delete[cid] = set()
        state.auto_delete[cid].add(target_id)
        save_all_states()
        send_and_react(message.chat.id, f"🗑️ AUTO-DELETE ENABLED FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "status" and admin_only(m))
    def cmd_status(message):
        cid = message.chat.id
        status_msg = (
            f"⚡ <b>VIVEK ENGINE STATUS</b>\n\n"
            f"🚀 <b>Spam Active:</b> {state.spam_flags.get(cid, False)}\n"
            f"⚡ <b>NC Loop Active:</b> {state.nc_flags.get(cid, False)}\n"
            f"⚔️ <b>Hunt Target:</b> {state.hunt_targets.get(cid, 'None')}\n"
            f"🖼️ <b>Group DP Loop:</b> {state.gpdp_flags.get(cid, False)}\n"
            f"⏱️ <b>Current Delay:</b> {state.spam_delay.get(cid, 0.1)}s"
        )
        send_and_react(cid, status_msg, parse_mode="HTML")

    # ==========================================
    # 📩 GLOBAL MESSAGE EVENT LISTENER
    # ==========================================
    @bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'sticker', 'animation'])
    def handle_all_messages(message):
        if not message.from_user:
            return
        
        cid = message.chat.id
        uid = message.from_user.id

        # 1. Auto Delete Check
        if cid in state.auto_delete and uid in state.auto_delete[cid]:
            try:
                bot.delete_message(cid, message.message_id)
                return
            except Exception:
                pass

        # 2. Auto Reaction
        if (cid, uid) in state.auto_react:
            try:
                emoji = state.auto_react[(cid, uid)]
                bot.set_message_reaction(cid, message.message_id, [telebot.types.ReactionTypeEmoji(emoji)])
            except Exception:
                pass

        # 3. Auto Text Reply
        if (cid, uid) in state.auto_reply:
            try:
                bot.reply_to(message, state.auto_reply[(cid, uid)])
            except Exception:
                pass

        # 4. Auto Photo Reply
        if (cid, uid) in state.auto_photo:
            try:
                bot.send_photo(cid, state.auto_photo[(cid, uid)], reply_to_message_id=message.message_id)
            except Exception:
                pass

        # 5. Auto Sticker Reply
        if (cid, uid) in state.auto_sticker:
            try:
                bot.send_sticker(cid, state.auto_sticker[(cid, uid)], reply_to_message_id=message.message_id)
            except Exception:
                pass

# ==========================================
# 🚀 MAIN BOT INITIATION
# ==========================================
def main():
    keep_alive()
    threads = []
    
    for idx, token in enumerate(BOT_TOKENS, 1):
        label = f"Bot-{idx}"
        # ThreadPoolExecutor to handle message events simultaneously (Speed optimization)
        bot = telebot.TeleBot(token, parse_mode=None, threaded=True, num_threads=20)
        state = BotState()
        _all_states[label] = state
        
        register_handlers(bot, state, label)
        
        def start_polling(b=bot, l=label):
            logger.info(f"Starting polling for {l}...")
            while True:
                try:
                    # Low latency parameters for fast response
                    b.infinity_polling(timeout=10, long_polling_timeout=2)
                except Exception as e:
                    logger.error(f"Error on {l}: {e}")
                    time.sleep(1)

        t = Thread(target=start_polling, daemon=True)
        t.start()
        threads.append(t)

    logger.info("All Multi-Bot Instances Running Successfully!")
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
