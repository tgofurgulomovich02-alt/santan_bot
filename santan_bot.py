from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = '7250606643:AAHFnAzFsT8WYrXb5GrcFVW_bDI147FcD4o'
CLIENT_GROUP_ID = -1002822741446
WORKER_GROUP_ID = -1002496303369

# Dictionary to track orders by message ID
order_data = {}

# When someone sends a message in the client group
async def handle_client_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CLIENT_GROUP_ID:
        return  # Only respond to messages in the client group

    user = update.effective_user
    message = update.message.text

    order_data[update.message.message_id] = {
        "user_id": user.id,
        "username": user.username or user.full_name,
        "message": message,
        "client_chat_id": update.effective_chat.id
    }

    keyboard = [
        [InlineKeyboardButton("✅ Ha", callback_data=f"confirm_{update.message.message_id}")],
        [InlineKeyboardButton("❌ Yo‘q", callback_data="cancel")]
    ]

    await update.message.reply_text(
        f"Buyurtmangiz:\n\n{message}\n\nBuyurtma berishni xohlaysizmi?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# When client clicks "Ha" or "Yo‘q"
async def handle_client_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_"):
        msg_id = int(query.data.split("_")[1])
        order = order_data.get(msg_id)

        if not order:
            await query.edit_message_text("Xatolik: buyurtma topilmadi.")
            return

        # Send to worker group
        keyboard = [
            [InlineKeyboardButton("✅ Ha", callback_data=f"approve_{msg_id}")]
        ]

        await context.bot.send_message(
            chat_id=WORKER_GROUP_ID,
            text=f"🛒 *Yangi buyurtma!*\n\n👤 Mijoz: @{order['username']}\n📝 Buyurtma:\n{order['message']}\n\nBuyurtmani 'jarayonda' deb aytaylikmi?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

        await query.edit_message_text("Buyurtmangiz qabul qilindi. Iltimos kuting...")

    elif query.data == "cancel":
        await query.edit_message_text("Buyurtma bekor qilindi.")

# When workers approve the order
async def handle_worker_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("approve_"):
        msg_id = int(query.data.split("_")[1])
        order = order_data.get(msg_id)

        if not order:
            await query.edit_message_text("Buyurtma topilmadi.")
            return

        await context.bot.send_message(
            chat_id=CLIENT_GROUP_ID,
            text=f"@{order['username']}, buyurtmangiz *jarayonda*! 🛠️\nTez orada siz bilan bog‘lanamiz. 😊",
            parse_mode="Markdown"
        )

        await query.edit_message_text("✅ Buyurtma 'jarayonda' deb belgilandi.")

# Main bot function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_client_message))
    app.add_handler(CallbackQueryHandler(handle_client_reply, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(handle_client_reply, pattern="^cancel$"))
    app.add_handler(CallbackQueryHandler(handle_worker_reply, pattern="^approve_"))

    print("✅ Santan bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
