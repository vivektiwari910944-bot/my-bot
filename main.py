import os
import sys
import time
import random
import logging
import threading
import requests
import telebot
from datetime import datetime
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VivekEngine")

START_TIME = time.time()
RENDER_WEB_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://my-bot-zlmx.onrender.com/")

# Global dicts to manage background active tasks per chat
ACTIVE_HUNTS = {}
ACTIVE_GCPFP = {}
ACTIVE_SPAM = {}
ACTIVE_NC = {}
ACTIVE_AUTOREPLY = {}
ACTIVE_AUTODELETE = {}
ACTIVE_AUTOREACT = {}
ACTIVE_AUTOSTICKER = {}
ACTIVE_AUTOPHOTO = {}

# ==========================================
# 🔑 ENVIRONMENT CONFIGURATION & TOKENS
# ==========================================
BOT_TOKENS = []
BOT_INSTANCES = []
i = 1
while True:
    tok = os.environ.get(f"BOT_TOKEN_{i}")
    if not tok:
        break
    BOT_TOKENS.append(tok.strip())
    i += 1

if not BOT_TOKENS and os.environ.get("BOT_TOKEN"):
    BOT_TOKENS.append(os.environ.get("BOT_TOKEN").strip())

for token in BOT_TOKENS:
    try:
        BOT_INSTANCES.append(telebot.TeleBot(token, parse_mode="HTML"))
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")

OWNER_IDS_RAW = os.environ.get("OWNER_IDS", "")
OWNER_IDS = set(int(x.strip()) for x in OWNER_IDS_RAW.split(",") if x.strip().isdigit())
DYNAMIC_ADMINS = set()

def is_admin(user_id):
    if not OWNER_IDS:
        return True
    return (user_id in OWNER_IDS) or (user_id in DYNAMIC_ADMINS)

def get_uptime():
    delta = int(time.time() - START_TIME)
    hours, remainder = divmod(delta, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m"

def get_ist_time():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%d %b %Y, %I:%M:%S %p")

# ==========================================
# 🎯 TRIGGER CHECK KEYWORDS & MATRIX
# ==========================================
ABUSIVE_KEYWORDS = [
    "bhenchod", "bc", "mc", "madarchod", "chutiya", "lodu", "gand", "gaand", 
    "bhosda", "bhosdi", "laude", "lund", "randike", "chup", "ma", "kutta",
    "rndyke", "randi", "jhantu", "chod", "terigand", "bhenklode"
]

TARGET_NAMES = ["vivek", "@danggvivek", "Vivek"]

def should_trigger_roast(text):
    if not text:
        return False
    text_lower = text.lower()
    contains_name = any(name in text_lower for name in TARGET_NAMES)
    contains_abuse = any(word in text_lower for word in ABUSIVE_KEYWORDS)
    return contains_name and contains_abuse

# ==========================================
# 🥸 AUTO ROAST RESPONSES (FULL 64 LINES)
# ==========================================
AUTO_ROAST_RESPONSES = [
    "Abe 👂 sasta 2-rupee troll, Vivek sir ka naam lene se pehle muh saaf kar le! 💩",
    "Tu jitna marzi bhok le, Vivek sir tere baap hain aur hamesha rahenge! 🔥👑",
    "Jitna dimaag gaali dene me lagaya hai, utna padhai me lagata toh aaj majdoori na kar raha hota! 💀",
    "Aukat me reh ke baat kar, tera pura khandaan khareedne ka dum rakhte hain Vivek sir! 💸💥",
    "Beta, tere jaise 100 daily Vivek sir ke samne aake ghutne tekte hain. Nikal yahan se! ⚔️",
    "Pehle apna dhang se recharge karwa le, fir Vivek sir ko gaali dene me dimag lagana! 📱😂",
    "Tera ye faltu attitude Vivek sir ke samne 2 second me dher ho jayega, samjha? 🔱",
    "Google pe search mar le 'Who is Boss' — Vivek sir ka photo aayega! 🔥",
    "Bolne de bolne de... dukh hua hai bechare ko, Vivek sir ne zindgi jo tabah kar di hai iski! 😭",
    "Abe chootey, Vivek sir tera baap hain, unhe gaali deke apni aukaat mat dikha! 💣",
    "Jiski shakal hi meme jaisi ho, woh Vivek sir pe comment kar raha hai? 😂",
    "Beta, shant ho ja! Warna bot army mil ke tujhe aisa roast karegi ki account delete kar dega! 🦅",
    "Tere bhokne se Vivek sir ka 1% bhi nuksan nahi hone wala. Chup kar ab! 🎯",
    "Jao beta pehle apna diapers change karo, fir Vivek sir se panga lena! 👶💩",
    "Gali dene se aukaat badi nahi hoti, dimaag ka kachra bahar aata hai. Vivek sir ke aage tu zero hai! 🤡",
    "Tera wifi pack Vivek sir ke ek minute ke kharche se sasta hai, aukaat me reh! 📶💸",
    "Itna hi dum hai toh samne aake bol, Telegram ke piche se kutte bhi bhokte hain! 🐕💀",
    "Vivek sir ko gaali deke soch raha hai tu cool lag raha hai? Bhai tu bas ek fool lag raha hai! 🤡🔥",
    "Jitna bada tera ego hai, utna bada toh Vivek sir ka footwear ka size hai! 👟💥",
    "Tere mummy-papa ko pata hai tu internet pe Vivek sir ko gaali deke apna time waste kar raha hai? 😭",
    "Abe keyboard warrior, thoda paani pee le, Vivek sir ke naam se hi teri jal ke raakh ho gayi hai! 🧯🔥",
    "Tere opinions ki utni hi value hai jitni YouTube pe skip ad button ki hoti hai! 🚫😂",
    "Vivek sir ki personality ke aage tera poora khandaan fade ho jaye, samjha kiddo? ✨👑",
    "Tu gaali deta reh, Vivek sir apna kaam karke aage nikal bhi gaye! 🚀🎯",
    "Tu wo aadmi hai jisko roast karne ke liye dimaag nahi, bas teri shakal hi kaafi hai! 🗿",
    "Abe 50 paise ke recharge waale, Vivek sir ka naam izzat se liya kar! ⚡",
    "Tu jitna marzi try kar le, Vivek sir ka level touch karne me tere 7 janam kam pad jayenge! 🧬💣",
    "Sun beta, Sher ke samne kutte bhokte ache nahi lagte, nikal yahan se! 🐺💥",
    "Tera dimaag utna hi khaali hai jitna bina pack ka SIM card! 📲🤡",
    "Vivek sir ke saamne teri aukat utni hi hai jitni biryani me elaichi ki hoti hai! 🍲😂",
    "Gali deke apna khandaan mat dikha, sabko pata hai tu kitna bada nalla hai! 🐍",
    "Koshish achi thi, par Vivek sir ko phark tak nahi padta tere jaise trolls se! 🤷‍♂️🔥",
    "Tu bas chat me bhok sakta hai, asal me toh tu Vivek sir ka shadow bhi nahi pakad sakta! 👤🎯",
    "Lagta hai aaj tera dimaag wala recharge khatam ho gaya hai! 🧠🔋",
    "Vivek sir ki ek smile me tera poora roast system destroy ho jayega! 😎💥",
    "Tere words me utna hi weight hai jitni hawam me dhool hoti hai! 💨",
    "Beta Google par search kar: 'How to talk to Legend Vivek Sir', thodi tameez seekh lega! 🔍📖",
    "Abe battery low wale phone, quiet reh varna Bot Army abhi format kar degi tujhe! 🤖💀",
    "Jitna attitude dikha raha hai, utna agar dimaag hota toh aaj yahan gali nahi de raha hota! 📉",
    "Vivek sir ke samne tu bas ek background noise hai, mute pe reh! 🔕😂",
    "Tere jaise 36 aate hain aur Vivek sir ke aage ghutne tek ke jaate hain! 🙇‍♂️⚡",
    "Bhokta reh bhai, tere bhokne se Vivek sir ka Brand aur bada hota hai! 🏆👑",
    "Gali deke tu badmashi nahi, apni helplessness dikha raha hai! 🩹😭",
    "Vivek sir ka naam lene se pehle 100 baar socha kar, varna aisi bezzati hogi ki kahi mu dikhane layak nahi rahega! 🚫🎭",
    "Tu wo machhar hai jise Vivek sir ek chutki me uda dein! 💥",
    "Tere gaali dene se Vivek sir ka nuksan nahi, tere hi sanskar dikh rahe hain! 🤌",
    "Itna frustrated kyu hai bhai? Vivek sir ne teri koi setting pata li kya? 🤣❤️",
    "Duniya aage nikal gayi aur tu abhi bhi Vivek sir ke naam pe ro raha hai! 😭🚜",
    "Abe saste joker, tera ye circus yahan nahi chalega! 🎪🤡",
    "Vivek sir ki entry pe tere jaise 100 log side me hoke rasta dete hain! 🚶‍♂️👑",
    "Gali deke soch raha hai tu winner hai? Abe tu toh pehle hi round me out hai! 🛑🎮",
    "Tere jaiso ke liye Vivek sir ki bot army ka 1% power hi kafi hai! ⚡🤖",
    "Bhokne wale kutte kabhi kaat te nahi, aur tu toh bas ek chota sa puppy hai! 🐶",
    "Abe cartoon, tere bolne se Vivek sir ki brand value kam nahi hogi! 💎",
    "Tu Vivek sir se jealous hai, baaki sabko pata hai! 😏🔥",
    "Jaake thanda paani pee le, Vivek sir ka success dekh ke teri jal rahi hai! 🧊💥",
    "Tere paas gaali deke alawa koi valid point nahi hai kyu ki tu zero hai! 0️⃣",
    "Vivek sir ke aage tu ek chota sa dot hai, zyaada mat phadphada! 📍",
    "Terko roast karne me bot ka 0.001 second laga, teri itni hi value hai! ⏱️⚡",
    "Gali likhna easy hai, Vivek sir jaisa ban ke dikhana impossible hai! 🏆",
    "Tera roast sunke toh khud gaali bhi sharma gayi ki kis nalle ke muh se nikli! 🤦‍♂️",
    "Chup chap kone me baithe reh, varna Bot Army spam karke tera phone hang kar degi! 📲💥",
    "Vivek sir ke level pe aane ke liye pehle apna level 0 se 1 toh kar le! 🎮💀",
    "Beta tu abhi bacha hai, Vivek sir ke maamle me taang mat adaa! 🚸🔥"
]

MIRZAPUR_HUNT_ROASTS = [
    "{target} Abe 👂 bhosdiwale, aukaat mein reh ke baat kar warna aisi jagah goli maarenge ki bawaseer ho jayega! 💣",
    "{target} Tumhare baap ka chota sa dhandha nahi hai jo jab man kiya chale aaye, shant baith warna gaand chod denge! 🔥",
    "{target} jada gand na fulao yahi ma chod denge tumhari ",
    "{target} Bhosdi ke, zyada bologe toh chhati me itna hole karenge ki confuse ho jaoge ki saas kahan se lein! 🎯",
    "{target} tumayi maiya baje chaiya chaiya bahubali hai ham yhake smjhe bhosdike⚡",
    "{target} Tumko kya laga tum humko hara loge? Abe jhaat ke baal, ek second me gaand phad denge! 💥",
    "{target} Abe madarchod, thoda sharam bachi hai ya wo bhi Telegram pe bech khaye ho? 🤮",
    "{target} Bhosdike, tum humare samne 2 second nahi tik paoge, tumhari gaand ka size badha denge! 🪵",
    "{target} Abe lund ke topae, aukaat me reh ke reply kar warna aisa bigger Laad maarunga ki 7 peedhi tak nishani rahegi! ⚔️",
    "{target} Beta {target}, O bhosdike wetter 😂"
]

# ==========================================
# 🌐 FLASK WEB DASHBOARD
# ==========================================
web_app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 VIVEK MULTI-BOT ENGINE V2.0 🔥</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #080711;
            color: #fff;
            font-family: 'Poppins', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 850px;
            background: rgba(18, 16, 38, 0.85);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 0, 127, 0.4);
            border-radius: 20px;
            padding: 35px;
            box-shadow: 0 0 40px rgba(255, 0, 127, 0.25);
        }
        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.2rem;
            text-align: center;
            background: linear-gradient(45deg, #ff007f, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
            letter-spacing: 2px;
        }
        .subtitle {
            text-align: center;
            color: #00f2fe;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 25px;
            text-shadow: 0 0 8px rgba(0,242,254,0.6);
        }
        .clock-box {
            background: linear-gradient(135deg, rgba(255,0,127,0.1), rgba(0,242,254,0.1));
            border: 1px solid rgba(0, 242, 254, 0.4);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            margin-bottom: 25px;
        }
        .clock-title { font-size: 0.8rem; color: #aaa; text-transform: uppercase; }
        .clock-time { font-family: 'Orbitron', sans-serif; font-size: 1.8rem; color: #ff007f; text-shadow: 0 0 10px #ff007f; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        .card {
            background: rgba(255, 255, 255, 0.03);
            border-left: 4px solid #00f2fe;
            border-radius: 10px;
            padding: 18px;
        }
        .card h3 { font-size: 0.85rem; color: #888; text-transform: uppercase; }
        .card p { font-size: 1.2rem; font-weight: 600; color: #fff; }
        .bot-list {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .bot-list h2 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            color: #00f2fe;
            margin-bottom: 15px;
        }
        .bot-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .bot-item:last-child { border-bottom: none; }
        .status-badge {
            background: #00ff88;
            color: #000;
            font-size: 0.75rem;
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 20px;
            box-shadow: 0 0 10px #00ff88;
        }
        .footer { text-align: center; margin-top: 25px; font-size: 0.85rem; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 VIVEK MULTI-BOT ENGINE V2.0 🔥</h1>
        <div class="subtitle">⚡ POWERED BY VIVEK • RUNNING CONTINUOUSLY ⚡</div>

        <div class="clock-box">
            <div class="clock-title">🇮🇳 Current India Time (IST)</div>
            <div class="clock-time" id="ist-clock">Loading...</div>
        </div>

        <div class="grid">
            <div class="card" style="border-color: #ff007f;">
                <h3>System Status</h3>
                <p>🟢 ALL SYSTEMS ACTIVE</p>
            </div>
            <div class="card" style="border-color: #00f2fe;">
                <h3>Engine Uptime</h3>
                <p>{{ uptime }}</p>
            </div>
            <div class="card" style="border-color: #00ff88;">
                <h3>Total Active Bots</h3>
                <p>{{ total_bots }} Connected</p>
            </div>
        </div>

        <div class="bot-list">
            <h2>🤖 ACTIVE BOTS NETWORK</h2>
            {% for bot in bots %}
            <div class="bot-item">
                <div>
                    <strong>{{ bot.name }}</strong> <span style="color:#888;">({{ bot.role }})</span>
                </div>
                <span class="status-badge">ONLINE ⚡</span>
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            © Vivek Multi-Bot System V2.0 • Hosted & Managed via Render Cloud
        </div>
    </div>

    <script>
        function updateISTClock() {
            const options = {
                timeZone: 'Asia/Kolkata',
                hour12: true,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            };
            const now = new Date();
            document.getElementById('ist-clock').innerText = now.toLocaleString('en-IN', options);
        }
        setInterval(updateISTClock, 1000);
        updateISTClock();
    </script>
</body>
</html>
"""

@web_app.route('/')
def home():
    bot_data = []
    total = len(BOT_TOKENS) if BOT_TOKENS else 1
    for idx in range(1, max(total + 1, 2)):
        role = "Leader Bot" if idx == 1 else f"Slave Bot 0{idx-1}"
        bot_data.append({"name": f"Vivek Bot Instance #{idx}", "role": role})
    
    return render_template_string(
        HTML_TEMPLATE,
        uptime=get_uptime(),
        total_bots=total,
        bots=bot_data
    )

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# ==========================================
# ⚙️ BACKGROUND WORKER ENGINE LOOPS
# ==========================================

def run_sequential_spam(chat_id, messages, delay=1.5):
    ACTIVE_SPAM[chat_id] = True
    bot = BOT_INSTANCES[0] if BOT_INSTANCES else None
    if not bot:
        return
    for msg in messages:
        if not ACTIVE_SPAM.get(chat_id):
            break
        try:
            bot.send_message(chat_id, msg)
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Spam sending error: {e}")
            time.sleep(3)
    ACTIVE_SPAM[chat_id] = False

def run_target_hunt(chat_id, target_username):
    ACTIVE_HUNTS[chat_id] = True
    bot = BOT_INSTANCES[0] if BOT_INSTANCES else None
    if not bot:
        return
    while ACTIVE_HUNTS.get(chat_id):
        roast_template = random.choice(MIRZAPUR_HUNT_ROASTS)
        formatted_msg = roast_template.format(target=target_username)
        try:
            bot.send_message(chat_id, formatted_msg)
            time.sleep(2.0)
        except Exception as e:
            logger.error(f"Hunt sending error: {e}")
            time.sleep(5)

def run_sequential_nc(chat_id, names_list):
    ACTIVE_NC[chat_id] = True
    bot = BOT_INSTANCES[0] if BOT_INSTANCES else None
    if not bot:
        return
    while ACTIVE_NC.get(chat_id):
        for name in names_list:
            if not ACTIVE_NC.get(chat_id):
                break
            try:
                bot.send_message(chat_id, f"🔄 Name Change Alert: <b>{name}</b>")
                time.sleep(3.0)
            except Exception as e:
                logger.error(f"NC error: {e}")
                time.sleep(5)

# ==========================================
# 📱 TELEGRAM DASHBOARD UI BUILDER
# ==========================================
def build_custom_dashboard():
    text = (
        "<b>🔥 VIVEK MULTI-BOT ENGINE V2.0 🔥</b>\n\n"
        f"<b>⏰ Current IST Time:</b> <code>{get_ist_time()}</code>\n"
        f"<b>⏳ Engine Uptime:</b> <code>{get_uptime()}</code>\n"
        f"<b>🤖 Active Bots:</b> <code>{len(BOT_TOKENS)} Connected</code>\n"
        "<b>🛡️ Auto Roast Guard:</b> <code>ACTIVE 🟢</code>\n\n"
        "<i>Select an option from below to manage engine features:</i>"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("⚙️ BOT MANAGER", callback_data="help_admin"),
        InlineKeyboardButton("🛡️ ROAST GUARD", callback_data="help_roast")
    )
    markup.row(
        InlineKeyboardButton("💥 SPAM & NC", callback_data="help_spam_nc"),
        InlineKeyboardButton("🎯 HUNT & AUTO REPLY", callback_data="help_hunt_reply")
    )
    markup.row(
        InlineKeyboardButton("🖼️ GC PFP & MEDIA", callback_data="help_media"),
        InlineKeyboardButton("⚡ AUTO TOOLS", callback_data="help_autotools")
    )
    markup.row(
        InlineKeyboardButton("📊 SYSTEM STATS", callback_data="help_status")
    )
    markup.row(
        InlineKeyboardButton("🌐 CHECK VIVEK BOTS ON GOOGLE", url=RENDER_WEB_URL)
    )
    return text, markup

# ==========================================
# 🤖 BOT HANDLERS & EVENT LISTENERS
# ==========================================
if BOT_INSTANCES:
    leader_bot = BOT_INSTANCES[0]

    try:
        leader_bot.set_my_commands([
            telebot.types.BotCommand("start", "🔥 Open Vivek Engine Dashboard"),
            telebot.types.BotCommand("menu", "📌 View Interactive Menu"),
            telebot.types.BotCommand("spam", "⚡ Start Sequential Spam"),
            telebot.types.BotCommand("nc", "⚡ Start Name Change Spam"),
            telebot.types.BotCommand("hunt", "💥 Start Target Hunt"),
            telebot.types.BotCommand("gcpfp", "🖼️ Change Group Profile"),
            telebot.types.BotCommand("stopall", "🛑 Stop All Active Tasks")
        ])
    except Exception as e:
        logger.error(f"Failed to set Telegram commands: {e}")

    @leader_bot.message_handler(commands=['start', 'menu'])
    def send_welcome_dashboard(message):
        text, markup = build_custom_dashboard()
        leader_bot.reply_to(message, text, reply_markup=markup)

    @leader_bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        data = call.data
        if data == "main_menu":
            text, markup = build_custom_dashboard()
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        
        elif data == "help_admin":
            text = "<b>⚙️ BOT MANAGER MENU</b>\n\n• Multi-Bot Cluster Manager is Running Active.\n• All Sub-instances connected."
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            
        elif data == "help_roast":
            text = f"<b>🛡️ ROAST GUARD SYSTEM</b>\n\nTrigger Names: <code>{', '.join(TARGET_NAMES)}</code>\nStatus: 🟢 Auto Roast is Enabled."
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

        elif data == "help_spam_nc":
            text = (
                "<b>💥 SPAM & NC CONTROLS</b>\n\n"
                "• <code>/spam &lt;count&gt; &lt;text&gt;</code> - Fast Text Spam\n"
                "• <code>/nc &lt;name1, name2&gt;</code> - Name Change Rotation Spam\n"
                "• <code>/stopspam</code> - Stop Current Active Spam"
            )
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

        elif data == "help_hunt_reply":
            text = (
                "<b>🎯 HUNT & AUTO REPLY CONTROLS</b>\n\n"
                "• <code>/hunt &lt;username/tag&gt;</code> - Start Target Hunt Attack\n"
                "• <code>/autoreply on/off</code> - Toggle Smart Auto Reply\n"
                "• <code>/stophunt</code> - Stop Active Target Attack"
            )
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

        elif data == "help_media":
            text = (
                "<b>🖼️ GC PFP & MEDIA CONTROLS</b>\n\n"
                "• <code>/gcpfp</code> - Group Profile Picture Changer\n"
                "• <code>/autophoto</code> - Send Dynamic Photo Responses\n"
                "• <code>/autosticker</code> - Auto Sticker Trigger Engine"
            )
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

        elif data == "help_autotools":
            text = (
                "<b>⚡ AUTO TOOLS CONTROLS</b>\n\n"
                "• <code>/autodelete on/off</code> - Auto Message Cleaner\n"
                "• <code>/autoreact on/off</code> - Auto Emoji Reaction Engine"
            )
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

        elif data == "help_status":
            text = (
                "<b>📊 SYSTEM STATS</b>\n\n"
                f"• <b>Current IST:</b> <code>{get_ist_time()}</code>\n"
                f"• <b>Uptime:</b> <code>{get_uptime()}</code>\n"
                f"• <b>Total Bots:</b> <code>{len(BOT_TOKENS)} Connected</code>\n"
                "• <b>Host Environment:</b> Render Cloud Engine"
            )
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
            leader_bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

        leader_bot.answer_callback_query(call.id)

    # Command Handlers Implementation
    @leader_bot.message_handler(commands=['spam'])
    def handle_spam(message):
        if not is_admin(message.from_user.id):
            return leader_bot.reply_to(message, "❌ Admin access required.")
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            return leader_bot.reply_to(message, "⚠️ Usage: `/spam <count> <message>`")
        count = int(args[1]) if args[1].isdigit() else 5
        text_to_spam = args[2]
        msg_list = [f"{text_to_spam} [{idx+1}]" for idx in range(count)]
        leader_bot.reply_to(message, f"⚡ Starting One-by-One Spam queue ({count} messages)...")
        threading.Thread(target=run_sequential_spam, args=(message.chat.id, msg_list), daemon=True).start()

    @leader_bot.message_handler(commands=['stopspam'])
    def stop_spam(message):
        ACTIVE_SPAM[message.chat.id] = False
        leader_bot.reply_to(message, "🛑 Spam process stopped.")

    @leader_bot.message_handler(commands=['hunt'])
    def handle_hunt(message):
        if not is_admin(message.from_user.id):
            return leader_bot.reply_to(message, "❌ Admin access required.")
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return leader_bot.reply_to(message, "⚠️ Usage: `/hunt <@username>`")
        target = args[1]
        leader_bot.reply_to(message, f"🎯 Mirzapur Target Hunt started against {target}!")
        threading.Thread(target=run_target_hunt, args=(message.chat.id, target), daemon=True).start()

    @leader_bot.message_handler(commands=['stophunt'])
    def stop_hunt(message):
        ACTIVE_HUNTS[message.chat.id] = False
        leader_bot.reply_to(message, "🛑 Target hunt process stopped.")

    @leader_bot.message_handler(commands=['nc'])
    def handle_nc(message):
        if not is_admin(message.from_user.id):
            return leader_bot.reply_to(message, "❌ Admin access required.")
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return leader_bot.reply_to(message, "⚠️ Usage: `/nc Name1, Name2`")
        names = [n.strip() for n in args[1].split(",") if n.strip()]
        leader_bot.reply_to(message, "⚡ Name Change rotation started!")
        threading.Thread(target=run_sequential_nc, args=(message.chat.id, names), daemon=True).start()

    @leader_bot.message_handler(commands=['stopnc'])
    def stop_nc(message):
        ACTIVE_NC[message.chat.id] = False
        leader_bot.reply_to(message, "🛑 Name Change process stopped.")

    @leader_bot.message_handler(commands=['gcpfp'])
    def handle_gcpfp(message):
        if not is_admin(message.from_user.id):
            return leader_bot.reply_to(message, "❌ Admin access required.")
        if message.reply_to_message and message.reply_to_message.photo:
            try:
                file_info = leader_bot.get_file(message.reply_to_message.photo[-1].file_id)
                downloaded_file = leader_bot.download_file(file_info.file_path)
                leader_bot.set_chat_photo(message.chat.id, downloaded_file)
                leader_bot.reply_to(message, "🖼️ Group Profile Picture updated successfully!")
            except Exception as e:
                leader_bot.reply_to(message, f"❌ Failed to set GC PFP: {e}")
        else:
            leader_bot.reply_to(message, "⚠️ Please reply to an image/photo with `/gcpfp`.")

    @leader_bot.message_handler(commands=['autoreply'])
    def toggle_autoreply(message):
        status = message.text.split(maxsplit=1)
        if len(status) > 1 and status[1].lower() == 'off':
            ACTIVE_AUTOREPLY[message.chat.id] = False
            leader_bot.reply_to(message, "🔴 Auto Reply disabled for this chat.")
        else:
            ACTIVE_AUTOREPLY[message.chat.id] = True
            leader_bot.reply_to(message, "🟢 Auto Reply enabled for this chat.")

    @leader_bot.message_handler(commands=['autodelete'])
    def toggle_autodelete(message):
        status = message.text.split(maxsplit=1)
        if len(status) > 1 and status[1].lower() == 'off':
            ACTIVE_AUTODELETE[message.chat.id] = False
            leader_bot.reply_to(message, "🔴 Auto Delete disabled.")
        else:
            ACTIVE_AUTODELETE[message.chat.id] = True
            leader_bot.reply_to(message, "🟢 Auto Delete enabled.")

    @leader_bot.message_handler(commands=['autoreact'])
    def toggle_autoreact(message):
        status = message.text.split(maxsplit=1)
        if len(status) > 1 and status[1].lower() == 'off':
            ACTIVE_AUTOREACT[message.chat.id] = False
            leader_bot.reply_to(message, "🔴 Auto React disabled.")
        else:
            ACTIVE_AUTOREACT[message.chat.id] = True
            leader_bot.reply_to(message, "🟢 Auto React enabled.")

    @leader_bot.message_handler(commands=['autosticker'])
    def toggle_autosticker(message):
        status = message.text.split(maxsplit=1)
        if len(status) > 1 and status[1].lower() == 'off':
            ACTIVE_AUTOSTICKER[message.chat.id] = False
            leader_bot.reply_to(message, "🔴 Auto Sticker disabled.")
        else:
            ACTIVE_AUTOSTICKER[message.chat.id] = True
            leader_bot.reply_to(message, "🟢 Auto Sticker enabled.")

    @leader_bot.message_handler(commands=['autophoto'])
    def toggle_autophoto(message):
        status = message.text.split(maxsplit=1)
        if len(status) > 1 and status[1].lower() == 'off':
            ACTIVE_AUTOPHOTO[message.chat.id] = False
            leader_bot.reply_to(message, "🔴 Auto Photo disabled.")
        else:
            ACTIVE_AUTOPHOTO[message.chat.id] = True
            leader_bot.reply_to(message, "🟢 Auto Photo enabled.")

    @leader_bot.message_handler(commands=['stopall'])
    def stop_all_processes(message):
        cid = message.chat.id
        ACTIVE_SPAM[cid] = False
        ACTIVE_HUNTS[cid] = False
        ACTIVE_NC[cid] = False
        ACTIVE_GCPFP[cid] = False
        ACTIVE_AUTOREPLY[cid] = False
        ACTIVE_AUTODELETE[cid] = False
        ACTIVE_AUTOREACT[cid] = False
        ACTIVE_AUTOSTICKER[cid] = False
        ACTIVE_AUTOPHOTO[cid] = False
        leader_bot.reply_to(message, "🛑 All background tasks and engines stopped.")

    # Main Message Guard (Auto-Roast + Reaction Trigger)
    @leader_bot.message_handler(func=lambda msg: True)
    def handle_all_messages(message):
        if message.text and should_trigger_roast(message.text):
            roast_msg = random.choice(AUTO_ROAST_RESPONSES)
            try:
                leader_bot.reply_to(message, roast_msg)
            except Exception as e:
                logger.error(f"Failed to send Auto-Roast: {e}")

# ==========================================
# 🚀 MAIN APPLICATION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("🔥 VIVEK ENGINE STARTED SUCCESSFULLY")
    
    if BOT_INSTANCES:
        BOT_INSTANCES[0].infinity_polling(skip_pending=True)
    else:
        logger.error("No valid BOT_TOKEN provided in Environment variables.")
        while True:
            time.sleep(3600)
