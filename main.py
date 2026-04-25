import json
import requests
from datetime import datetime
from io import BytesIO
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
REMOVE_BG_API = "f3Se7SVDqpvsM5TLknPKN6Cz"
IMGBB_API = "62736b1fc27c5c6bb91063f2ec92913b"

USERS_FILE = "users.json"

# Load DB
try:
    with open(USERS_FILE) as f:
        users = json.load(f)
except:
    users = {}

user_images = {}
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

        # Anti-fake referral
        if ref and ref != uid and ref in users:
            if uid not in users[ref]["refs"]:
                users[ref]["refs"].append(uid)
                users[ref]["credits"] += 1

    reset(uid)
    save()

    kb = [
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
        reply_markup=InlineKeyboardMarkup(kb)
    )

# REF LINK
async def ref(update, context):
    q = update.callback_query
    uid = str(q.from_user.id)
    link = f"https://t.me/YOUR_BOT_USERNAME?start={uid}"
    await q.answer()
    await q.message.reply_text(f"🔗 Your Referral Link:\n{link}")

# SET MODE
async def set_upload(update, context):
    uid = str(update.callback_query.from_user.id)
    mode[uid] = "upload"
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📤 Send image to upload")

async def set_remove(update, context):
    uid = str(update.callback_query.from_user.id)
    mode[uid] = "remove"
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🧠 Send image to remove background")

# IMAGE HANDLER
async def handle_photo(update, context):
    uid = str(update.effective_user.id)

    if uid not in users:
        return

    reset(uid)

    if users[uid]["credits"] <= 0:
        return await update.message.reply_text("❌ No credits left!")

    file = await update.message.photo[-1].get_file()
    img_bytes = requests.get(file.file_path).content

    # MODE: UPLOAD
    if mode.get(uid) == "upload":
        users[uid]["credits"] -= 1
        save()

        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API},
            files={"image": img_bytes}
        )

        data = res.json()
        if not data.get("success"):
            return await update.message.reply_text("❌ Upload failed")

        link = data["data"]["url"]
        return await update.message.reply_text(f"🌐 Your Image Link:\n{link}")

    # MODE: REMOVE BG
    users[uid]["credits"] -= 1
    save()

    res = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        data={"image_url": file.file_path},
        headers={"X-Api-Key": REMOVE_BG_API}
    )

    if res.status_code != 200:
        return await update.message.reply_text("❌ BG remove failed")

    user_images[uid] = res.content

    kb = [[
        InlineKeyboardButton("🔴 RED", callback_data="red"),
        InlineKeyboardButton("🔵 BLUE", callback_data="blue"),
        InlineKeyboardButton("⚪ WHITE", callback_data="white"),
        InlineKeyboardButton("🎨 CUSTOM", callback_data="custom")
    ]]

    await update.message.reply_photo(res.content, reply_markup=InlineKeyboardMarkup(kb))

# APPLY COLOR
async def apply_color(update, context):
    q = update.callback_query
    uid = str(q.from_user.id)
    c = q.data

    if uid not in user_images:
        return await q.answer("Send image first")

    if c == "custom":
        await q.answer()
        return await q.message.reply_text("Send HEX color like #ff0000")

    colors = {
        "red": (255,0,0),
        "blue": (0,0,255),
        "white": (255,255,255)
    }

    fg = Image.open(BytesIO(user_images[uid])).convert("RGBA")
    bg = Image.new("RGBA", fg.size, colors[c])
    final = Image.alpha_composite(bg, fg)

    bio = BytesIO()
    final.save(bio, "PNG")
    bio.seek(0)

    await q.answer()
    await q.message.reply_photo(bio)

# CUSTOM COLOR
async def custom_color(update, context):
    uid = str(update.effective_user.id)
    text = update.message.text.strip()

    if not text.startswith("#") or len(text) != 7:
        return

    try:
        rgb = tuple(int(text[i:i+2], 16) for i in (1,3,5))
    except:
        return

    if uid not in user_images:
        return

    fg = Image.open(BytesIO(user_images[uid])).convert("RGBA")
    bg = Image.new("RGBA", fg.size, rgb)
    final = Image.alpha_composite(bg, fg)

    bio = BytesIO()
    final.save(bio, "PNG")
    bio.seek(0)

    await update.message.reply_photo(bio)

# MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(ref, pattern="ref"))
app.add_handler(CallbackQueryHandler(set_upload, pattern="upload"))
app.add_handler(CallbackQueryHandler(set_remove, pattern="remove"))
app.add_handler(CallbackQueryHandler(apply_color, pattern="red|blue|white|custom"))

app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_color))

print("🚀 Bot running...")
app.run_polling()
