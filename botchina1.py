import json
import time
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

TOKEN = "7610776930:AAHUMdRsD66gd1fNEH_6fqxMfNdgDHkSq28"  # Ganti dengan token bot kamu
ADMIN_IDS = [7062724005, 6551372143]  # Ganti dengan dua ID admin Telegram kamu

# Fungsi untuk memuat saldo dari file JSON
def load_saldo():
    try:
        with open("saldo.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Fungsi untuk menyimpan saldo ke file JSON
def save_saldo(saldo):
    with open("saldo.json", "w") as file:
        json.dump(saldo, file, indent=4)

# Fungsi untuk menangani perintah /start (tidak membalas apapun di chat pribadi)
async def start(update: Update, context: CallbackContext):
    if update.message.chat.type == "private":
        return  # Tidak membalas di chat pribadi

# Fungsi utama untuk menangani pesan masuk (hanya di grup)
async def handle_message(update: Update, context: CallbackContext):
    if update.message.chat.type == "private":
        return  # Tidak membalas di chat pribadi

    user_id = str(update.message.from_user.id)
    name = update.message.from_user.full_name
    mention = f"[{name}](tg://user?id={user_id})"  # Membuat nama bisa diklik
    text = update.message.text.strip()
    saldo = load_saldo()

    # Jika pengguna mengetik "1"
    if text == "1":
        if user_id not in saldo:
            saldo[user_id] = {"name": name, "balance": 0.00}  # Saldo awal hanya dibuat, tidak di-reset
            save_saldo(saldo)
        waktu_sekarang = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        await update.message.reply_text(
            f"✅ 工资已报告！\n\n"
            f"👤 {mention}\n"
            f"💰 余额: {saldo[user_id]['balance']:.2f} 元\n"
            f"👨‍💻 运营商: @pyy281229\n"
            f"🕒 时间: {waktu_sekarang}",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    # Jika ADMIN mengetik "2" untuk melihat saldo semua pengguna
    elif text == "2":
        if update.message.from_user.id not in ADMIN_IDS:
            await update.message.reply_text("⚠️ 你不是管理员！")
            return
        if not saldo:
            await update.message.reply_text("🔎 尚未收集任何数据。")  # Pesan baru jika saldo kosong
            return
        total_saldo = sum(data["balance"] for data in saldo.values())
        laporan = f"🔎 所有工资明细:\n\n💰 总余额: {total_saldo:.2f} 元\n\n"
        for user, data in sorted(saldo.items(), key=lambda x: x[1]["balance"], reverse=True):
            laporan += f"👤 [{data['name']}](tg://user?id={user}) - 💰 {data['balance']:.2f} 元\n"
        await update.message.reply_text(laporan, parse_mode="Markdown", disable_web_page_preview=True)

    # Jika ADMIN mengetik "3" untuk reset saldo
    elif text == "3":
        if update.message.from_user.id not in ADMIN_IDS:
            await update.message.reply_text("⚠️ 你不是管理员！")
            return
        saldo.clear()
        save_saldo(saldo)
        await update.message.reply_text("✅ 付款成功，余额已重置！")

    # Jika ADMIN ingin menambah/mengurangi saldo dengan reply pesan "1" dari pengguna
    elif update.message.reply_to_message and update.message.from_user.id in ADMIN_IDS:
        target_id = str(update.message.reply_to_message.from_user.id)
        target_text = update.message.reply_to_message.text.strip()
        target_mention = f"[{update.message.reply_to_message.from_user.full_name}](tg://user?id={target_id})"

        # Pastikan admin hanya bisa menambah/mengurangi saldo jika mereply "1"
        if target_text == "1":
            try:
                jumlah = float(text)
                if target_id in saldo:
                    saldo[target_id]["balance"] += jumlah  # Saldo bertambah sesuai jumlah yang diketik admin
                    save_saldo(saldo)
                    await update.message.reply_text(
                        f"✅ {target_mention} 的余额已更改为 💰 {saldo[target_id]['balance']:.2f} 元",
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                else:
                    await update.message.reply_text("⚠️ 用户尚未报告工资 (未输入 '1')。")
            except ValueError:
                await update.message.reply_text("⚠️ 格式错误！请使用 +10 或 -20 这样的数字格式。")
        else:
            return  # Tidak membalas jika reply selain "1"

# Fungsi untuk menutup grup (perintah `下课`)
async def lock_group(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("⚠️ 你不是管理员！")
        return
    await context.bot.set_chat_permissions(
        chat_id=update.message.chat_id,
        permissions=ChatPermissions(can_send_messages=False)
    )
    await update.message.reply_text("🔒已开启全局禁言.")

# Fungsi untuk membuka grup (perintah `上课`)
async def unlock_group(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("⚠️ 你不是管理员！")
        return
    await context.bot.set_chat_permissions(
        chat_id=update.message.chat_id,
        permissions=ChatPermissions(can_send_messages=True)
    )
    await update.message.reply_text("🔓已解除全局禁言")

# Fungsi utama untuk menjalankan bot
def main():
    app = Application.builder().token(TOKEN).build()

    # Handler untuk perintah /start (tidak membalas di chat pribadi)
    app.add_handler(CommandHandler("start", start))

    # Handler untuk mengunci/membuka grup dengan perintah `上课` dan `下课`
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^下课$"), lock_group))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^上课$"), unlock_group))

    # Handler untuk menangani semua pesan teks lainnya (hanya di grup)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ 机器人正在运行...")
    app.run_polling()

if __name__ == "__main__":
    main()
