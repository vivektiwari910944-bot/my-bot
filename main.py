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
            <div class="card"><div class="cmd">vmenu</div><div class="desc">Show Menu</div></div>
            <div class="card"><div class="cmd">vhunt &lt;target&gt;</div><div class="desc">Hunt down target</div></div>
            <div class="card"><div class="cmd">stop / vhuntoff</div><div class="desc">Chat-Specific Kill Switch</div></div>
            <div class="card"><div class="cmd">vspam &lt;msg&gt;</div><div class="desc">Start fast spam</div></div>
            <div class="card"><div class="cmd">vnc &lt;name&gt;</div><div class="desc">Name changer loop</div></div>
            <div class="card"><div class="cmd">vgpdp &lt;url&gt;</div><div class="desc">Group DP changer</div></div>
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

def normalize_cmd(text: str) -> str:
    text = text.strip()
    if text.startswith("/"): text = text[1:]
    elif text.lower().startswith("v"): text = text[1:]
    parts = text.split(None, 1)
    if parts and "@" in parts[0]: parts[0] = parts[0].split("@")[0]
    return " ".join(parts)

_all_states = {}
_bot_instances_list = [] 

class BotState:
    def __init__(self):
        self.subadmins = set()
        self.spam_flags = {}
        self.spam_delay = {}
        self.spam_msgs = {}
        
        self.nc_flags = {}
        self.nc_delay = {}
        self.nc_names = {}

        self.hunt_flags = {}
        self.hunt_targets = {}
        self.hunt_delay = {}

        self.gpdp_flags = {}
        self.gpdp_delay = {}
        self.gpdp_urls = {}

        self.auto_delete = {}
        self.auto_react = {}
        self.auto_reply = {}
        self.auto_photo = {}
        self.auto_sticker = {}

    def is_admin(self, user_id):
        return user_id in OWNER_IDS or user_id in self.subadmins

thread_pool = ThreadPoolExecutor(max_workers=50)

# ==========================================
# 🚀 PARALLEL WORKERS
# ==========================================
def parallel_spam_worker(chat_id, text):
    while True:
        active_bots = [(b, st) for b, st, l in _bot_instances_list if st.spam_flags.get(chat_id, False)]
        if not active_bots: break
        delay = active_bots[0][1].spam_delay.get(chat_id, 0.05)
        
        futures = [thread_pool.submit(b.send_message, chat_id, text) for b, st in active_bots if st.spam_flags.get(chat_id, False)]
        for f in futures:
            try: f.result()
            except Exception: pass
        time.sleep(delay)

def parallel_nc_worker(chat_id, base_name):
    while True:
        active_bots = [(b, st) for b, st, l in _bot_instances_list if st.nc_flags.get(chat_id, False)]
        if not active_bots: break
        delay = active_bots[0][1].nc_delay.get(chat_id, 0.1)

        def fire_nc(bot_obj, cid, name_val):
            try:
                bot_obj.set_chat_title(cid, f"{name_val} {cool_emoji()}")
            except Exception:
                pass

        futures = [thread_pool.submit(fire_nc, b, chat_id, base_name) for b, st in active_bots if st.nc_flags.get(chat_id, False)]
        for f in futures:
            try: f.result()
            except Exception: pass
        time.sleep(delay)

def parallel_hunt_worker(chat_id, target_id):
    line_idx = 0
    while True:
        active_bots = [(b, st) for b, st, l in _bot_instances_list if st.hunt_flags.get(chat_id, False) and st.hunt_targets.get(chat_id) == target_id]
        if not active_bots: break
        
        delay = active_bots[0][1].hunt_delay.get(chat_id, 0.5)
        line = HUNT_LINES[line_idx % len(HUNT_LINES)]
        line_idx += 1

        def fire_hunt(bot_obj, cid, tid, txt):
            try:
                bot_obj.send_message(cid, f"<a href='tg://user?id={tid}'>Target</a> {txt}", parse_mode="HTML")
            except Exception:
                pass

        futures = [thread_pool.submit(fire_hunt, b, chat_id, target_id, line) for b, st in active_bots if st.hunt_flags.get(chat_id, False) and st.hunt_targets.get(chat_id) == target_id]
        for f in futures:
            try: f.result()
            except Exception: pass
        time.sleep(delay)

def gpdp_worker(bot, state, chat_id, photo_url):
    while state.gpdp_flags.get(chat_id, False):
        try:
            res = requests.get(photo_url, timeout=5)
            if res.status_code == 200:
                photo_bytes = io.BytesIO(res.content)
                photo_bytes.name = "gpdp.jpg"
                bot.set_chat_photo(chat_id, photo_bytes)
        except Exception:
            pass
        time.sleep(state.gpdp_delay.get(chat_id, 2.0))

def get_target_user(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    parts = message.text.strip().split(None, 2) if message.text else []
    if len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

def register_handlers(bot: telebot.TeleBot, state: BotState, label: str):
    def admin_only(message):
        uid = message.from_user.id if message.from_user else None
        return uid is not None and state.is_admin(uid)

    def send_and_react(chat_id, text, **kwargs):
        msg = bot.send_message(chat_id, text, **kwargs)
        try: bot.set_message_reaction(chat_id, msg.message_id, [telebot.types.ReactionTypeEmoji("🤣")])
        except Exception: pass
        return msg

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "menu" and admin_only(m))
    def cmd_vmenu(message):
        menu_text = "__________________________________\n𝘵𝘩𝘦 𝘴𝘭𝘢𝘷𝘦𝘴 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘰𝘯 𝘢𝘤𝘵𝘪𝘰𝘯 𝘓𝘰𝘳𝘥 🩸\n_________________________________"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Vivek's domain 🌐", url=render_web_url))
        send_and_react(message.chat.id, menu_text, reply_markup=markup)

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("flow ") and admin_only(m))
    def cmd_vflow(message):
        parts = normalize_cmd(message.text).split()
        if len(parts) < 2: return
        try:
            delay = float(parts[1])
            if delay < 0.01: delay = 0.01
            cid = message.chat.id
            state.spam_delay[cid] = delay
            state.nc_delay[cid] = delay
            state.hunt_delay[cid] = delay
            state.gpdp_delay[cid] = delay
            send_and_react(message.chat.id, f"⚡ Universal Delay Set To {delay}s!")
        except ValueError:
            pass

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("spam ") and admin_only(m))
    def cmd_spam(message):
        text = normalize_cmd(message.text)[5:].strip()
        if not text: return
        cid = message.chat.id
        for _, st, _ in _bot_instances_list:
            st.spam_flags[cid] = True
            st.spam_msgs[cid] = text
        Thread(target=parallel_spam_worker, args=(cid, text), daemon=True).start()
        send_and_react(message.chat.id, "🚀 BAWANDAR SPAM STARTED! 🔥")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("nc ") and admin_only(m))
    def cmd_nc(message):
        name = normalize_cmd(message.text)[3:].strip()
        if not name: return
        cid = message.chat.id
        for _, st, _ in _bot_instances_list:
            st.nc_flags[cid] = True
            st.nc_names[cid] = name
        Thread(target=parallel_nc_worker, args=(cid, name), daemon=True).start()
        send_and_react(message.chat.id, "⚡ NAME CHANGER STARTED! 🔥")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("hunt") and admin_only(m))
    def cmd_hunt(message):
        target_id = get_target_user(message)
        if not target_id: return
        cid = message.chat.id
        for _, st, _ in _bot_instances_list:
            st.hunt_flags[cid] = True
            st.hunt_targets[cid] = target_id
            
        Thread(target=parallel_hunt_worker, args=(cid, target_id), daemon=True).start()
        send_and_react(message.chat.id, f"⚔️ CONTINUOUS HUNTING STARTED ON USER: `{target_id}`", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("gpdp ") and admin_only(m))
    def cmd_gpdp(message):
        url = normalize_cmd(message.text)[5:].strip()
        if not url.startswith("http"): return
        cid = message.chat.id
        state.gpdp_flags[cid] = True
        state.gpdp_urls[cid] = url
        Thread(target=gpdp_worker, args=(bot, state, cid, url), daemon=True).start()
        send_and_react(message.chat.id, "🖼️ GROUP DP LOOP STARTED!")

    # 👇 CHAT-SPECIFIC UNIVERSAL STOP COMMAND (Sirf usi chat ka sab band karega)
    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) in ["stop", "off", "huntoff", "vhuntoff", "spamoff", "vspamoff", "ncoff", "vncoff", "gpdpoff"] and admin_only(m))
    def cmd_universal_stop(message):
        cid = message.chat.id
        for _, st, _ in _bot_instances_list:
            st.hunt_flags[cid] = False
            st.hunt_targets[cid] = None
            st.spam_flags[cid] = False
            st.nc_flags[cid] = False
            st.gpdp_flags[cid] = False
        send_and_react(message.chat.id, "🛑 CHAT STOPPED SUCCESSFULLY! ALL LOOPS HALTED HERE! ⚡")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("autoreply") and admin_only(m))
    def cmd_autoreply(message):
        target_id = get_target_user(message)
        parts = message.text.strip().split(None, 2)
        if not target_id or len(parts) < 3: return
        text = parts[2] if parts[1].isdigit() else message.text.split(None, 1)[1]
        cid = message.chat.id
        state.auto_reply[(cid, target_id)] = text
        send_and_react(message.chat.id, f"👑 AUTO-REPLY SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("autophoto") and admin_only(m))
    def cmd_autophoto(message):
        target_id = get_target_user(message)
        parts = message.text.strip().split(None, 2)
        if not target_id or len(parts) < 2: return
        url = parts[-1]
        cid = message.chat.id
        state.auto_photo[(cid, target_id)] = url
        send_and_react(message.chat.id, f"🖼️ AUTO-PHOTO SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("autosticker") and admin_only(m))
    def cmd_autosticker(message):
        target_id = get_target_user(message)
        parts = message.text.strip().split(None, 2)
        if not target_id or len(parts) < 2: return
        sticker_id = parts[-1]
        cid = message.chat.id
        state.auto_sticker[(cid, target_id)] = sticker_id
        send_and_react(message.chat.id, f"🎯 AUTO-STICKER SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text).startswith("react ") and admin_only(m))
    def cmd_react(message):
        target_id = get_target_user(message)
        parts = normalize_cmd(message.text).split()
        if not target_id or len(parts) < 2: return
        emoji = parts[1]
        cid = message.chat.id
        state.auto_react[(cid, target_id)] = emoji
        send_and_react(message.chat.id, f"👑 AUTO-REACT SET FOR `{target_id}`!", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "stopreply" and admin_only(m))
    def cmd_stopreply(message):
        cid = message.chat.id
        for store in (state.auto_reply, state.auto_photo, state.auto_sticker):
            for k in [k for k in store if k[0] == cid]: del store[k]
        send_and_react(message.chat.id, "🛑 ALL AUTO REPLIES STOPPED!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "info" and admin_only(m))
    def cmd_info(message):
        u = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        txt = f"🔍 <b>USER INFO</b>\nName: {u.first_name}\nID: <code>{u.id}</code>\nUsername: @{u.username or 'N/A'}"
        send_and_react(message.chat.id, txt, parse_mode="HTML")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "del" and admin_only(m))
    def cmd_del(message):
        cid = message.chat.id
        mid = message.message_id
        for i in range(mid, max(mid - 100, 0), -1):
            try: bot.delete_message(cid, i)
            except Exception: pass
        send_and_react(cid, "🗑️ Cleaned messages!")

    @bot.message_handler(func=lambda m: m.text and normalize_cmd(m.text) == "status" and admin_only(m))
    def cmd_status(message):
        cid = message.chat.id
        msg = f"⚡ <b>ENGINE STATUS</b>\nSpam: {state.spam_flags.get(cid, False)}\nNC: {state.nc_flags.get(cid, False)}\nHunt: {state.hunt_flags.get(cid, False)}"
        send_and_react(cid, msg, parse_mode="HTML")

    @bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'sticker', 'animation'])
    def handle_all_messages(message):
        if not message.from_user: return
        cid = message.chat.id
        uid = message.from_user.id

        if (cid, uid) in state.auto_react:
            try: bot.set_message_reaction(cid, message.message_id, [telebot.types.ReactionTypeEmoji(state.auto_react[(cid, uid)])])
            except Exception: pass

        if (cid, uid) in state.auto_reply:
            try: bot.reply_to(message, state.auto_reply[(cid, uid)])
            except Exception: pass

        if (cid, uid) in state.auto_photo:
            try: bot.send_photo(cid, state.auto_photo[(cid, uid)], reply_to_message_id=message.message_id)
            except Exception: pass

        if (cid, uid) in state.auto_sticker:
            try: bot.send_sticker(cid, state.auto_sticker[(cid, uid)], reply_to_message_id=message.message_id)
            except Exception: pass

def main():
    keep_alive()
    threads = []
    for idx, token in enumerate(BOT_TOKENS, 1):
        label = f"Bot-{idx}"
        bot = telebot.TeleBot(token, parse_mode=None, threaded=True, num_threads=50)
        state = BotState()
        _all_states[label] = state
        _bot_instances_list.append((bot, state, label))
        register_handlers(bot, state, label)
        
        def start_polling(b=bot, l=label):
            while True:
                try: b.infinity_polling(timeout=2, long_polling_timeout=1, skip_pending=True, interval=0)
                except Exception: time.sleep(1)

        t = Thread(target=start_polling, daemon=True)
        t.start()
        threads.append(t)

    logger.info("All Multi-Bot Instances Running Successfully!")
    for t in threads: t.join()

if __name__ == "__main__":
    main()
