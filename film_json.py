import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.request import HTTPXRequest

# === تنظیمات کلی ===
TOKEN = "8193454751:AAFYe2yYgCLIVJhTtZNG-OIXDRV1PPNzWhg"
BOT_USERNAME = "Filmvaseryaleirani_iii_bot"  # بدون @
CHANNEL_USERNAME = "@ISTFC"  # آیدی کانال با @
ADMINS = [1204215539]  # آیدی عددی ادمین‌ها


# === فایل دیتا ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# === /start: ارسال فیلم در صورت عضویت ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            data = load_data()
            if args:
                key = args[0].lower()
                if key in data:
                    msg = await update.message.reply_video(data[key], caption=f"🎬 فیلم: {key}")
                    warn = await update.message.reply_text("⏳ این فیلم بعد از 30 ثانیه حذف می‌شود.")
                    await asyncio.sleep(30)
                    try:
                        await msg.delete()
                        await warn.delete()
                    except:
                        pass
                else:
                    await update.message.reply_text("❌ فیلمی با این اسم پیدا نشد.")
            else:
                await update.message.reply_text("سلام! برای دیدن فیلم لینک رو از کانال بزن.")
        else:
            raise Exception("Not a member")
    except:
        join_link = f"https://t.me/{CHANNEL_USERNAME.strip('@')}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 عضویت در کانال", url=join_link)],
            [InlineKeyboardButton("✅ بررسی عضویت", callback_data=f"check_{args[0] if args else 'none'}")]
        ])
        await update.message.reply_text(
            "⛔ فقط اعضای کانال می‌تونن از ربات استفاده کنن.\n\n👇 اول عضو شو بعد بررسی کن:",
            reply_markup=keyboard
        )

# === بررسی عضویت از دکمه ===
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    args = query.data.split("_", 1)[1]

    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            data = load_data()
            key = args.lower()
            if key in data:
                msg = await query.message.reply_video(data[key], caption=f"🎬 فیلم: {key}")
                warn = await query.message.reply_text("⏳ این فیلم بعد از 30 ثانیه حذف می‌شود.")
                await asyncio.sleep(30)
                try:
                    await msg.delete()
                    await warn.delete()
                except:
                    pass
            else:
                await query.message.reply_text("❌ فیلمی با این اسم پیدا نشد.")
        else:
            raise Exception("Not subscribed")
    except:
        join_link = f"https://t.me/{CHANNEL_USERNAME.strip('@')}"
        await query.message.reply_text(
            f"⛔ هنوز عضو نیستی!\n📎 عضو شو:\n{join_link}"
        )

# === دریافت فایل و درخواست نام فیلم از ادمین ===
async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن فیلم آپلود کنن.")
        return

    if update.message.video:
        file_id = update.message.video.file_id
        await update.message.reply_text("📝 لطفاً اسم فیلم رو بنویس:")
        context.user_data["pending_file_id"] = file_id
    else:
        await update.message.reply_text("❌ لطفاً فقط فیلم بفرست.")

# === دریافت اسم فیلم و ذخیره همراه لینک اختصاصی ===
async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "pending_file_id" in context.user_data:
        name = update.message.text.strip().lower().replace(" ", "_")

        data = load_data()
        if name in data:
            await update.message.reply_text("⚠️ این اسم قبلاً استفاده شده. یه اسم دیگه بده.")
            return

        data[name] = context.user_data["pending_file_id"]
        save_data(data)

        link = f"https://t.me/{BOT_USERNAME}?start={name}"
        await update.message.reply_text(f"✅ فیلم '{name}' ذخیره شد.\n📎 لینک فیلم:\n{link}")

        context.user_data.clear()
    else:
        await update.message.reply_text("❌ لطفاً اول یه فیلم بفرست.")

# === اجرای ربات ===
if __name__ == "__main__":
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    app = ApplicationBuilder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="^check_"))
    app.add_handler(MessageHandler(filters.VIDEO, save_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_name))

    print("✅ ربات روشنه و آماده ارسال فیلم با تایمره...")
    app.run_polling()
