import json
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from pyrogram.enums import ButtonStyle  # just imported (UI styling limited)

BOT_TOKEN = "8684382287:AAHmeY-qd19A5VFe2DTJ4edxZKcvDCVoP8A"
REMOVE_BG_API = "f3Se7SVDqpvsM5TLknPKN6Cz"
IMGBB_API = "62736b1fc27c5c6bb91063f2ec92913b"
BOT_USERNAME = "IMAGE_TO_BACKREMOVE_bot"

USERS_FILE = "users.json"

# Load database
try:
    with open(USERS_FILE) as f:
        users = json.load(f)
except:
    users = {}

mode = {}

def save():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def reset(uid):
    today = str(datetime.now().date())
    if users[uid].get("last") != today:
        users[uid]["credits"] = 2
        users[uid]["last"] = today

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ref = context.args[0] if context.args else None

    if uid not in users:
        users[uid] = {"credits": 2, "refs": []}

        # Referral system
        if ref and ref != uid and ref in users:
            if uid not in users[ref]["refs"]:
                users[ref]["refs"].append(uid)
                users[ref]["credits"] += 1

    reset(uid)
    save()

    keyboard = [
        [InlineKeyboardButton("👥 GROUP", url="https://t.me/+dv_rcq5uIXhmMWM1")],
        [InlineKeyboardButton("🌐 NETWORK", url="https://t.me/+Imyf3M9TO5k1ODRl")],
        [InlineKeyboardButton("🔥 REMOVE BACKGROUND", callback_data="remove")],
        [InlineKeyboardButton("🖼 IMAGE TO LINK", callback_data="upload")],
        [InlineKeyboardButton("👨‍💻 DEVELOPER", url="https://t.me/YOUR_MADARA_BRO")],
        [InlineKeyboardButton("🔗 REFERRAL LINK", callback_data="ref")]
    ]

    await update.message.reply_photo(
        photo="https://i.ibb.co/Mk5MnbRY/x.jpg",
        caption="🔥 *Advanced BG Bot*\n\n🎯 Remove BG + Upload Link\n💰 2 credits/day",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# REFERRAL LINK
async def ref(update, context):
    q = update.callback_query
    uid = str(q.from_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    await q.answer()
    await q.message.reply_text(f"🔗 Your Referral Link:\n{link}")

# MODE SET
async def set_mode(update, context):
    q = update.callback_query
    uid = str(q.from_user.id)

    if q.data == "remove":
        mode[uid] = "remove"
        await q.answer()
        await q.message.reply_text("🧠 Send image to remove background")

    elif q.data == "upload":
        mode[uid] = "upload"
        await q.answer()
        await q.message.reply_text("📤 Send image to upload")

# IMAGE HANDLER
async def handle_photo(update, context):
    uid = str(update.effective_user.id)

    if uid not in users:
        return

    reset(uid)

    if users[uid]["credits"] <= 0:
        return await update.message.reply_text("❌ No credits left!")

    file = await update.message.photo[-1].get_file()
    img_url = file.file_path

    # UPLOAD MODE
    if mode.get(uid) == "upload":
        users[uid]["credits"] -= 1
        save()

        img_bytes = requests.get(img_url).content

        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API},
            files={"image": img_bytes}
        )

        data = res.json()
        if not data.get("success"):
            return await update.message.reply_text("❌ Upload failed")

        return await update.message.reply_text(f"🌐 Your Image Link:\n{data['data']['url']}")

    # REMOVE BACKGROUND
    users[uid]["credits"] -= 1
    save()

    res = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        data={"image_url": img_url},
        headers={"X-Api-Key": REMOVE_BG_API}
    )

    if res.status_code != 200:
        return await update.message.reply_text("❌ BG remove failed")

    await update.message.reply_photo(res.content)

# MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(ref, pattern="ref"))
app.add_handler(CallbackQueryHandler(set_mode, pattern="remove|upload"))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("🚀 Bot running...")
app.run_polling()
