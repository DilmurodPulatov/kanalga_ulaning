import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "2039341950:AAFQmnr2mxEWMMLs0G9RPabqc-zBoAgOeEE"
DATA_FILE = "channels.json"


# Fayldan yuklash
def load_channels():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Faylga yozish
def save_channels(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


group_channels = load_channels()


# /kanal → kanal qo‘shish
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not context.args:
        await update.message.reply_text("Iltimos, kanal username kiriting. Masalan:\n/kanal @darslik_kanali")
        return

    channel = context.args[0]
    if chat_id not in group_channels:
        group_channels[chat_id] = []

    if channel not in group_channels[chat_id]:
        group_channels[chat_id].append(channel)
        save_channels(group_channels)
        await update.message.reply_text(f"{channel} majburiy kanal sifatida qo‘shildi ✅")
    else:
        await update.message.reply_text(f"{channel} allaqachon qo‘shilgan.")


# /kanallar → ro‘yxatni ko‘rsatish
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in group_channels or not group_channels[chat_id]:
        await update.message.reply_text("Bu guruh uchun majburiy kanallar belgilanmagan.")
        return

    channels_list = "\n".join(group_channels[chat_id])
    await update.message.reply_text(f"📋 Bu guruh uchun majburiy kanallar:\n{channels_list}")


# /kanaldan_ol → kanalni o‘chirish
async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not context.args:
        await update.message.reply_text(
            "Iltimos, o‘chiriladigan kanal username kiriting. Masalan:\n/kanaldan_ol @darslik_kanali")
        return

    channel = context.args[0]
    if chat_id in group_channels and channel in group_channels[chat_id]:
        group_channels[chat_id].remove(channel)
        save_channels(group_channels)
        await update.message.reply_text(f"{channel} majburiy kanallar ro‘yxatidan o‘chirildi ✅")
    else:
        await update.message.reply_text(f"{channel} bu guruh ro‘yxatida topilmadi ❌")


# Guruhdagi har qanday xabarni tekshirish
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:  # system event (user joined, left...) bo‘lsa
        return

    chat_id = str(update.effective_chat.id)

    # Agar xabarni kanal yuborgan bo‘lsa (post) → tekshirmaymiz
    if update.message.sender_chat and update.message.sender_chat.type == "channel":
        return

    if not update.effective_user:
        return

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if chat_id not in group_channels:
        return

    for channel in group_channels[chat_id]:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                # Har qanday xabarni (text, rasm, stiker, video, fayl...) o‘chiradi
                try:
                    await update.message.delete()
                except:
                    pass

                # Majburiy kanallar ro‘yxati
                channels_list = " ".join(group_channels[chat_id])

                # Chatga ogohlantirish yuborish
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"👤 {user_name}, siz majburiy kanallarga ulanmagansiz!\n"
                         f"Iltimos, quyidagi kanallarga qo‘shiling:\n➡️ {channels_list}"
                )
                return
        except:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Kanalni tekshirishda xatolik: {channel}"
            )
            return


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("kanal", add_channel))
    app.add_handler(CommandHandler("kanallar", list_channels))
    app.add_handler(CommandHandler("kanaldan_ol", remove_channel))
    # Endi faqat text emas, balki barcha xabarlarni tekshiradi
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_membership))

    print("✅ Bot ishlayapti...")
    app.run_polling()


if __name__ == "__main__":
    main()
