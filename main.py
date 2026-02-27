import os
import img2pdf
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Bot tokeningizni bu yerga yozing
TOKEN = '8500990975:AAEVY5JdDALq33hWCUh3crAns2Mh8eKlEVs'

# Foydalanuvchi yuborgan rasmlarni saqlash uchun lug'at
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Menga rasmlarni yuboring, men ularni PDF qilib beraman.\n"
        "Rasmlarni yuborib bo'lgach, 'PDF-ga aylantirish' tugmasini bosing."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = []

    # Eng sifatli rasm (oxirgi index) ID sini olish
    photo_file = await update.message.photo[-1].get_file()

    # Rasmni vaqtincha saqlash
    file_path = f"{user_id}_{len(user_data[user_id])}.jpg"
    await photo_file.download_to_drive(file_path)
    user_data[user_id].append(file_path)

    # 4 ta Inline tugma (2x2 grid)
    keyboard = [
        [
            InlineKeyboardButton("📄 PDF-ga aylantirish", callback_data='convert'),
            InlineKeyboardButton("🗑 Tozalash", callback_data='clear')
        ],
        [
            InlineKeyboardButton("📊 Rasm soni", callback_data='count'),
            InlineKeyboardButton("ℹ️ Yordam", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Rasm qabul qilindi! (Jami: {len(user_data[user_id])} ta)",
                                    reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'convert':
        if user_id in user_data and user_data[user_id]:
            await query.edit_message_text("PDF tayyorlanmoqda, kuting...")

            pdf_path = f"{user_id}_result.pdf"
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(user_data[user_id]))

            # PDF ni yuborish
            with open(pdf_path, "rb") as f:
                await context.bot.send_document(chat_id=user_id, document=f, filename="tayyor_fayl.pdf")

            # Tozalash
            cleanup(user_id)
            await query.message.reply_text("PDF tayyor! Rasmlar xotiradan o'chirildi.")
        else:
            await query.message.reply_text("Hech qanday rasm yuborilmagan!")

    elif query.data == 'clear':
        cleanup(user_id)
        await query.edit_message_text("Barcha rasmlar ro'yxatdan o'chirildi.")

    elif query.data == 'count':
        count = len(user_data.get(user_id, []))
        await query.message.reply_text(f"Siz hozircha {count} ta rasm yubordingiz.")

    elif query.data == 'help':
        await query.message.reply_text("Rasmlarni ketma-ket yuboring va 'PDF-ga aylantirish' tugmasini bosing.")


def cleanup(user_id):
    """Vaqtincha fayllarni o'chirish"""
    if user_id in user_data:
        for path in user_data[user_id]:
            if os.path.exists(path):
                os.remove(path)
        del user_data[user_id]

    pdf_path = f"{user_id}_result.pdf"
    if os.path.exists(pdf_path):
        os.remove(pdf_path)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == '__main__':
    main()