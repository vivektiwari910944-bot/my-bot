import os, sys, threading, time, random, json, logging
from threading import Thread
import telebot
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VivekEngine")

STATE_FILE = "vivek_state.json"

# ==========================================
# 🌐 FLASK KEEP ALIVE SERVER (FOR 24/7 HOSTING)
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🔥 Vivek Multi-Bot Engine is Running 24/7! 🔥"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()
    logger.info("Flask Keep-Alive server active!")

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
    print("\nBot tokens ek ek karke daalo. Khatam karne ke liye blank Enter karo.")
    i = 1
    while True:
        tok = input(f"  Bot Token {i} (blank = done): ").strip()
        if not tok:
            if not tokens:
                print("  Kam se kam ek token chahiye!")
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

def normalize(text: str) -> str:
    text = text.strip()
    if text.startswith("/"):
        text = text[1:]
    parts = text.split(None, 1)
    if parts and "@" in parts[0]:
        parts[0] = parts[0].split("@")[0]
    return " ".join(parts)

_all_states = {}

def save_all_states():
    data = {}
    for label, state in _all_states.items():
        spam = {str(cid): {"active": state.spam_flags.get(cid, False), "msg": state.spam_msgs.get(cid, ""), "delay": state.spam_delay.get(cid, 0.5)} for cid in state.spam_flags}
        nc = {str(cid): {"active": state.nc_flags.get(cid, False), "name": state.nc_names.get(cid, ""), "delay": state.nc_delay.get(cid, 1.0)} for cid in state.nc_flags}
        dc = {str(cid): {"active": state.dc_flags.get(cid, False), "desc": state.dc_descs.get(cid, ""), "delay": state.dc_delay.get(cid, 1.5)} for cid in state.dc_flags}
        data[label] = {
            "spam": spam, "nc": nc, "dc": dc,
            "subadmins": list(state.subadmins),
            "auto_delete": {str(cid): list(uids) for cid, uids in state.auto_delete.items()},
            "auto_react": {str(k): v for k, v in state.auto_react.items()},
            "auto_reply": {str(k): v for k, v in state.auto_reply.items()},
            "auto_photo": {str(k): v for k, v in state.auto_photo.items()},
            "auto_sticker": {str(k): v for k, v in state.auto_sticker.items()}
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
        
        self.dc_flags = {}
        self.dc_threads = {}
        self.dc_delay = {}
        self.dc_descs = {}
        
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
        time.sleep(state.spam_delay.get(chat_id, 0.5))

def nc_worker(bot, state, chat_id, base_name):
    while state.nc_flags.get(chat_id, False):
        try:
            bot.set_chat_title(chat_id, f"{base_name} {cool_emoji()}")
        except Exception:
            pass
        time.sleep(state.nc_delay.get(chat_id, 1.0))

def dc_worker(bot, state, chat_id, base_desc):
    while state.dc_flags.get(chat_id, False):
        try:
            bot.set_chat_description(chat_id, f"{base_desc} {cool_emoji()}")
        except Exception:
            pass
        time.sleep(state.dc_delay.get(chat_id, 1.5))

def resume_state(label, state, bot):
    if not os.path.exists(STATE_FILE):
        return
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
    except Exception:
        return
    if label not in data:
        return
    d = data[label]
    state.subadmins = set(d.get("subadmins", []))
    state.auto_delete = {int(cid): set(uids) for cid, uids in d.get("auto_delete", {}).items()}
    state.auto_react = {int(k): v for k, v in d.get("auto_react", {}).items() if k.lstrip("-").isdigit()}
    state.auto_reply = {int(k): v for k, v in d.get("auto_reply", {}).items() if k.lstrip("-").isdigit()}
    state.auto_photo = {int(k): v for k, v in d.get("auto_photo", {}).items() if k.lstrip("-").isdigit()}
    state.auto_sticker = {int(k): v for k, v in d.get("auto_sticker", {}).items() if k.lstrip("-").isdigit()}
    
    for cid_str, info in d.get("spam", {}).items():
        if info.get("active") and info.get("msg"):
            cid = int(cid_str)
            state.spam_delay[cid] = info.get("delay", 0.5)
            state.spam_flags[cid] = True
            state.spam_msgs[cid] = info["msg"]
            t = threading.Thread(target=spam_worker, args=(bot, state, cid, info["msg"]), daemon=True)
            state.spam_threads[cid] = t
            t.start()
            
    for cid_str, info in d.get("nc", {}).items():
        if info.get("active") and info.get("name"):
            cid = int(cid_str)
            state.nc_delay[cid] = info.get("delay", 1.0)
            state.nc_flags[cid] = True
            state.nc_names[cid] = info["name"]
            t = threading.Thread(target=nc_worker, args=(bot, state, cid, info["name"]), daemon=True)
            state.nc_threads[cid] = t
            t.start()

def register_handlers(bot: telebot.TeleBot, state: BotState, label: str):

    def admin_only(message):
        uid = message.from_user.id if message.from_user else None
        return uid is not None and state.is_admin(uid)

    def save():
        save_all_states()

    @bot.message_handler(commands=["start", "menu"])
    def send_menu(message):
        if not admin_only(message):
            return
        bot.reply_to(message,
            "🔥 <b><u>𝑽𝑰𝑽𝑬𝑲 𝑴𝑼𝑳𝑻𝑰-𝑩𝑶𝑻 𝑬𝑵𝑮𝑰𝑵𝑬</u></b> [" + label + "] 🔥\n"
            "⚡ <i>POWERED BY VIVEK TIWARI</i> ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚀 <b>[ 𝗦𝗣𝗔𝗠 𝗖𝗢𝗡𝗧𝗥𝗢𝗟 ]</b>\n"
            "  ✦ <code>/spam &lt;msg&gt;</code> — Start Fast Spam\n"
            "  ✦ <code>/spamoff</code> — Stop Spamming\n"
            "  ✦ <code>/spam delay &lt;ms&gt;</code> — Speed Adjust (ms)\n\n"
            "⚡ <b>[ 𝗙𝗔𝗦𝗧 𝗚𝗥𝗢𝗨𝗣 𝗥𝗘𝗡𝗔𝗠𝗘𝗥 ]</b>\n"
            "  ✦ <code>/nc &lt;name&gt;</code> — Fast Auto Name Changer\n"
            "  ✦ <code>/ncoff</code> — Stop Name Changer\n"
            "  ✦ <code>/nc delay &lt;ms&gt;</code> — Speed Adjust (ms)\n\n"
            "👑 <b>[ 𝗔𝗨𝗧𝗢 𝗥𝗘𝗣𝗟𝗜𝗘𝗦 &amp; 𝗠𝗘𝗗𝗜𝗔 ]</b>\n"
            "  ✦ <code>/autoreply &lt;text&gt;</code> — Auto Slide Text Reply\n"
            "  ✦ <code>/autophoto &lt;url&gt;</code> — Auto Photo Reply\n"
            "  ✦ <code>/autosticker &lt;id&gt;</code> — Auto Sticker Reply\n"
            "  ✦ <code>/stopreply</code> — Stop All Auto Replies\n\n"
            "💀 <b>[ 𝗔𝗨𝗧𝗢 𝗗𝗘𝗟𝗘𝗧𝗘 &amp; 𝗥𝗘𝗔𝗖𝗧 ]</b>\n"
            "  ✦ <code>/auto_delete &lt;id&gt;</code> — Delete target user msgs\n"
            "  ✦ <code>/react &lt;emoji&gt;</code> — Auto Emoji Reaction\n"
            "  ✦ <code>/stopreact</code> — Stop Reactions\n\n"
            "🔱 <b>[ 𝗔𝗗𝗠𝗜𝗡 𝗖𝗢𝗡𝗧𝗥𝗢𝗟 ]</b>\n"
            "  ✦ <code>/addsubadmin &lt;id/@user&gt;</code>\n"
            "  ✦ <code>/removesubadmin &lt;id/@user&gt;</code>\n"
            "  ✦ <code>/status</code> — System Monitor\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 <i>DESIGNED BY VIVEK</i> 👑",
            parse_mode="HTML"
        )

    @bot.message_handler(commands=["spam"])
    def handle_spam_cmd(message):
        if not admin_only(message): return
        chat_id = message.chat.id
        text = normalize(message.text)
        if text.lower() == "spam off":
            state.spam_flags[chat_id] = False
            state.spam_msgs.pop(chat_id, None)
            save()
            bot.reply_to(message, "🔥 Spam stopped!")
            return
        if text.lower().startswith("spam delay"):
            parts = text.split()
            if len(parts) >= 3 and parts[2].isdigit():
                state.spam_delay[chat_id] = int(parts[2]) / 1000.0
                save()
                bot.reply_to(message, f"⚡ Spam delay: {parts[2]}ms")
            return
        parts = text.split(" ", 1)
        if len(parts) < 2: return
        spam_msg = parts[1].strip()
        state.spam_flags[chat_id] = False
        time.sleep(0.1)
        state.spam_flags[chat_id] = True
        state.spam_msgs[chat_id] = spam_msg
        save()
        t = threading.Thread(target=spam_worker, args=(bot, state, chat_id, spam_msg), daemon=True)
        state.spam_threads[chat_id] = t
        t.start()
        bot.reply_to(message, f"🚀 Fast Spamming Started: \"{spam_msg}\"")

    @bot.message_handler(commands=["spamoff"])
    def spam_off_cmd(message):
        if not admin_only(message): return
        state.spam_flags[message.chat.id] = False
        state.spam_msgs.pop(message.chat.id, None)
        save()
        bot.reply_to(message, "🔥 Spam stopped!")

    @bot.message_handler(commands=["nc"])
    def handle_nc_cmd(message):
        if not admin_only(message): return
        if message.chat.type == "private": return
        chat_id = message.chat.id
        text = normalize(message.text)
        if text.lower() == "nc off":
            state.nc_flags[chat_id] = False
            state.nc_names.pop(chat_id, None)
            save()
            bot.reply_to(message, "🔥 NC stopped!")
            return
        if text.lower().startswith("nc delay"):
            parts = text.split()
            if len(parts) >= 3 and parts[2].isdigit():
                state.nc_delay[chat_id] = int(parts[2]) / 1000.0
                save()
                bot.reply_to(message, f"⚡ NC delay: {parts[2]}ms")
            return
        parts = text.split(" ", 1)
        if len(parts) < 2: return
        base_name = parts[1].strip()
        state.nc_flags[chat_id] = False
        time.sleep(0.1)
        state.nc_flags[chat_id] = True
        state.nc_names[chat_id] = base_name
        save()
        t = threading.Thread(target=nc_worker, args=(bot, state, chat_id, base_name), daemon=True)
        state.nc_threads[chat_id] = t
        t.start()
        bot.reply_to(message, f"⚡ Fast NC Started: '{base_name}'")

    @bot.message_handler(commands=["ncoff"])
    def nc_off_cmd(message):
        if not admin_only(message): return
        state.nc_flags[message.chat.id] = False
        state.nc_names.pop(message.chat.id, None)
        save()
        bot.reply_to(message, "🔥 NC stopped!")

    # Auto Reply Commands
    @bot.message_handler(commands=["autoreply"])
    def set_autoreply(message):
        if not admin_only(message): return
        parts = message.text.split(" ", 1)
        if len(parts) < 2: return
        state.auto_reply[message.chat.id] = parts[1].strip()
        save()
        bot.reply_to(message, f"💬 Auto Slide Reply Set: {parts[1].strip()}")

    @bot.message_handler(commands=["autophoto"])
    def set_autophoto(message):
        if not admin_only(message): return
        parts = message.text.split(" ", 1)
        if len(parts) < 2: return
        state.auto_photo[message.chat.id] = parts[1].strip()
        save()
        bot.reply_to(message, "🖼️ Auto Photo Reply Set!")

    @bot.message_handler(commands=["autosticker"])
    def set_autosticker(message):
        if not admin_only(message): return
        parts = message.text.split(" ", 1)
        if len(parts) < 2: return
        state.auto_sticker[message.chat.id] = parts[1].strip()
        save()
        bot.reply_to(message, "🎯 Auto Sticker Reply Set!")

    @bot.message_handler(commands=["stopreply"])
    def stop_replies(message):
        if not admin_only(message): return
        cid = message.chat.id
        state.auto_reply.pop(cid, None)
        state.auto_photo.pop(cid, None)
        state.auto_sticker.pop(cid, None)
        save()
        bot.reply_to(message, "🔥 All Auto Replies Stopped!")

    @bot.message_handler(commands=["auto_delete", "autodelete"])
    def handle_auto_delete(message):
        if not admin_only(message): return
        chat_id = message.chat.id
        parts = message.text.strip().split(None, 1)
        arg = parts[1].strip() if len(parts) > 1 else ""
        if arg.lower() in ["off", ""]:
            state.auto_delete.pop(chat_id, None)
            save()
            bot.reply_to(message, "💀 Auto delete disabled!")
            return
        try:
            target_id = int(arg)
            state.auto_delete.setdefault(chat_id, set()).add(target_id)
            save()
            bot.reply_to(message, f"🎯 Auto delete ON for `{target_id}`", parse_mode="Markdown")
        except ValueError:
            pass

    @bot.message_handler(commands=["react"])
    def handle_react(message):
        if not admin_only(message): return
        parts = message.text.strip().split(None, 1)
        if len(parts) < 2: return
        state.auto_react[message.chat.id] = parts[1].strip()
        save()
        bot.reply_to(message, f"⚡ Auto react set to: {parts[1].strip()}")

    @bot.message_handler(commands=["stopreact"])
    def stop_react(message):
        if not admin_only(message): return
        state.auto_react.pop(message.chat.id, None)
        save()
        bot.reply_to(message, "🔥 Auto react disabled!")

    @bot.message_handler(commands=["status"])
    def show_status(message):
        if not admin_only(message): return
        chat_id = message.chat.id
        yn = lambda v: "ON ⚡" if v else "OFF ❌"
        bot.reply_to(message,
            f"👑 <b>[{label}] System Status</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Spam       : {yn(state.spam_flags.get(chat_id))}\n"
            f"Fast NC    : {yn(state.nc_flags.get(chat_id))}\n"
            f"Auto Reply : {yn(state.auto_reply.get(chat_id))}\n"
            f"Auto Photo : {yn(state.auto_photo.get(chat_id))}\n"
            f"Auto React : {yn(state.auto_react.get(chat_id))}\n"
            f"Subadmins  : {len(state.subadmins)}",
            parse_mode="HTML"
        )

    # Main Message Handler Loop
    @bot.message_handler(func=lambda m: True, content_types=["text","photo","sticker","video","audio","document","voice","animation"])
    def on_any_message(message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        # Auto Delete
        if user_id and chat_id in state.auto_delete and user_id in state.auto_delete[chat_id]:
            try: bot.delete_message(chat_id, message.message_id)
            except Exception: pass
            return

        # Don't trigger auto-replies on own bot or admin commands
        if message.text and message.text.startswith("/"):
            return

        # Auto React
        if chat_id in state.auto_react:
            try: bot.set_message_reaction(chat_id, message.message_id, [telebot.types.ReactionTypeEmoji(state.auto_react[chat_id])])
            except Exception: pass

        # Auto Text Reply
        if chat_id in state.auto_reply:
            try: bot.reply_to(message, state.auto_reply[chat_id])
            except Exception: pass

        # Auto Photo Reply
        if chat_id in state.auto_photo:
            try: bot.send_photo(chat_id, state.auto_photo[chat_id], reply_to_message_id=message.message_id)
            except Exception: pass

        # Auto Sticker Reply
        if chat_id in state.auto_sticker:
            try: bot.send_sticker(chat_id, state.auto_sticker[chat_id], reply_to_message_id=message.message_id)
            except Exception: pass

def start_bot(token: str, label: str):
    logger.info(f"Starting [{label}] ...")
    bot = telebot.TeleBot(token, parse_mode=None)
    state = BotState()
    _all_states[label] = state
    register_handlers(bot, state, label)
    try:
        me = bot.get_me()
        logger.info(f"[{label}] Connected as @{me.username}")
    except Exception as e:
        logger.error(f"[{label}] Failed: {e}")
        return
    resume_state(label, state, bot)
    while True:
        try:
            bot.infinity_polling(timeout=15, long_polling_timeout=10)
        except Exception as e:
            logger.warning(f"[{label}] Error: {e} — Retrying in 5s")
            time.sleep(5)

if __name__ == "__main__":
    if not OWNER_IDS or not BOT_TOKENS:
        sys.exit(1)

    # 1. Start Flask Keep-Alive Server
    keep_alive()

    print(f"🔥 VIVEK ENGINE ONLINE | Owners: {len(OWNER_IDS)} | Bots Active: {len(BOT_TOKENS)}")

    # 2. Start Bot Threads
    for idx, token in enumerate(BOT_TOKENS, start=1):
        t = threading.Thread(target=start_bot, args=(token, f"Bot{idx}"), daemon=True)
        t.start()
        time.sleep(0.5)

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nEngine Shutdown 👋")
