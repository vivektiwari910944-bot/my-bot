import os
import sys
import time
import random
import logging
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VivekEngine")

START_TIME = time.time()
RENDER_WEB_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://my-bot-zlmx.onrender.com/")

# Global dict to manage active hunt threads and active GCPFP loops per chat
ACTIVE_HUNTS = {}
ACTIVE_GCPFP = {}
ACTIVE_SPAM = {}

# ==========================================
# 🔑 ENVIRONMENT CONFIGURATION & TOKENS
# ==========================================
BOT_TOKENS = []
BOT_INSTANCES = []  # Holds telebot instances for all loaded bots
i = 1
while True:
    tok = os.environ.get(f"BOT_TOKEN_{i}")
    if not tok:
        break
    BOT_TOKENS.append(tok.strip())
    i += 1

if not BOT_TOKENS and os.environ.get("BOT_TOKEN"):
    BOT_TOKENS.append(os.environ.get("BOT_TOKEN").strip())

# Telebot instances create karein
for token in BOT_TOKENS:
    try:
        BOT_INSTANCES.append(telebot.TeleBot(token, parse_mode="HTML"))
    except Exception as e:
        logger.error(f"Failed to initialize bot with token: {token[:10]}... Error: {e}")

OWNER_IDS_RAW = os.environ.get("OWNER_IDS", "")
OWNER_IDS = set(int(x.strip()) for x in OWNER_IDS_RAW.split(",") if x.strip().isdigit())

# Dynamic Admins storage
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
    
    # Check 1: Vivek YA Username me se koi ek match ho
    contains_name = any(name in text_lower for name in TARGET_NAMES)
    
    # Check 2: Abusive word ho
    contains_abuse = any(word in text_lower for word in ABUSIVE_KEYWORDS)
    
    return contains_name and contains_abuse

# ==========================================
# 🥸 AUTO ROAST RESPONSES
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
    "Tere paas gaali ke alawa koi valid point nahi hai kyu ki tu zero hai! 0️⃣",
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
# ⚙️ QUEUE & SEQUENTIAL EXECUTION ENGINES
# ==========================================

# 1. ONE-BY-ONE SPAM QUEUE ENGINE (Flood Protection)
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
            time.sleep(delay)  # Controlled safe interval to avoid Flood limit
        except Exception as e:
            logger.error(f"Spam sending error: {e}")
            time.sleep(3)
    
    ACTIVE_SPAM[chat_id] = False

# 2. AUTOREPLY & ROTATION QUEUE ENGINE
def run_sequential_gcpfp(chat_id, name_list):
    ACTIVE_GCPFP[chat_id] = True
    bot = BOT_INSTANCES[0] if BOT_INSTANCES else None
    if not bot:
        return

    while ACTIVE_GCPFP.get(chat_id):
        for name in name_list:
            if not ACTIVE_GCPFP.get(chat_id):
                break
            try:
                # Name change or autoreply update line
                bot.send_message(chat_id, f"🔄 Updating Profile/Name to: <b>{name}</b>")
                time.sleep(3)  # 3-second gap between name changes/autoreplies
            except Exception as e:
                logger.error(f"GCPFP update error: {e}")
                time.sleep(5)

# ==========================================
# 🤖 BOT HANDLERS & EVENT LISTENERS
# ==========================================
if BOT_INSTANCES:
    leader_bot = BOT_INSTANCES[0]

    # Command: /spam <count> <message>
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

    # Command: /stopspam
    @leader_bot.message_handler(commands=['stopspam'])
    def stop_spam(message):
        ACTIVE_SPAM[message.chat.id] = False
        leader_bot.reply_to(message, "🛑 Spam process stopped.")

    # Main Message Handler (Auto-Roast Guard on Abuse + Vivek)
    @leader_bot.message_handler(func=lambda msg: True)
    def handle_all_messages(message):
        # Auto Roast Check
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
    # Start Flask Web Server Thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    logger.info("🔥 VIVEK ENGINE STARTED SUCCESSFULLY")
    
    # Start Main Leader Bot Polling Loop
    if BOT_INSTANCES:
        BOT_INSTANCES[0].infinity_polling(skip_pending=True)
    else:
        logger.error("No valid BOT_TOKEN provided in Environment variables.")
        while True:
            time.sleep(3600)
