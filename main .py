
import time
import requests
import json
import re
import os
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import sqlite3
import telebot
from telebot import types
import threading
import traceback
import random
import itertools

BASE = "http://139.99.63.204"
AJAX_PATH = "/ints/agent/res/data_smscdr.php"
LOGIN_PAGE_URL = BASE + "/ints/login"
LOGIN_POST_URL = BASE + "/ints/signin"
# ======================
# 🖥️ إعداد لوحات (2 لوحة)
# ======================
# 1. الإعدادات الجديدة (تأكد منها)
# ======================
# 🖥️ إعداد اللوحة بنظام الـ API
# ======================

DASHBOARD_CONFIGS = [
    {
        "name": "Ziad Panel",
        "api_url": "http://147.135.212.197/crapi/st/viewstats",
        "token": "RFJVRkhBWRENDPEBDBXOWBDWgddkebPIR2U1WKXWOEhg==",
        "type": "old_list",
        "records": 10,
        "session": requests.Session(), # ضيف السطر ده
        "is_logged_in": True           # وضيف السطر ده
    },
    {
        "name": "Ziad Panel",
        "api_url": "http://51.77.216.195/crapi/dgroup/viewstats",
        "token": "QlJSRTRSQmJ_g2F1houCR19Rj1Z2aIpafG2QiUZUlkdYY3dbapV4",
        "type": "new_json",
        "records": 10,
        "session": requests.Session(), # ضيف السطر ده هنا كمان
        "is_logged_in": True           # وضيف السطر ده هنا كمان
    }
]


# ======================
# 🚀 تهيئة الـ API والـ Headers
# ======================
COMMON_HEADERS = {
    "User-Agent": "Albrans-API-Monitor/2.0",
    "Accept": "application/json"
}

for dash in DASHBOARD_CONFIGS:
    dash["session"].headers.update(COMMON_HEADERS)
    # ملاحظة: تم إلغاء تجميع الروابط القديمة لأننا نستخدم api_url مباشرة
    dash["login_page_url"] = ""
    dash["login_post_url"] = ""
    dash["ajax_url"] = dash["api_url"] # جعل الـ ajax_url يشير للـ API
    print(f"[{dash['name']}] 🚀 نظام الـ API جاهز للمراقبة...")

# ======================
# ⚙️ إعدادات البوت والتحكم
# ======================
BOT_TOKEN = "8217309974:AAFoChl2Ot-oGvgNZsdQkcbZrDN0P51OGqo"
CHAT_IDS = ["-1003047942419"]
ADMIN_IDS = [7966354929, 7645594609, 8231420847, 7946718662, 8278640283, 1042225523]

REFRESH_INTERVAL = 5
TIMEOUT = 5  # الـ API سريع مش محتاج 100 ثانية
MAX_RETRIES = 5
RETRY_DELAY = 5

# الفهارس بناءً على القائمة اللي السيرفر بيبعتها [Service, Num, Msg, Date]
IDX_SERVICE = 0  # الخدمة
IDX_NUMBER = 1   # الرقم
IDX_SMS = 2      # الرسالة
IDX_DATE = 3     # التاريخ

DB_PATH = "bot_database.db"
SENT_MESSAGES_FILE = "sent_messages.json"
BOT_ACTIVE = True




if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN must be set in Secrets (Environment Variables)")
if not CHAT_IDS:
    raise SystemExit("❌ CHAT_IDS must be configured")


COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸", "US"),
    "7": ("Russia", "🇷🇺", "RU"),
    "20": ("Egypt", "🇪🇬", "EG"),
    "27": ("South Africa", "🇿🇦", "ZA"),
    "30": ("Greece", "🇬🇷", "GR"),
    "31": ("Netherlands", "🇳🇱", "NL"),
    "32": ("Belgium", "🇧🇪", "BE"),
    "33": ("France", "🇫🇷", "FR"),
    "34": ("Spain", "🇪🇸", "ES"),
    "36": ("Hungary", "🇭🇺", "HU"),
    "39": ("Italy", "🇮🇹", "IT"),
    "40": ("Romania", "🇷🇴", "RO"),
    "41": ("Switzerland", "🇨🇭", "CH"),
    "43": ("Austria", "🇦🇹", "AT"),
    "44": ("United Kingdom", "🇬🇧", "UK"),
    "45": ("Denmark", "🇩🇰", "DK"),
    "46": ("Sweden", "🇸🇪", "SE"),
    "47": ("Norway", "🇳🇴", "NO"),
    "48": ("Poland", "🇵🇱", "PL"),
    "49": ("Germany", "🇩🇪", "DE"),

    "51": ("Peru", "🇵🇪", "PE"),
    "52": ("Mexico", "🇲🇽", "MX"),
    "53": ("Cuba", "🇨🇺", "CU"),
    "54": ("Argentina", "🇦🇷", "AR"),
    "55": ("Brazil", "🇧🇷", "BR"),
    "56": ("Chile", "🇨🇱", "CL"),
    "57": ("Colombia", "🇨🇴", "CO"),
    "58": ("Venezuela", "🇻🇪", "VE"),

    "60": ("Malaysia", "🇲🇾", "MY"),
    "61": ("Australia", "🇦🇺", "AU"),
    "62": ("Indonesia", "🇮🇩", "ID"),
    "63": ("Philippines", "🇵🇭", "PH"),
    "64": ("New Zealand", "🇳🇿", "NZ"),
    "65": ("Singapore", "🇸🇬", "SG"),
    "66": ("Thailand", "🇹🇭", "TH"),

    "81": ("Japan", "🇯🇵", "JP"),
    "82": ("South Korea", "🇰🇷", "KR"),
    "84": ("Vietnam", "🇻🇳", "VN"),
    "86": ("China", "🇨🇳", "CN"),

    "90": ("Turkey", "🇹🇷", "TR"),
    "91": ("India", "🇮🇳", "IN"),
    "92": ("Pakistan", "🇵🇰", "PK"),
    "93": ("Afghanistan", "🇦🇫", "AF"),
    "94": ("Sri Lanka", "🇱🇰", "LK"),
    "95": ("Myanmar", "🇲🇲", "MM"),
    "98": ("Iran", "🇮🇷", "IR"),

    "211": ("South Sudan", "🇸🇸", "SS"),
    "212": ("Morocco", "🇲🇦", "MA"),
    "213": ("Algeria", "🇩🇿", "DZ"),
    "216": ("Tunisia", "🇹🇳", "TN"),
    "218": ("Libya", "🇱🇾", "LY"),

    "220": ("Gambia", "🇬🇲", "GM"),
    "221": ("Senegal", "🇸🇳", "SN"),
    "222": ("Mauritania", "🇲🇷", "MR"),
    "223": ("Mali", "🇲🇱", "ML"),
    "224": ("Guinea", "🇬🇳", "GN"),
    "225": ("Ivory Coast", "🇨🇮", "CI"),
    "226": ("Burkina Faso", "🇧🇫", "BF"),
    "227": ("Niger", "🇳🇪", "NE"),
    "228": ("Togo", "🇹🇬", "TG"),
    "229": ("Benin", "🇧🇯", "BJ"),

    "230": ("Mauritius", "🇲🇺", "MU"),
    "231": ("Liberia", "🇱🇷", "LR"),
    "232": ("Sierra Leone", "🇸🇱", "SL"),
    "233": ("Ghana", "🇬🇭", "GH"),
    "234": ("Nigeria", "🇳🇬", "NG"),
    "235": ("Chad", "🇹🇩", "TD"),
    "236": ("Central African Rep", "🇨🇫", "CF"),
    "237": ("Cameroon", "🇨🇲", "CM"),
    "238": ("Cape Verde", "🇨🇻", "CV"),
    "239": ("Sao Tome", "🇸🇹", "ST"),
    "240": ("Equatorial Guinea", "🇬🇶", "GQ"),
    "241": ("Gabon", "🇬🇦", "GA"),
    "242": ("Congo", "🇨🇬", "CG"),
    "243": ("DR Congo", "🇨🇩", "CD"),
    "244": ("Angola", "🇦🇴", "AO"),
    "245": ("Guinea-Bissau", "🇬🇼", "GW"),

    "248": ("Seychelles", "🇸🇨", "SC"),
    "249": ("Sudan", "🇸🇩", "SD"),
    "250": ("Rwanda", "🇷🇼", "RW"),
    "251": ("Ethiopia", "🇪🇹", "ET"),
    "252": ("Somalia", "🇸🇴", "SO"),
    "253": ("Djibouti", "🇩🇯", "DJ"),
    "254": ("Kenya", "🇰🇪", "KE"),
    "255": ("Tanzania", "🇹🇿", "TZ"),
    "256": ("Uganda", "🇺🇬", "UG"),
    "257": ("Burundi", "🇧🇮", "BI"),
    "258": ("Mozambique", "🇲🇿", "MZ"),
    "260": ("Zambia", "🇿🇲", "ZM"),
    "261": ("Madagascar", "🇲🇬", "MG"),
    "262": ("Reunion", "🇷🇪", "RE"),
    "263": ("Zimbabwe", "🇿🇼", "ZW"),
    "264": ("Namibia", "🇳🇦", "NA"),
    "265": ("Malawi", "🇲🇼", "MW"),
    "266": ("Lesotho", "🇱🇸", "LS"),
    "267": ("Botswana", "🇧🇼", "BW"),
    "268": ("Eswatini", "🇸🇿", "SZ"),
    "269": ("Comoros", "🇰🇲", "KM"),

    "350": ("Gibraltar", "🇬🇮", "GI"),
    "351": ("Portugal", "🇵🇹", "PT"),
    "352": ("Luxembourg", "🇱🇺", "LU"),
    "353": ("Ireland", "🇮🇪", "IE"),
    "354": ("Iceland", "🇮🇸", "IS"),
    "355": ("Albania", "🇦🇱", "AL"),
    "356": ("Malta", "🇲🇹", "MT"),
    "357": ("Cyprus", "🇨🇾", "CY"),
    "358": ("Finland", "🇫🇮", "FI"),
    "359": ("Bulgaria", "🇧🇬", "BG"),
    "370": ("Lithuania", "🇱🇹", "LT"),
    "371": ("Latvia", "🇱🇻", "LV"),
    "372": ("Estonia", "🇪🇪", "EE"),
    "373": ("Moldova", "🇲🇩", "MD"),
    "374": ("Armenia", "🇦🇲", "AM"),
    "375": ("Belarus", "🇧🇾", "BY"),
    "376": ("Andorra", "🇦🇩", "AD"),
    "377": ("Monaco", "🇲🇨", "MC"),
    "378": ("San Marino", "🇸🇲", "SM"),
    "380": ("Ukraine", "🇺🇦", "UA"),
    "381": ("Serbia", "🇷🇸", "RS"),
    "382": ("Montenegro", "🇲🇪", "ME"),
    "383": ("Kosovo", "🇽🇰", "XK"),
    "385": ("Croatia", "🇭🇷", "HR"),
    "386": ("Slovenia", "🇸🇮", "SI"),
    "387": ("Bosnia", "🇧🇦", "BA"),
    "389": ("North Macedonia", "🇲🇰", "MK"),

    "420": ("Czech Republic", "🇨🇿", "CZ"),
    "421": ("Slovakia", "🇸🇰", "SK"),
    "423": ("Liechtenstein", "🇱🇮", "LI"),

    "500": ("Falkland Islands", "🇫🇰", "FK"),
    "501": ("Belize", "🇧🇿", "BZ"),
    "502": ("Guatemala", "🇬🇹", "GT"),
    "503": ("El Salvador", "🇸🇻", "SV"),
    "504": ("Honduras", "🇭🇳", "HN"),
    "505": ("Nicaragua", "🇳🇮", "NI"),
    "506": ("Costa Rica", "🇨🇷", "CR"),
    "507": ("Panama", "🇵🇦", "PA"),
    "509": ("Haiti", "🇭🇹", "HT"),

    "591": ("Bolivia", "🇧🇴", "BO"),
    "592": ("Guyana", "🇬🇾", "GY"),
    "593": ("Ecuador", "🇪🇨", "EC"),
    "595": ("Paraguay", "🇵🇾", "PY"),
    "597": ("Suriname", "🇸🇷", "SR"),
    "598": ("Uruguay", "🇺🇾", "UY"),

    "670": ("Timor-Leste", "🇹🇱", "TL"),
    "673": ("Brunei", "🇧🇳", "BN"),
    "674": ("Nauru", "🇳🇷", "NR"),
    "675": ("Papua New Guinea", "🇵🇬", "PG"),
    "676": ("Tonga", "🇹🇴", "TO"),
    "677": ("Solomon Islands", "🇸🇧", "SB"),
    "678": ("Vanuatu", "🇻🇺", "VU"),
    "679": ("Fiji", "🇫🇯", "FJ"),
    "680": ("Palau", "🇵🇼", "PW"),
    "685": ("Samoa", "🇼🇸", "WS"),
    "686": ("Kiribati", "🇰🇮", "KI"),
    "687": ("New Caledonia", "🇳🇨", "NC"),
    "688": ("Tuvalu", "🇹🇻", "TV"),
    "689": ("French Polynesia", "🇵🇫", "PF"),
    "691": ("Micronesia", "🇫🇲", "FM"),
    "692": ("Marshall Islands", "🇲🇭", "MH"),

    "850": ("North Korea", "🇰🇵", "KP"),
    "852": ("Hong Kong", "🇭🇰", "HK"),
    "853": ("Macau", "🇲🇴", "MO"),
    "855": ("Cambodia", "🇰🇭", "KH"),
    "856": ("Laos", "🇱🇦", "LA"),

    "960": ("Maldives", "🇲🇻", "MV"),
    "961": ("Lebanon", "🇱🇧", "LB"),
    "962": ("Jordan", "🇯🇴", "JO"),
    "963": ("Syria", "🇸🇾", "SY"),
    "964": ("Iraq", "🇮🇶", "IQ"),
    "965": ("Kuwait", "🇰🇼", "KW"),
    "966": ("Saudi Arabia", "🇸🇦", "SA"),
    "967": ("Yemen", "🇾🇪", "YE"),
    "968": ("Oman", "🇴🇲", "OM"),
    "970": ("Palestine", "🇵🇸", "PS"),
    "971": ("UAE", "🇦🇪", "AE"),
    "972": ("Israel", "🇮🇱", "IL"),
    "973": ("Bahrain", "🇧🇭", "BH"),
    "974": ("Qatar", "🇶🇦", "QA"),
    "975": ("Bhutan", "🇧🇹", "BT"),
    "976": ("Mongolia", "🇲🇳", "MN"),
    "977": ("Nepal", "🇳🇵", "NP"),

    "992": ("Tajikistan", "🇹🇯", "TJ"),
    "993": ("Turkmenistan", "🇹🇲", "TM"),
    "994": ("Azerbaijan", "🇦🇿", "AZ"),
    "995": ("Georgia", "🇬🇪", "GE"),
    "996": ("Kyrgyzstan", "🇰🇬", "KG"),
    "998": ("Uzbekistan", "🇺🇿", "UZ"),
}
# ======================
# 🧰 دوال إدارة قاعدة البيانات (محدثة)
# ======================
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
# ======================
# 🧠 إنشاء قاعدة البيانات (مع جداول جديدة)
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT UNIQUE,
            numbers TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_url TEXT,
            ajax_path TEXT,
            login_page TEXT,
            login_post TEXT,
            username TEXT,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        )
    ''')
    # ✅ جدول القنوات الجديدة
    c.execute('''
        CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1
        )
    ''')

    # تهيئة الإعدادات القديمة (للتوافق مع البوت القديم)
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_channel', '')")
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_enabled', '0')")

    # 🔄 نقل القناة القديمة (إن وُجدت) تلقائيًا إلى الجدول الجديد
    c.execute("SELECT value FROM bot_settings WHERE key = 'force_sub_channel'")
    old_channel = c.fetchone()
    if old_channel and old_channel[0].strip():
        channel = old_channel[0].strip()
        # تأكد أنها ليست مكررة في الجدول الجديد
        c.execute("SELECT 1 FROM force_sub_channels WHERE channel_url = ?", (channel,))
        if not c.fetchone():
            enabled = 1 if get_setting("force_sub_enabled") == "1" else 0
            c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, ?)",
                      (channel, "القناة الأساسية", enabled))

    conn.commit()
    conn.close()

init_db()

# ======================
# 🧰 دوال إدارة قاعدة البيانات (محدثة)
# ======================


def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    """
    يحفظ أو يحدّث بيانات المستخدم باستخدام استعلام واحد (INSERT OR REPLACE).
    هذا يمنع أخطاء التزامن (race conditions) في البيئات متعددة الخيوط.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # نحتاج إلى جلب البيانات القديمة التي لا نريد تغييرها إذا لم يتم توفيرها
    # هذا يمنع مسح البيانات القيمة مثل country_code عند استدعاء الدالة بمعلومات أساسية فقط
    existing_data = get_user(user_id)
    if existing_data:
        # إذا لم يتم توفير country_code جديد، استخدم القديم
        if country_code is None:
            country_code = existing_data[4]
        # إذا لم يتم توفير assigned_number جديد، استخدم القديم
        if assigned_number is None:
            assigned_number = existing_data[5]
        # إذا لم يتم توفير private_combo_country جديد، استخدم القديم
        if private_combo_country is None:
            private_combo_country = existing_data[7]

    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)
    """, (
        user_id,
        username,
        first_name,
        last_name,
        country_code,
        assigned_number,
        user_id, # يُستخدم في COALESCE لجلب حالة الحظر القديمة
        private_combo_country
    ))
    conn.commit()
    conn.close()


def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1
    
def is_maintenance_mode():
    return not BOT_ACTIVE

def set_maintenance_mode(status):
    global BOT_ACTIVE
    BOT_ACTIVE = not status
    
def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_combo(country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0])
    c.execute("SELECT numbers FROM combos WHERE country_code=?", (country_code,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(country_code, numbers, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
    else:
        c.execute("REPLACE INTO combos (country_code, numbers) VALUES (?, ?)",
                  (country_code, json.dumps(numbers)))
    conn.commit()
    conn.close()

def delete_combo(country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
    else:
        c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
    conn.commit()
    conn.close()

def get_all_combos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code FROM combos")
    combos = [row[0] for row in c.fetchall()]
    conn.close()
    return combos

def assign_number_to_user(user_id, number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE assigned_number=?", (number,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

def release_number(old_number):
    if not old_number:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs")
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row
# --- دوال إدارة قنوات الاشتراك الإجباري (متعددة) ---
def get_all_force_sub_channels(enabled_only=True):
    """جلب القنوات (المفعلة فقط أو جميعها)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if enabled_only:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled = 1 ORDER BY id")
    else:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub_channel(channel_url, description=""):
    """إضافة قناة جديدة (لا تسمح بالتكرار)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (channel_url.strip(), description.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # قناة مكررة
    finally:
        conn.close()

def delete_force_sub_channel(channel_id):
    """حذف قناة بالرقم التعريفي"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM force_sub_channels WHERE id = ?", (channel_id,))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def toggle_force_sub_channel(channel_id):
    """تفعيل/تعطيل قناة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET enabled = 1 - enabled WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()
# ======================
# 🔐 دوال الاشتراك الإجباري
# ======================
def force_sub_check(user_id):
    """التحقق من اشتراك المستخدم في **جميع** القنوات المُفعَّلة"""
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True  # لا توجد قنوات → لا يوجد تحقق

    for _, url, _ in channels:
        try:
            # توحيد التنسيق: @xxx بدل https://t.me/xxx
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue  # تجاهل الروابط غير الصحيحة
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"[!] خطأ في التحقق من القناة {url}: {e}")
            return False  # أي فشل = غير مشترك
    return True

def force_sub_markup():
    """إنشاء زر لكل قناة مُفعَّلة + زر التحقق"""
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return None

    markup = types.InlineKeyboardMarkup()
    for _, url, desc in channels:
        text = f" {desc}" if desc else " اشترك في القناة"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ Check your subscription", callback_data="check_sub"))
    return markup
# ======================
# 🤖 إنشاء بوت Telegram
# ======================
bot = telebot.TeleBot(BOT_TOKEN)

# ======================
# 🎮 وظائف البوت التفاعلي
# ======================
def is_admin(user_id):
    return user_id in ADMIN_IDS
    
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. فحص وضع الصيانة (Maintenance Mode) مع صورة
    if is_maintenance_mode() and not is_admin(user_id):
        maintenance_caption = (
            "<b>❍─── <u>𝐖𝐞𝐥𝐜𝐨𝐦 𝐭𝐨 𝙋𝙍𝙄𝙈𝙀 𝙊𝙏𝙋 𝙃𝙐𝘽</u> ───❍</b>\n\n"
            "<b>⚠️ Sorry, dear user</b>\n"
            "<b>The bot is currently in maintenance mode to update services..</b>\n\n"
            "<b>⏳ Please try again later.</b>\n"
            "<b>────────────────────</b>"
        )
        # استبدل الرابط أدناه برابط صورتك الخاصة أو file_id
        maintenance_photo = "https://i.ibb.co/2352v1FN/file-000000004f20720aaa70039fcd26faab-1.png" 
        
        try:
            bot.send_photo(
                chat_id, 
                maintenance_photo, 
                caption=maintenance_caption, 
                parse_mode="HTML"
            )
        except:
            # في حال فشل إرسال الصورة نرسل النص فقط كبديل
            bot.send_message(chat_id, maintenance_caption, parse_mode="HTML")
        return

    # 2. فحص الحظر (Banned Users)
    if is_banned(user_id):
        bot.reply_to(message, "<b>🚫 عذراً، لقد تم حظرك من استخدام البوت.</b>", parse_mode="HTML")
        return

    # 3. فحص الاشتراك الإجباري (Force Subscribe)
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        if markup:
            bot.send_message(chat_id, "<b>🔒 You must subscribe to the channels to use the bot.</b>", parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, "<b>🔒 الاشتراك الإجباري مفعل لكن لم يتم تحديد قناة!</b>", parse_mode="HTML")
        return

    # 4. حفظ المستخدم الجديد وإشعار الإدارة
    if not get_user(user_id):
        save_user(
            user_id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or ""
        )
        
    
    # 5. بناء قائمة الأزرار (الدول والكومبوهات)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    user_data = get_user(user_id)
    private_combo = user_data[7] if user_data else None
    all_combos = get_all_combos()

    # الكومبو الخاص أولاً
    if private_combo and private_combo in COUNTRY_CODES:
        name, flag, _ = COUNTRY_CODES[private_combo]
        buttons.append(types.InlineKeyboardButton(f"{flag} {name} (Private)", callback_data=f"country_{private_combo}"))

    # باقي الدول
    for code in all_combos:
        if code in COUNTRY_CODES and code != private_combo:
            name, flag, _ = COUNTRY_CODES[code]
            buttons.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"country_{code}"))

    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])

    # زر لوحة التحكم للأدمن فقط
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))

    # 6. الرسالة الترحيبية المنسقة
    fancy_text = (
        "<b><u>𝐖𝐞𝐥𝐜𝐨𝐦 𝐭𝐨 𝙋𝙍𝙄𝙈𝙀 𝙊𝙏𝙋 𝙃𝙐𝘽</u></b>\n\n"
        "<b>👨🏻‍💻 <u>𝑼𝒑𝒅𝒂𝒕𝒆 𝑪𝒉𝒂𝒏𝒏𝒆𝒍</u>  • <a href='https://t.me/OV20000'>𝙋𝙍𝙄𝙈𝙀 𝙃𝙐𝘽</a></b>\n\n"
        "<b>────────────────────</b>\n"
        "<b><u>: 𝐒𝐞𝐥𝐞𝐜𝐭 𝐂𝐨𝐮𝐧𝐭𝐫𝐲</u> ⬇️</b>"
    )

    bot.send_message(
        chat_id, 
        fancy_text, 
        parse_mode="HTML", 
        reply_markup=markup,
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified, you can now use the bot.", show_alert=True)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't subscribed yet", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def handle_country_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # 1. الفحوصات الأمنية (حظر واشتراك)
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 You are banned.", show_alert=True)
        return
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        bot.send_message(chat_id, "<b>🔒 You must subscribe to the channels to use the bot.</b>", parse_mode="HTML", reply_markup=markup)
        return

    # 2. استخراج الدولة وفحص الأرقام
    country_code = call.data.split("_", 1)[1]
    available_numbers = get_available_numbers(country_code, user_id)
    
    if not available_numbers:
        # رسالة خطأ فخمة في حال عدم توفر أرقام
        error_msg = "<b>❌ نعتذر، جميع الأرقام قيد الاستخدام حالياً لهذه الدولة.</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 العودة لاختيار دولة أخرى", callback_data="back_to_countries"))
        bot.edit_message_text(error_msg, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        return

    # 3. تخصيص الرقم وتحرير القديم
    assigned = random.choice(available_numbers)
    old_user = get_user(user_id)
    if old_user and old_user[5]:
        release_number(old_user[5])
    
    assign_number_to_user(user_id, assigned)
    save_user(user_id, country_code=country_code, assigned_number=assigned)
    
    # 4. جلب بيانات الدولة وتنسيق النص
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    msg_text = (
        f"<b>◈ Number:</b> <code>{assigned}</code>\n"
        f"<b>◈ Country:</b> {flag} {name}\n"
        f"<b>◈ Status :</b> ⏳ Waiting for SMS"
    )

# 5. بناء الأزرار المحدثة
    markup = types.InlineKeyboardMarkup()

# زر الجروب
    markup.add(types.InlineKeyboardButton("👥 OTP Group", url="https://t.me/OV2001"))

# زر تغيير الرقم
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{country_code}"))

# زر العودة
    markup.add(types.InlineKeyboardButton("🔙 Change Country", callback_data="back_to_countries"))


    # 6. التحديث النهائي للرسالة
    try:
        bot.edit_message_text(
            text=msg_text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        bot.answer_callback_query(call.id, "✅ The number was received successfully")
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def change_number(call):
    user_id = call.from_user.id
    
    # 1. الفحوصات الأمنية
    if is_banned(user_id):
        return
    if not force_sub_check(user_id):
        return
        
    # 2. استخراج كود الدولة
    country_code = call.data.split("_", 2)[2]
    available_numbers = get_available_numbers(country_code, user_id)
    
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ نعتذر، جميع الأرقام قيد الاستخدام حالياً.", show_alert=True)
        return

    # 3. تحرير الرقم القديم وتعيين الجديد
    old_user = get_user(user_id)
    if old_user and old_user[5]:
        release_number(old_user[5])
        
    assigned = random.choice(available_numbers)
    assign_number_to_user(user_id, assigned)
    save_user(user_id, assigned_number=assigned)
    
    # 4. جلب بيانات الدولة والتنسيق الفخم
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    
    msg_text = (
        f"<b>◈ Number:</b> <code>{assigned}</code>\n"
        f"<b>◈ Country:</b> {flag} {name}\n"
        f"<b>◈ Status :</b> ⏳ Waiting for SMS"
    )
# 5. بناء الأزرار المحدثة
    markup = types.InlineKeyboardMarkup()

# زر الجروب
    markup.add(types.InlineKeyboardButton("👥 OTP Group", url="https://t.me/OV2001"))

# زر تغيير الرقم
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{country_code}"))

# زر العودة
    markup.add(types.InlineKeyboardButton("🔙 Change Country", callback_data="back_to_countries"))

    # 6. تحديث الرسالة
    try:
        bot.edit_message_text(
            text=msg_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        # إشعار سريع بنجاح التغيير
        bot.answer_callback_query(call.id, "✅ The number was successfully changed.")
    except Exception as e:
        print(f"Error in change_number: {e}")
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries(call):
    # 1. بناء قائمة الأزرار
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    # جلب البيانات (تأكد من وجود الدوال get_user و get_all_combos في ملفك)
    user = get_user(call.from_user.id)
    private_combo = user[7] if user else None
    all_combos = get_all_combos()

    # إضافة الكومبو الخاص أولاً (إذا وُجد)
    if private_combo and private_combo in COUNTRY_CODES:
        name, flag, _ = COUNTRY_CODES[private_combo]
        buttons.append(types.InlineKeyboardButton(f"{flag} {name} (Private)", callback_data=f"country_{private_combo}"))

    # إضافة الكومبوهات العامة
    for code in all_combos:
        if code in COUNTRY_CODES and code != private_combo:
            name, flag, _ = COUNTRY_CODES[code]
            buttons.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"country_{code}"))

    # توزيع الأزرار في صفوف
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])

    # إضافة زر الإدارة للمشرفين
    if is_admin(call.from_user.id):
        admin_btn = types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")
        markup.add(admin_btn)

    # 2. النص المنسق (نفس تنسيق رسالة الترحيب)
    fancy_text = (
        "<b>❍<u>𝐖𝐞𝐥𝐜𝐨𝐦 𝐭𝐨 𝙋𝙍𝙄𝙈𝙀 𝙊𝙏𝙋 𝙃𝙐𝘽</u>❍</b>\n\n"
        "<b>👨🏻‍💻 <u>𝑼𝒑𝒅𝒂𝒕𝒆 𝑪𝒉𝒂𝒏𝒏𝒆𝒍</u>  • <a href='https://t.me/OV20000'>𝙋𝙍𝙄𝙈𝙀 𝙃𝙐𝘽</a></b>\n\n"
        "<b>────────────────────</b>\n"
        "<b><u>𝐒𝐞𝐥𝐞𝐜𝐭 𝐂𝐨𝐮𝐧𝐭𝐫𝐲</u> ⬇️</b>"
    )

    # 3. تعديل الرسالة الحالية
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=fancy_text,
            parse_mode="HTML",
            reply_markup=markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error editing message: {e}")
        bot.answer_callback_query(call.id)

# ======================
# 🔐 لوحة التحكم الإدارية (محدثة)
# ======================
user_states = {}

def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    
    # 1. زر حالة البوت (يحتل الصدارة)
    status_icon = "🟢" if not is_maintenance_mode() else "🔴"
    status_text = "الآن: يعمل بنجاح" if not is_maintenance_mode() else "الآن: قيد الصيانة"
    markup.add(types.InlineKeyboardButton(f"{status_icon} {status_text} {status_icon}", callback_data="toggle_maintenance"))
    
    # 2. قسم إدارة الكومبوهات (أزرار كبيرة)
    markup.row(
        types.InlineKeyboardButton("📥 إضافة كومبو", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ حذف كومبو", callback_data="admin_del_combo")
    )
    
    # 3. قسم الإحصائيات والتقارير
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_full_report")
    )
    
    # 4. قسم الإذاعة (Broadcast)
    markup.row(
        types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user")
    )
    
    # 5. قسم إدارة المستخدمين
    markup.row(
        types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("👤 معلومات", callback_data="admin_user_info")
    )
    
    # 6. قسم الإعدادات المتقدمة
    markup.row(
        types.InlineKeyboardButton("🔗 إشتراك", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🖥️ اللوحات", callback_data="admin_dashboards"),
        types.InlineKeyboardButton("🔑 برايفت", callback_data="admin_private_combo")
    )

    # 7. زر الخروج
    markup.add(types.InlineKeyboardButton("🔙 مغادرة لوحة التحكم", callback_data="back_to_countries"))
    
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def show_admin_panel(call):
    # التحقق من الرتبة أولاً
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ عذراً، هذا القسم للمطورين فقط.", show_alert=True)
        return

    # النص المنسق فخم جداً
    admin_text = (
        "<b>❍─── <u>𝐋𝐎𝐆𝐈𝐍 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</u> ───❍</b>\n\n"
        "<b>👋 مرحباً بك يا مطور في لوحة التحكم.</b>\n\n"
        "<b>⚙️ يمكنك التحكم في كامل وظائف البوت من هنا.</b>\n"
        "<b>⚠️ تنبيه: أي تغيير في الإعدادات يؤثر على المستخدمين فوراً.</b>\n\n"
        "<b>────────────────────</b>\n"
        "<b>إحصائيات سريعة:</b>\n"
        "<b>• حالة السيرفر: <u>Online</u> ✅</b>\n"
        f"<b>• الوقت الحالي: <u>{datetime.now().strftime('%H:%M')}</u></b>\n"
        "<b>────────────────────</b>"
    )
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=admin_text,
            parse_mode="HTML",
            reply_markup=admin_main_menu(),
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Admin Panel Error: {e}")

    
# ======================
# 📌 ميزة الاشتراك الإجباري في لوحة الإدارة
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id):
        return

    channels = get_all_force_sub_channels(enabled_only=False)
    text = "⚙️ إدارة قنوات الاشتراك الإجباري:\n"
    text += f"إجمالي القنوات: {len(channels)}\n"
    text += "──────────────────\n"

    markup = types.InlineKeyboardMarkup()
    for ch_id, url, desc in channels:
        # جلب الحالة بدقة
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT enabled FROM force_sub_channels WHERE id=?", (ch_id,))
        enabled = c.fetchone()[0]
        conn.close()
        status = "✅" if enabled else "❌"
        btn_text = f"{status} {desc or url[:25]}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"edit_force_ch_{ch_id}"))

    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_force_ch"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_maintenance")
def handle_maintenance_toggle(call):
    if not is_admin(call.from_user.id): return
    
    # عكس الحالة الحالية
    current_status = is_maintenance_mode()
    set_maintenance_mode(not current_status) # دالة الحفظ
    
    new_status_text = "🔓 تم فتح البوت للجميع" if current_status else "🔒 تم قفل البوت (وضع الصيانة)"
    
    # إشعار سريع للأدمن
    bot.answer_callback_query(call.id, new_status_text, show_alert=True)
    
    # تحديث اللوحة فوراً ليتغير شكل الزر
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu())
    
# --- إضافة قناة جديدة ---
@bot.callback_query_handler(func=lambda call: call.data == "add_force_ch")
def add_force_ch_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "add_force_ch_url"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text("أرسل رابط القناة (مثل: https://t.me/xxx أو @xxx):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_force_ch_url")
def add_force_ch_step2(message):
    url = message.text.strip()
    if not (url.startswith("@") or url.startswith("https://t.me/")):
        bot.reply_to(message, "❌ رابط غير صالح! يجب أن يبدأ بـ @ أو https://t.me/")
        return
    user_states[message.from_user.id] = {"step": "add_force_ch_desc", "url": url}
    bot.reply_to(message, "أدخل وصفًا للقناة (أو اترك فارغًا):")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "add_force_ch_desc")
def add_force_ch_step3(message):
    data = user_states[message.from_user.id]
    url = data["url"]
    desc = message.text.strip()
    if add_force_sub_channel(url, desc):
        bot.reply_to(message, f"✅ تم إضافة القناة:\n{url}\nالوصف: {desc or '—'}")
    else:
        bot.reply_to(message, "❌ القناة موجودة مسبقًا!")
    del user_states[message.from_user.id]


# --- تعديل/حذف قناة فردية ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_force_ch_"))
def edit_force_ch(call):
    if not is_admin(call.from_user.id):
        return
    try:
        ch_id = int(call.data.split("_", 3)[3])
    except:
        return
    # جلب بيانات القناة
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description, enabled FROM force_sub_channels WHERE id=?", (ch_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        bot.answer_callback_query(call.id, "❌ القناة غير موجودة!", show_alert=True)
        return

    url, desc, enabled = row
    status = "مفعلة" if enabled else "معطلة"
    text = f"🔧 إدارة القناة:\nالرابط: {url}\nالوصف: {desc or '—'}\nالحالة: {status}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل الوصف", callback_data=f"edit_desc_{ch_id}"))
    if enabled:
        markup.add(types.InlineKeyboardButton("❌ تعطيل", callback_data=f"toggle_ch_{ch_id}"))
    else:
        markup.add(types.InlineKeyboardButton("✅ تفعيل", callback_data=f"toggle_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_ch_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_ch_"))
def toggle_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    toggle_force_sub_channel(ch_id)
    bot.answer_callback_query(call.id, "🔄 تم تغيير حالة القناة", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_ch_"))
def del_ch(call):
    ch_id = int(call.data.split("_", 2)[2])
    if delete_force_sub_channel(ch_id):
        bot.answer_callback_query(call.id, "✅ تم الحذف!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ فشل الحذف!", show_alert=True)
    admin_force_sub(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_desc_"))
def edit_desc_step1(call):
    ch_id = int(call.data.split("_", 2)[2])
    user_states[call.from_user.id] = f"edit_desc_{ch_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"edit_force_ch_{ch_id}"))
    bot.edit_message_text("أدخل الوصف الجديد:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), str) and user_states[msg.from_user.id].startswith("edit_desc_"))
def edit_desc_step2(message):
    try:
        ch_id = int(user_states[message.from_user.id].split("_")[2])
        desc = message.text.strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE force_sub_channels SET description = ? WHERE id = ?", (desc, ch_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, "✅ تم تحديث الوصف!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "waiting_combo_file"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("📤 أرسل ملف الكومبو بصيغة TXT", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_combo_file(message):
    if not is_admin(message.from_user.id):
        return
    if user_states.get(message.from_user.id) != "waiting_combo_file":
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            bot.reply_to(message, "❌ الملف فارغ!")
            return
        first_num = clean_number(lines[0])
        country_code = None
        for code in COUNTRY_CODES:
            if first_num.startswith(code):
                country_code = code
                break
        if not country_code:
            bot.reply_to(message, "❌ لا يمكن تحديد الدولة من الأرقام!")
            return
        save_combo(country_code, lines)
        name, flag, _ = COUNTRY_CODES[country_code]
        bot.reply_to(message, f"✅ تم حفظ الكومبو لدولة {flag} {name}\n🔢 عدد الأرقام: {len(lines)}")
        del user_states[message.from_user.id]
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    combos = get_all_combos()
    if not combos:
        bot.answer_callback_query(call.id, "لا توجد كومبوهات!")
        return
    markup = types.InlineKeyboardMarkup()
    for code in combos:
        if code in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[code]
            markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"del_combo_{code}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("اختر الكومبو للحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    code = call.data.split("_", 2)[2]
    delete_combo(code)
    name, flag, _ = COUNTRY_CODES.get(code, ("Unknown", "🌍", ""))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(f"✅ تم حذف الكومبو: {flag} {name}", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        return
    total_users = len(get_all_users())
    combos = get_all_combos()
    total_numbers = sum(len(get_combo(c)) for c in combos)
    otp_count = len(get_otp_logs())
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(
        f"📊 إحصائيات البوت:\n"
        f"👥 المستخدمين النشطين: {total_users}\n"
        f"🌐 الدول المضافة: {len(combos)}\n"
        f"📞 إجمالي الأرقام: {total_numbers}\n"
        f"🔑 إجمالي الأكواد المستلمة: {otp_count}",
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id):
        return
    try:
        report = "📊 تقرير شامل عن البوت\n" + "="*40 + "\n\n"
        # المستخدمون
        report += "👥 المستخدمون:\n"
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        for u in users:
            status = "محظور" if u[6] else "نشط"
            report += f"ID: {u[0]} | @{u[1] or 'N/A'} | الرقم: {u[5] or 'N/A'} | الحالة: {status}\n"
        report += "\n" + "="*40 + "\n\n"
        # الأكواد
        report += "🔑 سجل الأكواد:\n"
        c.execute("SELECT * FROM otp_logs")
        logs = c.fetchall()
        for log in logs:
            user_info = get_user_info(log[5]) if log[5] else None
            user_tag = f"@{user_info[1]}" if user_info and user_info[1] else f"ID:{log[5] or 'N/A'}"
            report += f"الرقم: {log[1]} | الكود: {log[2]} | المستخدم: {user_tag} | الوقت: {log[4]}\n"
        conn.close()
        report += "\n" + "="*40 + "\n\n"
        report += "تم إنشاء التقرير في: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("bot_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        with open("bot_report.txt", "rb") as f:
            bot.send_document(call.from_user.id, f)
        os.remove("bot_report.txt")
        bot.answer_callback_query(call.id, "✅ تم إرسال التقرير!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لحظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text)
        ban_user(uid)
        bot.reply_to(message, f"✅ تم حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لفك حظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text)
        unban_user(uid)
        bot.reply_to(message, f"✅ تم فك حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أرسل الرسالة للإرسال للجميع:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except:
            pass
    bot.reply_to(message, f"✅ تم الإرسال إلى {success}/{len(users)} مستخدم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_user")
def admin_broadcast_user_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "broadcast_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_user_id")
def admin_broadcast_user_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(message, "أرسل الرسالة:")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, "").startswith("broadcast_msg_"))
def admin_broadcast_user_step3(message):
    uid = int(user_states[message.from_user.id].split("_")[2])
    try:
        bot.send_message(uid, message.text)
        bot.reply_to(message, f"✅ تم الإرسال للمستخدم {uid}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid = int(message.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(message, "❌ المستخدم غير موجود!")
            return
        status = "محظور" if user[6] else "نشط"
        info = f"👤 معلومات المستخدم:\n"
        info += f"🆔: {user[0]}\n"
        info += f".Username: @{user[1] or 'N/A'}\n"
        info += f"الاسم: {user[2] or ''} {user[3] or ''}\n"
        info += f"الرقم المخصص: {user[5] or 'N/A'}\n"
        info += f"الحالة: {status}"
        bot.reply_to(message, info)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "set_force_sub_channel")
def admin_set_force_sub_channel_step2(message):
    channel = message.text.strip()
    if not (channel.startswith("@") or channel.startswith("https://t.me/")):
        bot.reply_to(message, "❌ رابط غير صالح! يجب أن يبدأ بـ @ أو https://t.me/")
        return
    set_setting("force_sub_channel", channel)
    bot.reply_to(message, f"✅ تم تعيين القناة: {channel}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_enable_force_sub")
def admin_enable_force_sub(call):
    set_setting("force_sub_enabled", "1")
    bot.answer_callback_query(call.id, "✅ تم تفعيل الاشتراك الإجباري!", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_disable_force_sub")
def admin_disable_force_sub(call):
    set_setting("force_sub_enabled", "0")
    bot.answer_callback_query(call.id, "❌ تم تعطيل الاشتراك الإجباري!", show_alert=True)
    admin_force_sub(call)

# ======================
# 🖥️ ميزة لوحات الأرقام المتعددة
# ======================
def get_dashboards():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM dashboards")
    rows = c.fetchall()
    conn.close()
    return rows

def save_dashboard(base_url, ajax_path, login_page, login_post, username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO dashboards (base_url, ajax_path, login_page, login_post, username, password)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (base_url, ajax_path, login_page, login_post, username, password))
    conn.commit()
    conn.close()

def delete_dashboard(dash_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM dashboards WHERE id=?", (dash_id,))
    conn.commit()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "admin_dashboards")
def admin_dashboards(call):
    if not is_admin(call.from_user.id):
        return
    dashboards = get_dashboards()
    markup = types.InlineKeyboardMarkup()
    if dashboards:
        for d in dashboards:
            markup.add(types.InlineKeyboardButton(f"لوحة {d[0]}", callback_data=f"view_dashboard_{d[0]}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة لوحة", callback_data="add_dashboard"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("🖥️ لوحات الأرقام:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_dashboard_"))
def view_dashboard(call):
    dash_id = int(call.data.split("_")[2])
    dashboards = get_dashboards()
    dash = next((d for d in dashboards if d[0] == dash_id), None)
    if not dash:
        bot.answer_callback_query(call.id, "❌ اللوحة غير موجودة!")
        return
    text = f"لوحة {dash_id}:\nBase: {dash[1]}\nUsername: {dash[5]}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_dashboard_{dash_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_dashboards"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_dashboard_"))
def del_dashboard(call):
    dash_id = int(call.data.split("_")[2])
    delete_dashboard(dash_id)
    bot.answer_callback_query(call.id, "✅ تم الحذف!", show_alert=True)
    admin_dashboards(call)

@bot.callback_query_handler(func=lambda call: call.data == "add_dashboard")
def add_dashboard_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "add_dash_base"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_dashboards"))
    bot.edit_message_text("أدخل Base URL:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_dash_base")
def add_dashboard_step2(message):
    user_states[message.from_user.id] = {"step": "ajax", "base": message.text}
    bot.reply_to(message, "أدخل AJAX Path:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "ajax")
def add_dashboard_step3(message):
    user_states[message.from_user.id]["ajax"] = message.text
    user_states[message.from_user.id]["step"] = "login_page"
    bot.reply_to(message, "أدخل Login Page URL:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "login_page")
def add_dashboard_step4(message):
    user_states[message.from_user.id]["login_page"] = message.text
    user_states[message.from_user.id]["step"] = "login_post"
    bot.reply_to(message, "أدخل Login POST URL:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "login_post")
def add_dashboard_step5(message):
    user_states[message.from_user.id]["login_post"] = message.text
    user_states[message.from_user.id]["step"] = "username"
    bot.reply_to(message, "أدخل Username:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "username")
def add_dashboard_step6(message):
    user_states[message.from_user.id]["username"] = message.text
    user_states[message.from_user.id]["step"] = "password"
    bot.reply_to(message, "أدخل Password:")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "password")
def add_dashboard_step7(message):
    data = user_states[message.from_user.id]
    save_dashboard(
        data["base"],
        data["ajax"],
        data["login_page"],
        data["login_post"],
        data["username"],
        message.text
    )
    bot.reply_to(message, "✅ تم إضافة اللوحة بنجاح!")
    del user_states[message.from_user.id]

# ======================
# 👤 ميزة كومبو برايفت
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_private_combo")
def admin_private_combo(call):
    if not is_admin(call.from_user.id):
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة كومبو برايفت", callback_data="add_private_combo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح كومبو برايفت", callback_data="del_private_combo"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("👤 كومبو برايفت:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_private_combo")
def add_private_combo_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "add_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_private_user_id")
def add_private_combo_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"add_private_country_{uid}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for code in get_all_combos():
            if code in COUNTRY_CODES:
                name, flag, _ = COUNTRY_CODES[code]
                buttons.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"select_private_{uid}_{code}"))
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
        bot.reply_to(message, "اختر الدولة:", reply_markup=markup)
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_private_"))
def select_private_combo(call):
    parts = call.data.split("_")
    uid = int(parts[2])
    country_code = parts[3]
    save_user(uid, private_combo_country=country_code)
    name, flag, _ = COUNTRY_CODES[country_code]
    bot.answer_callback_query(call.id, f"✅ تم تعيين كومبو برايفت لـ {uid} - {flag} {name}", show_alert=True)
    admin_private_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "del_private_combo")
def del_private_combo_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "del_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "del_private_user_id")
def del_private_combo_step2(message):
    try:
        uid = int(message.text)
        save_user(uid, private_combo_country=None)
        bot.reply_to(message, f"✅ تم مسح الكومبو البرايفت للمستخدم {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")
    del user_states[message.from_user.id]

# ======================
# 🆕 دالة جديدة: جلب الأرقام المتاحة (غير المستخدمة) مع دعم private
# ======================
def get_available_numbers(country_code, user_id=None):
    all_numbers = get_combo(country_code, user_id)
    if not all_numbers:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used_numbers = set(row[0] for row in c.fetchall())
    conn.close()
    available = [num for num in all_numbers if num not in used_numbers]
    return available

# ======================
# 🔄 الدالة المعدلة لإرسال OTP للمستخدم + الجروب
def send_otp_to_user_and_group(date_str, number, sms, service_api=None):
    try:
        # تأخير عشوائي موزّع صح عشان نهرب من الـ Spam detection
        time.sleep(random.uniform(1.0, 3.0))

        # استخراج البيانات الأساسية
        otp_code = extract_otp(sms)
        country_name, country_flag, country_code = get_country_info(number)
        service = service_api if service_api else detect_service(sms)

        # تسجيل العملية في القاعدة
        try:
            user_id = get_user_by_number(number)
            log_otp(number, otp_code, sms, user_id)
        except:
            user_id = None

        # ───── إرسال خاص للمستخدم ─────
        if user_id:
            try:
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("👤 Owner", url="https://t.me/OV2001"),
                    types.InlineKeyboardButton("📢 Channel", url="https://t.me/OV2001")
                )
                bot.send_message(
                    user_id,
                    (f"<b><u>✨ SPEED OTP Received ✨</u></b>\n\n"
                     f"🌍 <b>Country:</b> {country_name} {country_flag}\n"
                     f"⚙ <b>Service:</b> {service}\n"
                     f"☎ <b>Number:</b> <code>{number}</code>\n"
                     f"🕒 <b>Time:</b> {date_str}\n\n"
                     f"🔐 <b>Code:</b> <code>{otp_code}</code>"),
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception as e:
                if "Too Many Requests" in str(e):
                    print(f"⚠️ ضغط إرسال للمستخدم {user_id}.. سيتم التخطي للجروب")

        # ───── إرسال للجروب (مع حماية إعادة المحاولة) ─────
        text = format_message(date_str, number, sms)
        
        # بنحاول نبعت 3 مرات لو تليجرام رفض بسبب الزحمة
        for attempt in range(3):
            try:
                # التعديل الجوهري هنا: ضفنا sms كمتغير تالت عشان الزرار يشتغل
                if send_to_telegram_group(text, otp_code, sms):
                    print(f"✅ [SUCCESS] GROUP | {number}")
                    break
                else:
                    break
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print(f"⚠️ تليجرام مضغوط.. محاولة {attempt+1} للرقم {number} بعد 6 ثواني")
                    time.sleep(6)
                    continue
                else:
                    print(f"❌ [ERROR] GROUP | {e}")
                    break

    except Exception as e:
        print(f"⚠️ Error in sending Thread: {e}")

# ======================
# 📡 دوال الاتصال بالـ Dashboard (كما هي من الملف الأصلي)
# ======================
# ======================
# 📡 دوال الاتصال بالـ API (نظام Albrans المطور)
# ======================

# لم نعد بحاجة لعمل headers معقدة ولا لمحاكاة متصفح أندرويد لأن الـ API مخصص للبرمجة
session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "User-Agent": "Albrans-Monitor/2.0"
})

def retry_request(func, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):
    """دالة إعادة المحاولة في حالة وقوع خطأ في الشبكة"""
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️ محاولة {attempt + 1}/{max_retries} فشلت.. انتظار {retry_delay} ثانية")
                time.sleep(retry_delay)
            else:
                print(f"❌ فشلت جميع المحاولات بعد {max_retries} مرات.")
                raise
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            raise

# 🛑 دالة login_for_dashboard لم تعد مستخدمة في نظام الـ API 
# ولكن سنبقيها كـ "دالة فارغة" إذا كان الـ Loop يناديها لتجنب الأخطاء
def login_for_dashboard(dash):
    # في نظام الـ API التوكن هو تسجيل الدخول
    dash["is_logged_in"] = True
    return True

def build_api_url_for_dashboard(dash):
    """بناء رابط الطلب بناءً على التاريخ الحالي والتوكن"""
    # التاريخ يبدأ من بداية اليوم (00:00:00) لضمان جلب كل جديد
    start_date = datetime.now().strftime('%Y-%m-%d 00:00:00')
    
    # بناء الرابط حسب التنسيق الذي أرسله المشرف
    # لاحظ أننا استخدمنا dt1 فقط لأن dt2 السيرفر بيعتبرها "الآن" لو سبناها فاضية
    params = {
        "token": dash["token"],
        "dt1": start_date,
        "dt2": "", 
        "records": dash["records"]
    }
    
    # تحويل القاموس لرابط Query String
    query_string = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
    return f"{dash['api_url']}?{query_string}"

def fetch_api_json_for_dashboard(dash, url):
    """جلب بيانات الـ JSON ومعالجة الأخطاء الشائعة"""
    FETCH_TIMEOUT = 15 

    def do_fetch():
        r = dash["session"].get(url, timeout=FETCH_TIMEOUT)
        
        if r.status_code == 200:
            try:
                return r.json()
            except:
                print(f"[{dash['name']}] ❌ فشل في تحليل الـ JSON")
                return None
        elif r.status_code == 503:
            print(f"[{dash['name']}] ⚠️ السيرفر مضغوط (503).")
            return None
        else:
            print(f"[{dash['name']}] ❌ خطأ سيرفر: {r.status_code}")
            return None

    try:
        return retry_request(do_fetch, max_retries=2, retry_delay=3)
    except:
        return None

def extract_rows_from_json(j):
    """
    توحيد شكل بيانات الـ API
    يدعم dict / list / aaData / data / rows
    """
    if j is None:
        return []

    # أشهر مفاتيح APIs
    for key in ("data", "rows", "aaData", "aa_data"):
        if isinstance(j, dict) and key in j and isinstance(j[key], list):
            return j[key]

    # لو رجع List مباشر
    if isinstance(j, list):
        return j

    # آخر حل: أي قيمة List داخل dict
    if isinstance(j, dict):
        for v in j.values():
            if isinstance(v, list):
                return v

    return []

def fetch_data():
    if not DASHBOARD_CONFIGS:
        return []

    dash = DASHBOARD_CONFIGS[0]
    today = datetime.now().strftime('%Y-%m-%d 00:00:00')

    try:
        url = (
            f"{dash['api_url']}?"
            f"token={dash['token']}&"
            f"dt1={quote_plus(today)}&"
            f"records={dash['records']}"
        )
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            return extract_rows_from_json(r.json())
    except Exception as e:
        print(f"❌ API Error: {e}")

    return []

def clean_html(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    return text

def clean_number(number):
    if not number:
        return ""
    number = re.sub(r'\D', '', str(number))
    return number

def row_to_tuple(row, config_type="old_list"):
    date_str, number, sms = "", "", ""
    
    # لو اللوحة قديمة (نظام القائمة)
    if config_type == "old_list":
        try:
            # التأكد من تنظيف البيانات واستخراجها من مكانها الصح في القائمة
            date_str = clean_html(str(row[0])) # التاريخ غالباً أول عنصر
            number = clean_number(str(row[1])) # الرقم تاني عنصر
            sms = clean_html(str(row[2]))      # الرسالة تالت عنصر
        except:
            pass

    # لو اللوحة جديدة (Ziad Panel - نظام الـ Dictionary)
    elif config_type == "new_json":
        # هنا بنستخدم الأسماء اللي الـ API بتاع زياد بيبعتها (dt, num, message)
        date_str = clean_html(str(row.get("dt", "")))
        number = clean_number(str(row.get("num", "")))
        sms = clean_html(str(row.get("message", "")))

    # عمل مفتاح فريد لمنع التكرار (رقم + رسالة + وقت)
    key = f"{number}|{sms}|{date_str}"
    return date_str, number, sms, key

def get_country_info(number):
    number = number.strip().replace("+", "").replace(" ", "").replace("-", "")

    for code, (name, flag, short) in COUNTRY_CODES.items():
        if number.startswith(code):
            return name, flag, short

    return "Unknown", "🌍", "UN"


def mask_number(number):
    number = number.strip()
    if len(number) > 8:
        return number[:4] + "⁦⁦•••" + number[-4:]
    return number

def extract_otp(message):
    patterns = [
        r'(?:code|رمز|كود|verification|تحقق|otp|pin)[:\s]+[‎]?(\d{3,8}(?:[- ]\d{3,4})?)',
        r'(\d{3})[- ](\d{3,4})',
        r'\b(\d{4,8})\b',
        r'[‎](\d{3,8})',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                return ''.join(match.groups())
            return match.group(1).replace(' ', '').replace('-', '')
    all_numbers = re.findall(r'\d{4,8}', message)
    if all_numbers:
        return all_numbers[0]
    return "N/A"

def detect_service(message):
    message_lower = message.lower()

    # القاموس الأساسي (زي ما هو)
    services = {
        "#WP": ["whatsapp", "واتساب", "واتس"],
        "#FB": ["facebook", "فيسبوك", "fb"],
        "#IG": ["instagram", "انستقرام", "انستا"],
        "#TG": ["telegram", "تيليجرام", "تلي"],
        "#TW": ["twitter", "تويتر", "x"],
        "#GG": ["google", "gmail", "جوجل", "جميل"],
        "#DC": ["discord", "ديسكورد"],
        "#LN": ["line", "لاين"],
        "#VB": ["viber", "فايبر"],
        "#SK": ["skype", "سكايب"],
        "#SC": ["snapchat", "سناب"],
        "#TT": ["tiktok", "تيك توك", "تيك"],
        "#AMZ": ["amazon", "امازون"],
        "#APL": ["apple", "ابل", "icloud"],
        "#MS": ["microsoft", "مايكروسوفت"],
        "#IN": ["linkedin", "لينكد"],
        "#UB": ["uber", "اوبر"],
        "#AB": ["airbnb", "ايربنب"],
        "#NF": ["netflix", "نتفلكس"],
        "#SP": ["spotify", "سبوتيفاي"],
        "#YT": ["youtube", "يوتيوب"],
        "#GH": ["github", "جيت هاب"],
        "#PT": ["pinterest", "بنتريست"],
        "#PP": ["paypal", "باي بال"],
        "#BK": ["booking", "بوكينج"],
        "#TL": ["tala", "تالا"],
        "#OLX": ["olx", "اوليكس"],
        "#STC": ["stcpay", "stc"],
    }

    # ✅ التحقق الأساسي (زي ما هو)
    for service_code, keywords in services.items():
        for keyword in keywords:
            if keyword in message_lower:
                return service_code

    # ✅ Fallback ذكي من صيغة رسالة OTP نفسها
    if "code" in message_lower or "verification" in message_lower:
        if "telegram" in message_lower:
            return "#TG"
        if "whatsapp" in message_lower:
            return "#WP"
        if "facebook" in message_lower:
            return "#FB"
        if "instagram" in message_lower:
            return "#IG"
        if "google" in message_lower or "gmail" in message_lower:
            return "#GG"
        if "twitter" in message_lower or "x.com" in message_lower:
            return "#TW"

    #  آخر حل
    return "Unknown"

def delete_message_after_delay(chat_id, message_id, delay=72000):
    """تحذف الرسالة بعد مرور delay ثانية"""
    time.sleep(delay)
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
        payload = {"chat_id": chat_id, "message_id": message_id}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ فشل حذف الرسالة: {e}")

# ----------------------------
def send_to_telegram_group(text, otp_code, full_sms):
    # 1. تجهيز الأزرار مع ميزة النسخ للرسالة الكاملة
    keyboard = {
        "inline_keyboard": [
            [{"text": f"Click to Copy Code: {otp_code}", "copy_text": {"text": str(otp_code)}}],
            [{"text": "📋 Full Message", "copy_text": {"text": full_sms}}],
            [
                {"text": "💬 Channel", "url": "https://t.me/OV2001"},
                {"text": "🤖 Bot Panel", "url": "https://t.me/OV2001"}
            ],
            [{"text": "👨‍💻 Developer", "url": "https://t.me/OV2001"}]
        ]
    }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    success_count = 0
    
    # 2. حلقة الإرسال لجميع المعرفات الموجودة في CHAT_IDS
    for chat_id in CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard)
            }
            
            # محاولة الإرسال الفعلي
            resp = requests.post(url, json=payload, timeout=15)
            
            if resp.status_code == 200:
                print(f"✅ [SUCCESS] تم إرسال الرسالة بنجاح إلى: {chat_id}")
                success_count += 1

                # تشغيل مؤقت الحذف التلقائي (72000 ثانية = 20 ساعة)
                msg_id = resp.json().get("result", {}).get("message_id")
                if msg_id:
                    threading.Thread(
                        target=delete_message_after_delay, 
                        args=(chat_id, msg_id, 72000), 
                        daemon=True
                    ).start()
            else:
                print(f"⚠️ [FAILED] تليجرام رفض الطلب لآيدي {chat_id}: {resp.text}")
                
        except Exception as e:
            print(f"❌ [ERROR] خطأ غير متوقع مع آيدي {chat_id}: {e}")

    return success_count > 0




def html_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")   # مهم جداً
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

def format_message(date_str, number, sms):
    country_name, country_flag, country_code = get_country_info(number)
    masked_num = mask_number(number)
    otp_code = extract_otp(sms)
    service = detect_service(sms)

    message = (
        f"\n"
        f" {country_flag} #{country_code} [{service}] {masked_num} \n"
        f""
    )
    return message

# ======================
# 🔄 الحلقة الرئيسية (معدلة لدعم لوحات متعددة)
# ======================
# ======================
# 🔄 دوال التشغيل الآمنة (محمية ضد التوقف)
# ======================

def run_bot():
    """تشغيل البوت مع خاصية إعادة الاتصال التلقائي"""
    print("[*] Starting bot with infinity polling...")
    while True:
        try:
            # infinity_polling بيعيد الاتصال لوحده لو النت فصل
            # timeout=60 بيخلي الاتصال مفتوح لفترة أطول عشان ميقطعش بسرعة
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Bot Polling Crashed: {e}")
            time.sleep(5)  # استراحة قصيرة قبل إعادة المحاولة

def main_loop():
    print("🚀 Monitoring started (Optimized Mode)...")
    sent = set()

    while True:
        for dash in DASHBOARD_CONFIGS:
            try:
                # 1. جلب البيانات باستخدام الـ Session والـ Timeout والـ Records اللي أنت حددتهم
                response = dash["session"].get(
                    dash['api_url'], 
                    params={"token": dash['token'], "records": dash['records']}, 
                    timeout=TIMEOUT # اللي هي 5 ثواني
                )
                
                result = response.json()
                rows = result.get('data', []) if isinstance(result, dict) else result
                
                if not rows: continue

                # 2. معالجة آخر 10 رسايل
                for row in rows[-10:]:
                    try:
                        date_str, number, sms, key = row_to_tuple(row, dash.get('type', 'old_list'))

                        if key not in sent:
                            print(f"📩 [{dash['name']}] New: {number}")
                            
                            # تشغيل الإرسال في خيط منفصل
                            threading.Thread(
                                target=send_otp_to_user_and_group, 
                                args=(date_str, number, sms),
                                daemon=True
                            ).start()
                            
                            sent.add(key)
                            
                            # استراحة نص ثانية بين كل رسالة والتانية جوه اللفة 
                            # عشان تليجرام ميزعلش لو الـ 10 رسايل نزلوا مع بعض
                            time.sleep(0.5) 
                            
                    except: continue

            except Exception as e:
                print(f"⚠️ {dash['name']} Error: {e}")
                continue
        
        # 3. تنظيف الذاكرة لو زادت عن 2000 رسالة
        if len(sent) > 2000:
            sent = set(list(sent)[-1000:])
        
        # 4. التعديل اللي سألت عليه: الاستراحة بين اللفات
        # البوت هيستنى الـ 5 ثواني (REFRESH_INTERVAL) قبل ما يلف لفة جديدة
        time.sleep(REFRESH_INTERVAL)

# --- تشغيل البوت والمراقب ---
if __name__ == "__main__":
    try:
        # تشغيل استقبال أوامر البوت في الخلفية
        bot_thread = threading.Thread(target=lambda: bot.infinity_polling(), daemon=True)
        bot_thread.start()
        print("🤖 Telegram Bot is running...")
        print("⏸️ OTP monitoring from websites is DISABLED")
        print("⚠️ Bot will only respond to commands, won't fetch OTP codes")
    except Exception as e:
        print(f"⚠️ Bot Thread Error: {e}")

    # البقاء في حلقة فارغة للحفاظ على تشغيل البرنامج
    while True:
        time.sleep(3600)  # النوم لمدة ساعة فقط للحفاظ على البرنامج نشط