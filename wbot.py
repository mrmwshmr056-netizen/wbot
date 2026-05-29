from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import io

TOKEN = "حط التوكن حقك هنا"
ADMIN_ID = 123456789 # <-- حط الـ ID بتاعك هنا

# مراحل المحادثة للرفع
UPLOAD_NAME, UPLOAD_DESC, UPLOAD_FILE = range(3)

# قاعدة بيانات الأكواد
CODES = {
    "navbar": {
        "name": "Navbar احترافي",
        "desc": "شريط علوي متجاوب",
        "code": "<!-- كودك هنا -->"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("🎨 عرض الأكواد", callback_data="cat_ui")],
    ]

    # زر الرفع يظهر للأدمن بس
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⬆️ رفع كود جديد", callback_data="upload")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 مرحباً ببوت الأكواد الاحترافية", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # حماية زر الرفع
    if query.data == "upload":
        if user_id!= ADMIN_ID:
            await query.answer("⛔️ انت ما الأدمن، ما عندك صلاحية", show_alert=True)
            return

        await query.edit_message_text("ارسل اسم الكود الجديد، مثال: `footer`")
        return UPLOAD_NAME

    # باقي الأزرار عادية
    elif query.data.startswith("code_"):
        code_key = query.data.replace("code_", "")
        code_data = CODES[code_key]

        file = io.StringIO(code_data['code'])
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file,
            filename=f"{code_key}.html",
            caption=f"📄 {code_data['name']}"
        )

async def upload_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return ConversationHandler.END

    context.user_data['new_code_name'] = update.message.text.lower()
    await update.message.reply_text("تمام، هسي ارسل وصف الكود، مثال: فوتر متعدد الأعمدة")
    return UPLOAD_DESC

async def upload_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return ConversationHandler.END

    context.user_data['new_code_desc'] = update.message.text
    await update.message.reply_text("أخيراً، ارسل ملف.html بتاع الكود")
    return UPLOAD_FILE

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return ConversationHandler.END

    doc = update.message.document
    if not doc.file_name.endswith('.html'):
        await update.message.reply_text("❌ ارسل ملف.html بس")
        return UPLOAD_FILE

    file = await doc.get_file()
    code_content = (await file.download_as_bytearray()).decode('utf-8')

    name = context.user_data['new_code_name']
    desc = context.user_data['new_code_desc']

    # نضيف الكود لقاعدة البيانات
    CODES[name] = {
        "name": name,
        "desc": desc,
        "code": code_content
    }

    await update.message.reply_text(f"✅ تم رفع الكود `{name}` بنجاح!\nهسي بقى ظاهر لكل الناس", parse_mode="Markdown")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء")
    context.user_data.clear()
    return ConversationHandler.END

app = Application.builder().token(TOKEN).build()

# محادثة الرفع المحمية
upload_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^upload$")],
    states={
        UPLOAD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_name)],
        UPLOAD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_desc)],
        UPLOAD_FILE: [MessageHandler(filters.Document.ALL, upload_file)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(upload_conv)
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()