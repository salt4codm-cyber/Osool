
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

DATA_FILE = "osool_data.json"
MANAGERS = ["صادق"]  # فقط شما مدیر هستید
CHANNEL_ID = "@dMquuneASWNlYWU0"  # کانال

# بارگذاری داده‌ها
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! پیام‌های درسی خودت رو با قالب {Osool} ارسال کن.\nبرای مشاهده درس‌ها /list را بزنید.\nبرای جستجو /search <کلمه>.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text
    lines = text.strip().split("\n")
    if len(lines) < 3 or lines[0].strip() != "{Osool}" or not lines[1].startswith("#"):
        return

    user_name = lines[1][1:].strip()
    if "درس" in lines[2] and "قسمت" in lines[2]:
        lesson_part = lines[2].strip()
        try:
            lesson_name = lesson_part.split("قسمت")[0].strip()
            part_number = lesson_part.split("قسمت")[1].strip()
        except:
            return
    else:
        return

    message_content = "\n".join(lines[3:]).strip()

    if lesson_name not in data:
        data[lesson_name] = {}
    if user_name not in data[lesson_name]:
        data[lesson_name][user_name] = {}
    data[lesson_name][user_name][part_number] = message_content
    save_data()

    try:
        await message.delete()
    except:
        pass

    await update.message.reply_text(f"پیام درس {lesson_name} قسمت {part_number} از {user_name} ذخیره شد ✅")

async def list_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data:
        await update.message.reply_text("هیچ داده‌ای موجود نیست.")
        return
    buttons = [[InlineKeyboardButton(lesson, callback_data=f"lesson|{lesson}")] for lesson in data.keys()]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("درس‌ها:", reply_markup=markup)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("لطفاً یک کلمه برای جستجو وارد کنید: /search <کلمه>")
        return
    results = ""
    for lesson, users in data.items():
        for user, parts in users.items():
            for part, msg in parts.items():
                if query in msg:
                    results += f"{lesson} - {user} - قسمت {part}:\n{msg}\n\n"
    await update.message.reply_text(results if results else "هیچ نتیجه‌ای پیدا نشد.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")

    if parts[0] == "lesson":
        lesson = parts[1]
        if lesson in data:
            buttons = [[InlineKeyboardButton(user, callback_data=f"user|{lesson}|{user}")] for user in data[lesson]]
            markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(f"کاربران درس {lesson}:", reply_markup=markup)

    elif parts[0] == "user":
        lesson, user_name = parts[1], parts[2]
        if lesson in data and user_name in data[lesson]:
            buttons = []
            text_msg = ""
            for part, msg in data[lesson][user_name].items():
                text_msg += f"قسمت {part}:\n{msg}\n\n"
                buttons.append([
                    InlineKeyboardButton(f"❌ حذف قسمت {part}", callback_data=f"delete|{lesson}|{user_name}|{part}"),
                    InlineKeyboardButton(f"📤 ارسال به کانال", callback_data=f"send|{lesson}|{user_name}|{part}")
                ])
            markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(f"مطالب {user_name} در {lesson}:\n\n{text_msg}", reply_markup=markup)

    elif parts[0] == "delete":
        lesson, user_name, part = parts[1], parts[2], parts[3]
        sender = query.from_user.first_name
        if sender == user_name or sender in MANAGERS:
            try:
                del data[lesson][user_name][part]
                if not data[lesson][user_name]:
                    del data[lesson][user_name]
                if not data[lesson]:
                    del data[lesson]
                save_data()
                await query.edit_message_text(f"قسمت {part} حذف شد ✅")
            except:
                await query.edit_message_text("خطا در حذف پیام ❌")
        else:
            await query.answer("شما اجازه حذف این قسمت را ندارید ❌", show_alert=True)

    elif parts[0] == "send":
        lesson, user_name, part = parts[1], parts[2], parts[3]
        if lesson in data and user_name in data[lesson] and part in data[lesson][user_name]:
            msg_to_send = f"{user_name} - {lesson} قسمت {part}:\n{data[lesson][user_name][part]}"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=msg_to_send)
            await query.answer("پیام ارسال شد ✅")

app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_lessons))
app.add_handler(CommandHandler("search", search))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("ربات در حال اجراست...")
app.run_polling()
