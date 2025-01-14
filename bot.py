import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes, CallbackQueryHandler
from queue import Queue
import asyncio
import pandas as pd
import os
from app import answer_question_with_bert, find_story_by_title


# Token Telegram Bot
BOT_TOKEN = "7869114977:AAEGYJFuWFBo0mxc77bqO66_hg_gd1hZqoQ"
update_queue = Queue()
user_choices = {}

# Membaca daftar cerita dari file JSON
with open("cerita1.json", "r", encoding="utf-8") as f:
    cerita_data = json.load(f)

# Membaca file CSV
csv_data = pd.read_csv("LogiNER - QAS.csv")

def get_answer_from_csv(story_name, question, csv_data):
    """Cari jawaban tetap berdasarkan cerita dan pertanyaan di CSV."""
    # Filter data berdasarkan cerita
    filtered_data = csv_data[csv_data['Cerita'] == story_name]
    
    # Cari pertanyaan yang cocok
    matched_row = filtered_data[filtered_data['Question'] == question]
    
    # Jika ditemukan, kembalikan jawaban
    if not matched_row.empty:
        return matched_row.iloc[0]['Answer']
    return None

def process_question(user_input, story_title):
    """Proses pertanyaan pengguna berdasarkan cerita yang dipilih."""
    # Cari jawaban di CSV
    answer = get_answer_from_csv(story_title, user_input, csv_data)
    
    if answer:
        return f"Jawaban: {answer}"
    
    # Jika tidak ada di CSV, gunakan IndoBERT QA
    story = find_story_by_title(story_title)
    context = story["teks"]  
    answer_from_indobert = answer_question_with_bert(user_input, context)  # Panggil model IndoBERT QA
    
    if answer_from_indobert:
        return f"Jawaban : {answer_from_indobert}"
    
    # Jika IndoBERT QA juga tidak bisa menjawab
    return "Maaf, saya tidak menemukan jawaban untuk pertanyaan Anda."

# Fungsi untuk memulai interaksi bot dan menampilkan daftar cerita
async def stories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /cerita agar menampilkan daftar cerita kepada pengguna."""
    keyboard = [
        [InlineKeyboardButton(value["judul"], callback_data=key)]
        for key, value in cerita_data.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Silakan pilih cerita yang ingin Anda ajukan pertanyaan.",
        reply_markup=reply_markup
    )


# Fungsi menangani pilihan pengguna dari tombol
async def send_images(chat_id, folder_path, context):
    """Kirim gambar secara bertahap dengan jeda."""
    image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]

    for image_file in image_files[:10]:  # Batasi pengiriman hingga 10 gambar
        image_path = os.path.join(folder_path, image_file)
        with open(image_path, 'rb') as image:
            try:
                await context.bot.send_photo(chat_id=chat_id, photo=image)
                await asyncio.sleep(1)  # Beri jeda 1 detik antar pengiriman
            except Exception as e:
                print(f"Error saat mengirim gambar: {e}")

async def choose_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk menangani pilihan cerita."""
    query = update.callback_query

    # Jawab callback query dengan cepat
    await query.answer()

    user_id = query.from_user.id
    story_id = query.data

    if story_id in cerita_data.keys():
        user_choices[user_id] = cerita_data[story_id]['judul']  # Simpan pilihan pengguna

        # Kirim respons awal
        await query.edit_message_text(
            text=f"✅ Anda telah memilih cerita: {cerita_data[story_id]['judul']}.\n\nTunggu sebentar, kami sedang memuat gambar..."
        )

        # Path gambar dari folder static
        if 'gambar_folder' in cerita_data[story_id]:
            folder_path = os.path.join('static', 'images', cerita_data[story_id]['gambar_folder'])
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Kirim gambar dengan jeda
                asyncio.create_task(send_images(query.message.chat_id, folder_path, context))

                # Beri tahu pengguna bahwa gambar sedang dikirim
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="Gambar sedang dikirim. Silakan tunggu..."
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"Folder gambar tidak ditemukan untuk cerita: {cerita_data[story_id]['judul']}."
                )
    else:
        await query.answer(text="Cerita yang Anda pilih tidak valid. Silakan coba lagi.")


# Fungsi untuk menangani pesan pertanyaan dari pengguna
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk memproses input dari pengguna dan memanggil fungsi pemrosesan."""
    user_id = update.message.from_user.id
    if user_id not in user_choices:
        await update.message.reply_text(
            "🔔 Anda belum memilih cerita. Gunakan /cerita untuk memilih terlebih dahulu."
        )
    else:
        user_input = update.message.text
        story_title = user_choices[user_id]
        response = process_question(user_input, story_title)  # Kirim judul cerita
        await update.message.reply_text(response)


# Fungsi utama untuk menjalankan bot
def main():
    """Membuat dan menjalankan bot Telegram."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Tambahkan handler
    application.add_handler(CommandHandler("cerita", stories))
    application.add_handler(CallbackQueryHandler(choose_story))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    # Jalankan bot
    application.run_polling()


if __name__ == "__main__":
    main()

